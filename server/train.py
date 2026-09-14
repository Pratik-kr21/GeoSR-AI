import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import numpy as np

# Adjust imports since this is running from the 'server' directory
from app.ml.model import SatelliteSRModel

# -------------------------------------------------------------
# 1. Dataset Definition
# -------------------------------------------------------------
class GeoSRDataset(Dataset):
    """
    A simple PyTorch dataset that pairs low-res satellite images with 
    their high-res ground truth targets.
    
    If no actual files are provided, it generates synthetic data so you 
    can verify the training loop runs locally.
    """
    def __init__(self, low_res_dir="dataset/LR_2m/LR_2m", high_res_dir="dataset/HR_0.5m/HR_0.5m", upscale_factor=4, synthetic_samples=100):
        self.lr_paths = []
        self.hr_paths = []
        self.upscale_factor = upscale_factor
        
        # Check if actual directories exist and have files
        if os.path.exists(low_res_dir) and os.path.exists(high_res_dir):
            lr_files = sorted(os.listdir(low_res_dir))
            hr_files = sorted(os.listdir(high_res_dir))
            if len(lr_files) > 0 and len(lr_files) == len(hr_files):
                self.lr_paths = [os.path.join(low_res_dir, f) for f in lr_files]
                self.hr_paths = [os.path.join(high_res_dir, f) for f in hr_files]
        
        self.use_synthetic = len(self.lr_paths) == 0
        if self.use_synthetic:
            print("⚠️ No dataset found. Using synthetic random data for training loop verification.")
            self.synthetic_samples = synthetic_samples
        else:
            print(f"✅ Found {len(self.lr_paths)} image pairs.")

    def __len__(self):
        if self.use_synthetic:
            return self.synthetic_samples
        return len(self.lr_paths)

    def __getitem__(self, idx):
        if self.use_synthetic:
            # Generate dummy Low-Res (3, 64, 64) and High-Res (3, 256, 256)
            lr_tensor = torch.rand(3, 64, 64)
            hr_tensor = torch.rand(3, 64 * self.upscale_factor, 64 * self.upscale_factor)
            return lr_tensor, hr_tensor
            
        else:
            # Load real images
            # (Assuming you are using standard image formats like png/tif for training patches)
            lr_img = np.array(Image.open(self.lr_paths[idx]))
            hr_img = np.array(Image.open(self.hr_paths[idx]))
            
            # Normalize and convert to C,H,W
            lr_tensor = torch.from_numpy(lr_img.transpose((2, 0, 1)).astype(np.float32)) / 255.0
            hr_tensor = torch.from_numpy(hr_img.transpose((2, 0, 1)).astype(np.float32)) / 255.0
            
            # Crop to a consistent size to avoid PyTorch DataLoader stacking errors
            # (since Kaggle dataset images might differ by 1-2 pixels)
            # We crop a 64x64 patch from LR, and the corresponding 256x256 patch from HR
            lr_size = 64
            hr_size = lr_size * self.upscale_factor
            
            lr_tensor = lr_tensor[:, :lr_size, :lr_size]
            hr_tensor = hr_tensor[:, :hr_size, :hr_size]
            
            return lr_tensor, hr_tensor


from tqdm import tqdm

# -------------------------------------------------------------
# 2. Training Loop
# -------------------------------------------------------------
def train_model(epochs=10, batch_size=16, learning_rate=1e-3, in_channels=3, upscale_factor=4):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🚀 Initializing Training on Device: {device}")
    
    # 1. Prepare Data
    dataset = GeoSRDataset(upscale_factor=upscale_factor)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # 2. Initialize Model, Loss, and Optimizer
    model = SatelliteSRModel(in_channels=in_channels, upscale_factor=upscale_factor).to(device)
    criterion = nn.MSELoss() # Standard MSE for Super Resolution
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    print(f"Starting training for {epochs} epochs...\n" + "-"*40)
    
    # 3. Training Loop
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        
        # Use tqdm for a live progress bar
        progress_bar = tqdm(enumerate(dataloader), total=len(dataloader), desc=f"Epoch [{epoch+1}/{epochs}]")
        
        for batch_idx, (lr, hr) in progress_bar:
            lr, hr = lr.to(device), hr.to(device)
            
            # Zero gradients
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(lr)
            
            # Compute loss
            loss = criterion(outputs, hr)
            
            # Backward pass & Optimize
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
            # Update live loss in the progress bar
            progress_bar.set_postfix(live_loss=f"{loss.item():.4f}")
            
        avg_loss = epoch_loss / len(dataloader)
        print(f"Epoch [{epoch+1}/{epochs}] Completed | Average Loss: {avg_loss:.6f}\n")
        
    print("-"*40)
    print("✅ Training Complete!")
    
    # 4. Save the trained weights
    os.makedirs("weights", exist_ok=True)
    save_path = "weights/srcnn_weights.pth"
    torch.save(model.state_dict(), save_path)
    print(f"💾 Model weights saved successfully to: {save_path}")

if __name__ == "__main__":
    train_model(epochs=5, batch_size=8)
