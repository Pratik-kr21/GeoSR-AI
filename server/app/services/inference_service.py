import os
import rasterio
from rasterio.transform import Affine
import numpy as np
import torch

from app.services.storage_service import storage_service
from app.ml.model import SatelliteSRModel

class InferenceService:
    def __init__(self):
        # Determine device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"InferenceService initialized on device: {self.device}")
        
        # We will instantiate the model per-inference in this MVP to handle varying band counts,
        # but typically this is cached if band count is static.

    def run_super_resolution(self, input_path: str, output_path: str):
        print(f"Starting ML inference pipeline. MinIO Input: {input_path}")
        
        local_input = f"/tmp/input_{os.path.basename(input_path)}"
        local_output = f"/tmp/output_{os.path.basename(output_path)}"
        
        try:
            # 1. Download from Object Storage
            storage_service.download_file(input_path, local_input)
            
            # 2. Read GeoTIFF
            with rasterio.open(local_input) as src:
                meta = src.meta.copy()
                bands_data = src.read() # Shape: [C, H, W]
                in_channels, h, w = bands_data.shape
                
                # The tensor conversion is now handled inside the tile loop to save memory
                
            # 3. Initialize Model
            upscale_factor = 4
            
            # The weights were trained on 3 channels (RGB). If the input has more (e.g. NIR),
            # we must only process the first 3 channels to avoid state_dict size mismatches.
            model_channels = min(in_channels, 3)
            model = SatelliteSRModel(in_channels=model_channels, upscale_factor=upscale_factor)
            
            # Load trained weights if they exist
            weights_path = "/app/weights/srcnn_weights.pth"
            if os.path.exists(weights_path):
                print(f"Loading trained weights from {weights_path}")
                # Use strict=False just in case, but model_channels=3 should fix the root cause
                model.load_state_dict(torch.load(weights_path, map_location=self.device), strict=False)
            else:
                print("No trained weights found. Using uninitialized model.")
                
            model.to(self.device)
            model.eval()
            
            # 4. Tiled Inference to prevent OOM on massive GeoTIFFs
            tile_size = 1024
            new_h, new_w = h * upscale_factor, w * upscale_factor
            
            # 5. Update Raster Metadata for the 4x larger image
            transform = meta['transform']
            new_transform = Affine(
                transform.a / upscale_factor, transform.b, transform.c,
                transform.d, transform.e / upscale_factor, transform.f
            )
            
            meta.update({
                "height": new_h,
                "width": new_w,
                "transform": new_transform,
                "dtype": 'uint8',
                "count": model_channels # Ensure output is 3 channels even if input was 4
            })
            
            print(f"Processing image of size {h}x{w} in tiles of {tile_size}x{tile_size} and streaming to disk...")
            
            from rasterio.windows import Window
            
            with rasterio.open(local_output, 'w', **meta) as dst:
                with torch.no_grad():
                    for y in range(0, h, tile_size):
                        for x in range(0, w, tile_size):
                            # Extract tile
                            y_end = min(y + tile_size, h)
                            x_end = min(x + tile_size, w)
                            tile = bands_data[:model_channels, y:y_end, x:x_end]
                            
                            # Convert to tensor (cast to float32 to avoid uint16 PyTorch error)
                            tensor_tile = torch.from_numpy(tile.astype(np.float32)) / 65535.0 if tile.dtype == np.uint16 else torch.from_numpy(tile.astype(np.float32)) / 255.0
                            tensor_tile = tensor_tile.unsqueeze(0).to(self.device)
                            
                            # Forward pass
                            out_tile = model(tensor_tile) # Shape: [1, C, H_t*4, W_t*4]
                            
                            # Post-process
                            out_tile = out_tile.squeeze(0).cpu()
                            out_tile_arr = torch.clamp(out_tile * 255.0, 0, 255).byte().numpy()
                            
                            # Place directly in output file
                            out_y, out_x = y * upscale_factor, x * upscale_factor
                            out_h, out_w = out_tile_arr.shape[1], out_tile_arr.shape[2]
                            
                            dst.write(out_tile_arr, window=Window(out_x, out_y, out_w, out_h))
                            
            print("Inference complete!")
            
            # 6. Upload to Object Storage
            storage_service.upload_file(local_output, output_path)
            print(f"Successfully uploaded SR output to {output_path}")
            
        except Exception as e:
            print(f"Inference Pipeline Error: {e}")
            raise e
        finally:
            # Clean up local temporary files
            if os.path.exists(local_input):
                os.remove(local_input)
            if os.path.exists(local_output):
                os.remove(local_output)

        return True

inference_service = InferenceService()
