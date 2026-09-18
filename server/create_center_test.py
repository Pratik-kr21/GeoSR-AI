import rasterio
from rasterio.windows import Window
import os

input_file = "data/test_input.tif"
output_file = "data/center_test.tif"

print(f"Reading {input_file}...")
with rasterio.open(input_file) as src:
    # We want a small 1024x1024 window from the DEAD CENTER
    # The image is 10980x10980
    cx = src.width // 2 - 512
    cy = src.height // 2 - 512
    window = Window(cx, cy, 1024, 1024)
    
    # Update metadata for the new small size
    meta = src.meta.copy()
    meta.update({
        "height": window.height,
        "width": window.width,
        "transform": rasterio.windows.transform(window, src.transform)
    })
    
    print(f"Extracting 1024x1024 center patch to {output_file}...")
    with rasterio.open(output_file, 'w', **meta) as dst:
        dst.write(src.read(window=window))

print(f"Successfully created {output_file}!")
print(f"File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
