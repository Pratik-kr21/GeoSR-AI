"""
realtime_service.py
===================
Provides live satellite data fetching from:
  1. Copernicus Data Space Ecosystem (CDSE) — Sentinel-2 L2A GeoTIFFs
  2. Open-Meteo — free weather API (no credentials required)

Design decisions:
  - CDSE auth uses the OAuth2 token endpoint directly (requests library),
    then queries the CDSE OData/STAC catalog to find the best scene,
    then downloads via the CDSE S3-compatible download endpoint.
  - If CDSE_CLIENT_ID / CDSE_CLIENT_SECRET are missing, fetch functions
    raise a clear RuntimeError so the API layer can return a 503 with a
    helpful message rather than a silent failure.
  - All file I/O uses /tmp so nothing bleeds into the repo or MinIO
    until the caller explicitly uploads.
"""

import os
import math
import uuid
import asyncio
import tempfile
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any, List

import requests
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# ─── CDSE constants ────────────────────────────────────────────────────────────
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
CDSE_DOWNLOAD_URL = "https://zipper.dataspace.copernicus.eu/api/v1/dataspace/custom-script/band-combination"
CDSE_S3_ENDPOINT = "https://eodata.dataspace.copernicus.eu"

# Sentinel-2 L2A collection name on CDSE OData
S2_COLLECTION = "SENTINEL-2"
S2_PRODUCT_TYPE = "S2MSI2A"  # Level-2A atmospherically corrected

# Temp directory for downloaded tiles
TEMP_DIR = "/tmp/geosrai_realtime"
os.makedirs(TEMP_DIR, exist_ok=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_wkt_bbox(lat: Optional[float], lon: Optional[float], buffer_km: Optional[float], bbox: Optional[List[float]] = None) -> str:
    """
    Build a WKT POLYGON string representing a square bounding box
    around (lat, lon) with the given buffer radius in kilometres,
    or from a direct bounding box [west, south, east, north].
    Uses approximate degree conversion (1 deg lat ≈ 111 km).
    """
    if bbox is not None:
        west, south, east, north = bbox
    else:
        delta_lat = buffer_km / 111.0
        delta_lon = buffer_km / (111.0 * math.cos(math.radians(lat)))

        west  = lon - delta_lon
        east  = lon + delta_lon
        south = lat - delta_lat
        north = lat + delta_lat

    # Clamp to valid WGS-84 bounds
    west  = max(-180.0, west)
    east  = min(180.0, east)
    south = max(-90.0, south)
    north = min(90.0, north)

    return (
        f"POLYGON(({west} {south}, {east} {south}, "
        f"{east} {north}, {west} {north}, {west} {south}))"
    )


def _get_cdse_token() -> str:
    """
    Obtain a short-lived OAuth2 access token from the CDSE identity provider.
    Raises RuntimeError if credentials are missing or authentication fails.
    """
    if not settings.CDSE_ENABLED:
        raise RuntimeError(
            "CDSE credentials are not configured. "
            "Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET in your .env file. "
            "Register for free at https://dataspace.copernicus.eu/"
        )

    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.CDSE_CLIENT_ID,
        "client_secret": settings.CDSE_CLIENT_SECRET,
    }
    try:
        resp = requests.post(CDSE_TOKEN_URL, data=payload, timeout=15)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise RuntimeError("CDSE returned an empty access token.")
        return token
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "?"
        body = e.response.text[:300] if e.response else ""
        raise RuntimeError(
            f"CDSE authentication failed (HTTP {status}). "
            f"Check your Client ID / Secret. Details: {body}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Could not reach CDSE auth server: {e}") from e


def _search_cdse_catalog(
    wkt_polygon: str,
    days_back: int,
    max_cloud_cover: int,
) -> Optional[Dict[str, Any]]:
    """
    Query the CDSE OData catalog for the most recent Sentinel-2 L2A product
    matching the given spatial footprint, date range, and cloud cover filter.

    Returns the best product dict, or None if nothing is found.
    """
    start_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
        "%Y-%m-%dT00:00:00.000Z"
    )
    end_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT23:59:59.999Z")

    filter_str = (
        f"Collection/Name eq '{S2_COLLECTION}' "
        f"and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' "
        f"and att/OData.CSC.StringAttribute/Value eq '{S2_PRODUCT_TYPE}') "
        f"and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' "
        f"and att/OData.CSC.DoubleAttribute/Value le {max_cloud_cover}.00) "
        f"and ContentDate/Start gt {start_date} "
        f"and ContentDate/Start lt {end_date} "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;{wkt_polygon}')"
    )

    params = {
        "$filter": filter_str,
        "$orderby": "ContentDate/Start desc",
        "$top": 1,
        "$expand": "Attributes",
    }

    try:
        resp = requests.get(CDSE_CATALOG_URL, params=params, timeout=20)
        resp.raise_for_status()
        results = resp.json().get("value", [])
        return results[0] if results else None
    except Exception as e:
        logger.warning(f"CDSE catalog search failed: {e}")
        return None


