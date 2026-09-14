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
    def generate_thumbnail(file_path: str, size: int = 512) -> bytes:
        from rasterio.enums import Resampling
        from PIL import Image
        import io
        import numpy as np
        try:
            with rasterio.open(file_path) as src:
                # Decimated read to avoid OOM
                data = src.read(
                    out_shape=(src.count, size, size),
                    resampling=Resampling.bilinear
                )
                
                # Take first 3 bands for RGB (or duplicate 1 band if grayscale)
                if src.count >= 3:
                    rgb = data[:3, :, :]
                else:
                    rgb = np.repeat(data[0:1, :, :], 3, axis=0)
                    
                # Normalize to 0-255 uint8
                if rgb.dtype != np.uint8:
                    rgb = rgb.astype(np.float32)
                    rgb = (rgb / rgb.max() * 255.0).astype(np.uint8)
                    
                # Transpose from (C, H, W) to (H, W, C) for Pillow
                rgb_hwc = np.transpose(rgb, (1, 2, 0))
                
                img = Image.fromarray(rgb_hwc)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=85)
                return buf.getvalue()
        except Exception as e:
            raise Exception(f"Thumbnail generation failed: {str(e)}")

raster_service = RasterService()
