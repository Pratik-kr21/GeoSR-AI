import rasterio
from rasterio.windows import Window
import os

input_file = "data/test_input.tif"
output_file = "data/small_test.tif"

print(f"Reading {input_file}...")
with rasterio.open(input_file) as src:
    # We want a small 512x512 window
    window = Window(0, 0, 512, 512)
    
    # Update metadata for the new small size
    meta = src.meta.copy()
    meta.update({
        "height": window.height,
        "width": window.width,
        "transform": rasterio.windows.transform(window, src.transform)
    })
    
    print(f"Extracting 512x512 patch to {output_file}...")
    with rasterio.open(output_file, 'w', **meta) as dst:
        dst.write(src.read(window=window))

print(f"Successfully created {output_file}!")
print(f"File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
