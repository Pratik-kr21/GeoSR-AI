import os
import rasterio
import numpy as np
from rasterio.transform import from_origin

def create_multiband_test_tif():
    os.makedirs('data', exist_ok=True)
    out_path = 'data/test_small_multiband.tif'
    
    # 4 bands: B(1), G(2), R(3), NIR(4)
    # Typical for Sentinel-2 10m data
    width = 128
    height = 128
    count = 4
    
    # Generate some synthetic data for each band
    # Sentinel-2 data is often uint16 (0 to 10000 range)
    bands_data = []
    
    # Band 1 (Blue) - Base pattern
    x = np.linspace(-5, 5, width)
    y = np.linspace(-5, 5, height)
    X, Y = np.meshgrid(x, y)
    b1 = np.sin(X**2 + Y**2)
    b1 = ((b1 + 1) / 2 * 4000).astype(np.uint16)
    bands_data.append(b1)
    
    # Band 2 (Green) - Shifted pattern
    b2 = np.cos(X**2 + Y**2)
    b2 = ((b2 + 1) / 2 * 4000).astype(np.uint16)
    bands_data.append(b2)
    
    # Band 3 (Red) - Gradient
    b3 = np.zeros((height, width), dtype=np.uint16)
    for i in range(height):
        b3[i, :] = int((i / height) * 4000)
    bands_data.append(b3)
    
    # Band 4 (NIR) - Random vegetation-like noise + high reflection
    b4 = np.random.randint(2000, 8000, size=(height, width), dtype=np.uint16)
    bands_data.append(b4)
    
    # Define arbitrary transform (e.g., somewhere in the world, 10m resolution)
    transform = from_origin(300000.0, 4000000.0, 10.0, 10.0)
    
    print(f"Generating test GeoTIFF at {out_path}...")
    with rasterio.open(
        out_path, 'w', driver='GTiff',
        height=height, width=width,
        count=count, dtype=str(bands_data[0].dtype),
        crs='+proj=utm +zone=33 +datum=WGS84 +units=m +no_defs',
        transform=transform
    ) as dst:
        for i in range(count):
            dst.write(bands_data[i], i + 1)
            
    print(f"Successfully created {out_path} with {count} bands.")

if __name__ == "__main__":
    create_multiband_test_tif()
