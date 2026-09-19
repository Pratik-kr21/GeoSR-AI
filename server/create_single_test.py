import rasterio
from rasterio.windows import Window
import os

# Path to a single Sentinel-2 band (B02 - Blue, 10m resolution)
SAFE_DIR = "data/S2B_MSIL2A_20260418T052639_N0512_R105_T43RFQ_20260418T091045.SAFE"
BAND_FILE = os.path.join(
    SAFE_DIR,
    "GRANULE/L2A_T43RFQ_A047607_20260418T053640/IMG_DATA/R10m",
    "T43RFQ_20260418T052639_B02_10m.jp2"
)

output_file = "data/single_band_test.tif"
PATCH_SIZE = 1024  # pixels (1024x1024 @ 10m = ~10km x 10km)

print(f"Reading single band: {BAND_FILE}")
with rasterio.open(BAND_FILE) as src:
    print(f"  Source size : {src.width} x {src.height} pixels")
    print(f"  CRS         : {src.crs}")
    print(f"  Resolution  : {src.res} meters")
    print(f"  Dtype       : {src.dtypes[0]}")

    # Extract a patch from the center of the single band image
    cx = src.width  // 2 - PATCH_SIZE // 2
    cy = src.height // 2 - PATCH_SIZE // 2
    window = Window(cx, cy, PATCH_SIZE, PATCH_SIZE)

    meta = src.meta.copy()
    meta.update({
        "driver": "GTiff",
        "height": PATCH_SIZE,
        "width": PATCH_SIZE,
        "count": 1,
        "transform": rasterio.windows.transform(window, src.transform),
        "compress": "lzw",   # lightweight compression
    })

    print(f"\nExtracting {PATCH_SIZE}x{PATCH_SIZE} center patch -> {output_file}")
    with rasterio.open(output_file, "w", **meta) as dst:
        dst.write(src.read(1, window=window), 1)

size_mb = os.path.getsize(output_file) / (1024 * 1024)
print(f"\n[OK] Done!")
print(f"   Output : {output_file}")
print(f"   Size   : {size_mb:.2f} MB")
print(f"   Bands  : 1  (Sentinel-2 B02 - Blue, 10m)")
print(f"   Pixels : {PATCH_SIZE} x {PATCH_SIZE}")
