import rasterio

class RasterService:
    @staticmethod
    def read_metadata(file_path: str) -> dict:
        try:
            with rasterio.open(file_path) as src:
                return {
                    "driver": src.driver,
                    "dtype": src.dtypes[0],
                    "nodata": src.nodata,
                    "width": src.width,
                    "height": src.height,
                    "count": src.count,
                    "crs": src.crs.to_string() if src.crs else None,
                    "bounds": list(src.bounds)
                }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_reprojected_bounds(file_path: str) -> dict:
        from rasterio.warp import transform_bounds
        try:
            with rasterio.open(file_path) as src:
                if not src.crs:
                    return {"error": "GeoTIFF has no CRS"}
                # Transform to WGS84 (Lat/Lon)
                left, bottom, right, top = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
                return {
                    "bounds": [[bottom, left], [top, right]] # Leaflet format: [[south, west], [north, east]]
                }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def generate_thumbnail(file_path: str, size: int = None) -> bytes:
        from rasterio.enums import Resampling
        from PIL import Image
        import io
        import numpy as np
        try:
            with rasterio.open(file_path) as src:
                if size is None:
                    out_shape = (src.count, src.height, src.width)
                else:
                    out_shape = (src.count, size, size)
                    
                # Decimated or full read
                data = src.read(
                    out_shape=out_shape,
                    resampling=Resampling.bilinear
                )
                
                # Take first 3 bands for RGB (or duplicate 1 band if grayscale)
                if src.count >= 3:
                    rgb = data[:3, :, :]
                else:
                    rgb = np.repeat(data[0:1, :, :], 3, axis=0)
                    
                # Normalize to 0-255 uint8 using 2nd and 98th percentile for satellite imagery
                rgb = rgb.astype(np.float32)
                p2, p98 = np.percentile(rgb, (2, 98))
                if p98 > p2:
                    rgb = np.clip((rgb - p2) / (p98 - p2), 0, 1)
                else:
                    rgb = np.zeros_like(rgb)
                rgb = (rgb * 255.0).astype(np.uint8)
                    
                # Transpose from (C, H, W) to (H, W, C) for Pillow
                rgb_hwc = np.transpose(rgb, (1, 2, 0))
                
                img = Image.fromarray(rgb_hwc)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=85)
                return buf.getvalue()
        except Exception as e:
            raise Exception(f"Thumbnail generation failed: {str(e)}")

    @staticmethod
    def detect_sentinel2_bands(file_path: str) -> dict:
        """
        Auto-detect Sentinel-2 band indices (1-based) from rasterio band descriptions.

        Detection priority:
        1. Exact description match (e.g. "B04", "B08", "B03", "B11")
        2. Substring match in description
        3. Positional fallback for standard RGB-NIR or RGBN stacks

        Returns a dict with keys: red, nir, green, swir (all optional).
        Also returns 'warning' key if fallback was used.
        """
        import re
        result = {}
        warning = None

        # Known band description → canonical name mappings
        BAND_KEYWORDS = {
            "red":   ["B04", "B4", "red", "RED", "665", "664"],
            "nir":   ["B08", "B8", "B8A", "nir", "NIR", "842", "833", "865"],
            "green": ["B03", "B3", "green", "GREEN", "560", "559"],
            "swir":  ["B11", "B12", "swir", "SWIR", "1610", "2190"],
        }

        try:
            with rasterio.open(file_path) as src:
                count = src.count
                descriptions = [d or "" for d in (src.descriptions or [])]

                def find_band(keywords):
                    for kw in keywords:
                        for i, desc in enumerate(descriptions, start=1):
                            if kw.upper() in desc.upper():
                                return i
                    return None

                # Try description-based detection
                for band_name, keywords in BAND_KEYWORDS.items():
                    idx = find_band(keywords)
                    if idx is not None:
                        result[band_name] = idx

                # If we found at least red and NIR, we're good — no warning
                if "red" in result and "nir" in result:
                    return {**result, "warning": None}

                # Positional fallback
                warning = (
                    "Band descriptions not found or insufficient for auto-detection. "
                    "Falling back to positional assumptions: "
                )
                if count >= 4:
                    # Standard Sentinel-2 export: Blue(1), Green(2), Red(3), NIR(4)
                    result = {"blue": 1, "green": 2, "red": 3, "nir": 4}
                    warning += "Bands 1=Blue, 2=Green, 3=Red, 4=NIR (4-band RGBN stack assumed)."
                elif count == 3:
                    result = {"blue": 1, "green": 2, "red": 3}
                    warning += "Only 3 bands found (RGB). NIR unavailable — NDVI cannot be computed."
                else:
                    result = {}
                    warning += f"Only {count} band(s) found. Cannot determine spectral indices."

                return {**result, "warning": warning}
        except Exception as e:
            return {"warning": f"Band detection failed: {str(e)}"}

    @staticmethod
    def generate_colormap_overlay(
        array: "np.ndarray",
        cmap_name: str = "RdYlGn",
        vmin: float = -1.0,
        vmax: float = 1.0,
        alpha: float = 0.85,
    ) -> bytes:
        """
        Convert a 2D numpy array into a RGBA PNG image bytes using a matplotlib colormap.
        Suitable for use as a Leaflet ImageOverlay.
        """
        import numpy as np
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        import io
        from PIL import Image

        # Normalize to [0, 1]
        normed = np.clip((array - vmin) / (vmax - vmin + 1e-10), 0, 1)

        cmap = cm.get_cmap(cmap_name)
        rgba = cmap(normed)  # (H, W, 4) float64

        # Apply alpha channel (mask NaN to transparent)
        rgba[..., 3] = np.where(np.isnan(array), 0.0, alpha)

        img_array = (rgba * 255).astype(np.uint8)
        img = Image.fromarray(img_array, mode="RGBA")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


raster_service = RasterService()