def _extract_product_metadata(product: Dict[str, Any]) -> Dict[str, Any]:
    """Parse useful fields from a CDSE OData product record."""
    attrs = {a["Name"]: a.get("Value") for a in product.get("Attributes", [])}
    cloud = attrs.get("cloudCover", 0.0)
    date_str = product.get("ContentDate", {}).get("Start", "")

    acquisition_date = None
    if date_str:
        try:
            acquisition_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass

    return {
        "product_id": product.get("Id"),
        "name": product.get("Name"),
        "cloud_cover": float(cloud) if cloud is not None else 0.0,
        "acquisition_date": acquisition_date,
        "size_mb": round(product.get("ContentLength", 0) / 1e6, 1),
    }


def _fetch_sentinelhub_crop(lat: Optional[float], lon: Optional[float], buffer_km: Optional[float], date: str, token: str, output_dir: str, bbox: Optional[List[float]] = None) -> str:
    """
    Use Sentinel Hub Process API to fetch a fast cropped GeoTIFF for the exact area.
    """
    logger.info("Fetching cropped GeoTIFF from Sentinel Hub Process API...")
    url = "https://sh.dataspace.copernicus.eu/api/v1/process"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    if bbox is None:
        lat_diff = buffer_km / 111.0
        lon_diff = buffer_km / (111.0 * math.cos(math.radians(lat)))
        bbox = [lon - lon_diff, lat - lat_diff, lon + lon_diff, lat + lat_diff]

    # Extract just YYYY-MM-DD from the datetime string or object
    date_str = str(date)
    date_only = date_str.split(" ")[0].split("T")[0]
    from_time = f"{date_only}T00:00:00Z"
    to_time = f"{date_only}T23:59:59Z"

    # Evalscript to return True Color Image (TCI) + Near Infrared (NIR)
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: ["B02", "B03", "B04", "B08"],
            output: { bands: 4, sampleType: "AUTO" }
        };
    }
    function evaluatePixel(sample) {
        // Red, Green, Blue, NIR
        return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02, 2.5 * sample.B08];
    }
    """

    payload = {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {"from": from_time, "to": to_time},
                    "maxCloudCoverage": 100
                }
            }]
        },
        "output": {
            "width": 512,
            "height": 512,
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
        },
        "evalscript": evalscript
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    
    if resp.status_code != 200:
        logger.error(f"Sentinel Hub Process API error: {resp.text}")
        resp.raise_for_status()

    final_path = os.path.join(output_dir, f"{uuid.uuid4()}_sentinel2.tif")
    with open(final_path, "wb") as f:
        f.write(resp.content)
        
    logger.info(f"GeoTIFF saved to {final_path}")
    return final_path


# ─── Public Service Class ──────────────────────────────────────────────────────

class RealtimeService:
    """
    Service layer for real-time satellite data acquisition.

    Use `fetch_sentinel2_geotiff()` to download a Sentinel-2 scene.
    Use `fetch_weather_data()` to get current + 7-day precipitation from Open-Meteo.
    Use `get_latest_available_scene()` to run both and return combined metadata.
    """

    # ── Sentinel-2 / CDSE ─────────────────────────────────────────────────────

    def fetch_sentinel2_geotiff(
        self,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        buffer_km: Optional[float] = 5.0,
        bbox: Optional[List[float]] = None,
        days_back: int = 30,
        max_cloud_cover: int = 20,
    ) -> Tuple[str, Optional[datetime], float, List[float]]:
        """
        Download the most recent cloud-free Sentinel-2 L2A GeoTIFF covering
        the given coordinates from the Copernicus Data Space Ecosystem.

        Args:
            lat: Latitude in decimal degrees (-90 to 90).
            lon: Longitude in decimal degrees (-180 to 180).
            buffer_km: Half-width of the search bounding box in kilometres.
            days_back: How many days into the past to search for scenes.
            max_cloud_cover: Maximum acceptable cloud cover percentage (0-100).

        Returns:
            Tuple of:
                - local_file_path: Absolute path to the downloaded GeoTIFF in /tmp
                - acquisition_date: UTC datetime of the satellite overpass
                - cloud_cover: Cloud cover percentage of the selected scene
                - bounds: [west, south, east, north] in WGS-84

        Raises:
            ValueError: If coordinates are out of valid range.
            RuntimeError: If CDSE credentials are missing, auth fails,
                          no scene is found, or download fails.
        """
        # Validate coordinates if using point
        if bbox is None:
            if lat is None or lon is None:
                raise ValueError("Must provide either a bounding box (bbox) or lat/lon center point.")
            if not (-90 <= lat <= 90):
                raise ValueError(f"Latitude {lat} is out of range (-90 to 90).")
            if not (-180 <= lon <= 180):
                raise ValueError(f"Longitude {lon} is out of range (-180 to 180).")
            center_lat, center_lon = lat, lon
        else:
            center_lon = (bbox[0] + bbox[2]) / 2
            center_lat = (bbox[1] + bbox[3]) / 2

        wkt = _build_wkt_bbox(lat, lon, buffer_km, bbox)
        logger.info(f"Searching CDSE for Sentinel-2 scenes over "
                    f"{'bbox=' + str(bbox) if bbox else f'({lat}, {lon})'}, "
                    f"days_back={days_back}, cloud<{max_cloud_cover}%")

        # 1. Search catalog (no auth needed for catalog)
        product = _search_cdse_catalog(wkt, days_back, max_cloud_cover)
        if product is None:
            raise RuntimeError(
                f"No Sentinel-2 scene found for ({lat}, {lon}) within the last {days_back} days "
                f"with cloud cover < {max_cloud_cover}%. "
                f"Try increasing days_back or max_cloud_cover."
            )

        meta = _extract_product_metadata(product)
        logger.info(f"Found scene: {meta['name']} | cloud={meta['cloud_cover']}% | "
                    f"date={meta['acquisition_date']} | size={meta['size_mb']}MB")

        # 2. Authenticate and download using Sentinel Hub Process API
        token = _get_cdse_token()
        local_path = _fetch_sentinelhub_crop(lat, lon, buffer_km, meta["acquisition_date"], token, TEMP_DIR, bbox)

        # 3. Extract actual bounds from the downloaded TIF
        bounds = self._read_tif_bounds(local_path, center_lat, center_lon, buffer_km if bbox is None else 0, bbox)

        return local_path, meta["acquisition_date"], meta["cloud_cover"], bounds

    @staticmethod
    def _read_tif_bounds(
        tif_path: str, fallback_lat: float, fallback_lon: float, buffer_km: float, fallback_bbox: Optional[List[float]] = None
    ) -> List[float]:
        """Extract [west, south, east, north] bounds from a GeoTIFF using rasterio."""
        try:
            import rasterio
            from rasterio.warp import transform_bounds

            with rasterio.open(tif_path) as ds:
                src_crs = ds.crs
                left, bottom, right, top = ds.bounds
                if src_crs and str(src_crs) != "EPSG:4326":
                    left, bottom, right, top = transform_bounds(
                        src_crs, "EPSG:4326", left, bottom, right, top
                    )
                return [
                    round(left, 6), round(bottom, 6),
                    round(right, 6), round(top, 6)
                ]
        except Exception as e:
            logger.warning(f"Could not read TIF bounds ({e}), using approximate bbox.")
            if fallback_bbox:
                return [round(b, 6) for b in fallback_bbox]
            delta_lat = buffer_km / 111.0
            delta_lon = buffer_km / (111.0 * math.cos(math.radians(fallback_lat)))
            return [
                round(fallback_lon - delta_lon, 6),
                round(fallback_lat - delta_lat, 6),
                round(fallback_lon + delta_lon, 6),
                round(fallback_lat + delta_lat, 6),
            ]

    # ── Sentinel-1 / CDSE ─────────────────────────────────────────────────────

    def fetch_sentinel1_geotiff(
        self,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        buffer_km: Optional[float] = 5.0,
        bbox: Optional[List[float]] = None,
        days_back: int = 30,
        polarizations: List[str] = ["VV", "VH"],
        orbit_direction: Optional[str] = None,
    ) -> Tuple[str, Optional[datetime], float, List[float], Dict[str, Any]]:
        """
        Download Sentinel-1 IW GRD GeoTIFF (VV and VH backscatter in linear power).
        """
        if bbox is None:
            if lat is None or lon is None:
                raise ValueError("Must provide either a bounding box (bbox) or lat/lon center point.")
            center_lat, center_lon = lat, lon
        else:
            center_lon = (bbox[0] + bbox[2]) / 2
            center_lat = (bbox[1] + bbox[3]) / 2

        token = _get_cdse_token()
        
        # Determine bbox
        if bbox is None:
            lat_diff = buffer_km / 111.0
            lon_diff = buffer_km / (111.0 * math.cos(math.radians(center_lat)))
            bbox = [center_lon - lon_diff, center_lat - lat_diff, center_lon + lon_diff, center_lat + lat_diff]

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        from_time = start_date.strftime("%Y-%m-%dT00:00:00Z")
        to_time = end_date.strftime("%Y-%m-%dT23:59:59Z")

        # Linear power evalscript for VV and VH
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: ["VV", "VH", "dataMask"],
                output: { bands: 3, sampleType: "FLOAT32" }
            };
        }
        function evaluatePixel(sample) {
            // Return linear power. dB can be calculated later as 10 * log10(val)
            return [sample.VV, sample.VH, sample.dataMask];
        }
        """
        
        data_filter = {
            "timeRange": {"from": from_time, "to": to_time},
            "acquisitionMode": "IW",
            "polarization": "DV", # Dual polarization (VV + VH)
            "resolution": "HIGH"
        }
        if orbit_direction:
            data_filter["orbitDirection"] = orbit_direction

        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [{
                    "type": "sentinel-1-grd",
                    "dataFilter": data_filter,
                    "processing": {
                        "backCoeff": "SIGMA0_ELLIPSOID",
                        "orthorectify": True
                    }
                }]
            },
            "output": {
                "width": 512,
                "height": 512,
                "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
            },
            "evalscript": evalscript
        }

        url = "https://sh.dataspace.copernicus.eu/api/v1/process"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Fetching Sentinel-1 SAR imagery... days_back={days_back}")
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if resp.status_code != 200:
            if "No data" in resp.text:
                raise RuntimeError(f"No Sentinel-1 scene found. Try increasing days_back.")
            raise RuntimeError(f"Sentinel Hub S1 Process API error: {resp.text}")

        final_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_sentinel1.tif")
        with open(final_path, "wb") as f:
            f.write(resp.content)
            
        bounds = self._read_tif_bounds(final_path, center_lat, center_lon, buffer_km if bbox is None else 0, bbox)
        
        # We don't get the exact acquisition date from Process API easily, we can use headers or fallback
        # SH Process API returns 'SH-Date' header sometimes, but let's just use end_date as proxy if missing
        acquired_date = end_date
        date_header = resp.headers.get("x-sh-date")
        if date_header:
            try:
                acquired_date = datetime.strptime(date_header, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
                
        metadata = {
            "polarizations": polarizations,
            "unit": "linear_power",
            "orbit_direction": orbit_direction or "UNKNOWN"
        }

        return final_path, acquired_date, 0.0, bounds, metadata

    # ── Copernicus DEM ────────────────────────────────────────────────────────

    def fetch_copernicus_dem(
        self,
        lat: float,
        lon: float,
        buffer_km: float = 5.0,
        bbox: Optional[List[float]] = None
    ) -> Tuple[str, List[float]]:
        """
        Download Copernicus DEM (30m) for the given bounds.
        """
        token = _get_cdse_token()
        
        if bbox is None:
            lat_diff = buffer_km / 111.0
            lon_diff = buffer_km / (111.0 * math.cos(math.radians(lat)))
            bbox = [lon - lon_diff, lat - lat_diff, lon + lon_diff, lat + lat_diff]

        # DEM Evalscript for FLOAT32 elevation
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: ["DEM", "dataMask"],
                output: { bands: 2, sampleType: "FLOAT32" }
            };
        }
        function evaluatePixel(sample) {
            return [sample.DEM, sample.dataMask];
        }
        """

        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [{
                    "type": "dem",
                    "dataFilter": {
                        "demInstance": "COPERNICUS_90"
                    }
                }]
            },
            "output": {
                "width": 512,
                "height": 512,
                "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
            },
            "evalscript": evalscript
        }

        url = "https://sh.dataspace.copernicus.eu/api/v1/process"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Fetching Copernicus DEM 30m imagery...")
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if resp.status_code != 200:
            raise RuntimeError(f"Sentinel Hub DEM Process API error: {resp.text}")

        final_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_dem.tif")
        with open(final_path, "wb") as f:
            f.write(resp.content)
            
        bounds = self._read_tif_bounds(final_path, lat, lon, buffer_km if bbox is None else 0, bbox)
        
        return final_path, bounds

    # ── Open-Meteo weather ────────────────────────────────────────────────────

    async def fetch_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetch current and recent precipitation data from Open-Meteo.
        No API key required. Always succeeds (returns a safe fallback on error).

        Returns:
            {
                "available": bool,
                "current_precip_mm": float | None,
                "total_7d_rain_mm": float | None,
                "daily_breakdown": [{"date": str, "precip_mm": float}, ...],
                "raw": dict  # full Open-Meteo response
            }
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "precipitation",
            "daily": "precipitation_sum",
            "past_days": 7,
            "timezone": "auto",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(settings.OPEN_METEO_BASE_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            current_precip = None
            current_block = data.get("current", {})
            if isinstance(current_block, dict):
                current_precip = current_block.get("precipitation")

            daily = data.get("daily", {})
            dates = daily.get("time", [])
            precips = daily.get("precipitation_sum", [])

            daily_breakdown = [
                {"date": d, "precip_mm": round(p, 2) if p is not None else 0.0}
                for d, p in zip(dates, precips)
            ]
            total_7d = sum(
                (p or 0.0) for p in precips
            )

            return {
                "available": True,
                "current_precip_mm": round(current_precip, 2) if current_precip is not None else None,
                "total_7d_rain_mm": round(total_7d, 2),
                "daily_breakdown": daily_breakdown,
                "raw": data,
            }
        except Exception as e:
            logger.warning(f"Open-Meteo request failed: {e}. GeoRisk will use neutral weather score.")
            return {
                "available": False,
                "error": str(e),
                "current_precip_mm": None,
                "total_7d_rain_mm": None,
                "daily_breakdown": [],
                "raw": {},
            }

    # ── Orchestrator ──────────────────────────────────────────────────────────

    async def get_latest_available_scene(
        self,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        buffer_km: Optional[float] = 5.0,
        bbox: Optional[List[float]] = None,
        days_back: int = 30,
        max_cloud_cover: int = 20,
    ) -> Dict[str, Any]:
        """
        High-level orchestrator: search for a Sentinel-2 scene and fetch
        concurrent weather data. Returns a combined metadata dictionary.

        Does NOT download the full GeoTIFF — only checks catalog availability.
        Use fetch_sentinel2_geotiff() when you actually want the file.
        """
        wkt = _build_wkt_bbox(lat, lon, buffer_km, bbox)

        # Run catalog search and weather fetch concurrently
        center_lat = lat if lat is not None else ((bbox[1] + bbox[3]) / 2 if bbox else 0)
        center_lon = lon if lon is not None else ((bbox[0] + bbox[2]) / 2 if bbox else 0)

        loop = asyncio.get_event_loop()
        product_future = loop.run_in_executor(
            None, _search_cdse_catalog, wkt, days_back, max_cloud_cover
        )
        weather_future = self.fetch_weather_data(center_lat, center_lon)

        product, weather = await asyncio.gather(product_future, weather_future)

        if product is None:
            return {
                "found": False,
                "error": (
                    f"No Sentinel-2 scene found for ({lat}, {lon}) "
                    f"within the last {days_back} days with cloud cover < {max_cloud_cover}%. "
                    f"Tip: Try increasing days_back (e.g. 60) or max_cloud_cover (e.g. 35)."
                ),
                "weather": weather,
            }

        meta = _extract_product_metadata(product)
        if bbox is not None:
            approximate_bounds = bbox
        else:
            delta_lat = buffer_km / 111.0
            delta_lon = buffer_km / (111.0 * math.cos(math.radians(center_lat)))
            approximate_bounds = [
                round(center_lon - delta_lon, 4),
                round(center_lat - delta_lat, 4),
                round(center_lon + delta_lon, 4),
                round(center_lat + delta_lat, 4),
            ]

        return {
            "found": True,
            "product_id": meta["product_id"],
            "product_name": meta["name"],
            "acquisition_date": meta["acquisition_date"].isoformat() if meta["acquisition_date"] else None,
            "cloud_cover": meta["cloud_cover"],
            "size_mb": meta["size_mb"],
            "approximate_bounds": approximate_bounds,
            "weather": weather,
            "cdse_enabled": settings.CDSE_ENABLED,
        }


# Module-level singleton
realtime_service = RealtimeService()
