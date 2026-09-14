import os
import rasterio
from rasterio.windows import Window
import numpy as np
from PIL import Image
import cv2

# Configuration
INPUT_TIFF = "data/test_input.tif"
LR_DIR = "dataset/lr"
HR_DIR = "dataset/hr"
TILE_SIZE = 256  # Size of High-Res ground truth tiles
SCALE_FACTOR = 4 # Downscale factor (so LR will be 64x64)
MAX_TILES = 500  # Prevent filling up the hard drive

def generate_self_supervised_dataset():
    print(f"Creating directories {LR_DIR} and {HR_DIR}...")
    os.makedirs(LR_DIR, exist_ok=True)
    os.makedirs(HR_DIR, exist_ok=True)
    
    print(f"Opening {INPUT_TIFF}...")
    if not os.path.exists(INPUT_TIFF):
        print(f"Error: Could not find {INPUT_TIFF}")
        return
        
    tiles_generated = 0
    
    with rasterio.open(INPUT_TIFF) as src:
        height, width = src.height, src.width
        print(f"Image Dimensions: {width}x{height}")
        
        for y in range(0, height - TILE_SIZE, TILE_SIZE):
            for x in range(0, width - TILE_SIZE, TILE_SIZE):
                if tiles_generated >= MAX_TILES:
                    print(f"Reached limit of {MAX_TILES} tiles. Stopping extraction.")
                    return
                
                # Extract 256x256 tile
                window = Window(x, y, TILE_SIZE, TILE_SIZE)
                tile_data = src.read(window=window) # Shape: [C, H, W]
                
                # We only need RGB for this example (assuming bands 1, 2, 3 are RGB)
                # If it's a 4-band image (RGB + NIR), we will just extract the first 3 bands for standard image training
                if tile_data.shape[0] >= 3:
                    tile_data = tile_data[:3, :, :]
                
                # Convert to [H, W, C] for OpenCV/PIL
                img_hr = np.transpose(tile_data, (1, 2, 0))
                
                # Normalize 16-bit to 8-bit for Sentinel-2 (values usually 0-10000)
                if img_hr.dtype == np.uint16 or tile_data.dtype == np.uint16:
                    # Clip at 4000 (common for optical bands) and scale to 255
                    img_hr = np.clip(img_hr, 0, 4000)
                    img_hr = ((img_hr / 4000.0) * 255).astype(np.uint8)
                
                # Ignore tiles that are completely empty/black
                if np.max(img_hr) == 0 or np.mean(img_hr) < 5:
                    continue
                    
                # Downsample by 4x to create the Low-Res input (64x64)
                lr_size = (TILE_SIZE // SCALE_FACTOR, TILE_SIZE // SCALE_FACTOR)
                img_lr = cv2.resize(img_hr, lr_size, interpolation=cv2.INTER_CUBIC)
                
                # Save both pairs
                hr_path = os.path.join(HR_DIR, f"tile_{y}_{x}.png")
                lr_path = os.path.join(LR_DIR, f"tile_{y}_{x}.png")
                
                # PIL saves RGB arrays perfectly
                Image.fromarray(img_hr).save(hr_path)
                Image.fromarray(img_lr).save(lr_path)
                
                tiles_generated += 1
                if tiles_generated % 50 == 0:
                    print(f"Generated {tiles_generated} tiles...")

    print(f"Successfully generated {tiles_generated} paired training samples!")

if __name__ == "__main__":
    generate_self_supervised_dataset()
