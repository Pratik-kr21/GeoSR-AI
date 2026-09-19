import rasterio
from rasterio.windows import Window
import os

input_file = "data/test_input.tif"
output_file = "data/different_area_test.tif"

print(f"Reading {input_file}...")
with rasterio.open(input_file) as src:
    # Let's crop a 1024x1024 window from a different area (e.g., bottom right corner)
    # The image is 10980x10980, so we'll offset by a lot
    cx = src.width - 2000
    cy = src.height - 2000
    window = Window(cx, cy, 1024, 1024)
    
    # Update metadata for the new small size
    meta = src.meta.copy()
    meta.update({
        "height": window.height,
        "width": window.width,
        "transform": rasterio.windows.transform(window, src.transform)
    })
    
    print(f"Extracting 1024x1024 offset patch to {output_file}...")
    with rasterio.open(output_file, 'w', **meta) as dst:
        dst.write(src.read(window=window))

print(f"Successfully created {output_file}!")
print(f"File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
