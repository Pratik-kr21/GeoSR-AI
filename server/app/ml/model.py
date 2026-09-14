import torch
import torch.nn as nn

class SatelliteSRModel(nn.Module):
    """
    A lightweight Super-Resolution architecture for Satellite Imagery.
    Uses PixelShuffle to upsample by a factor of 4.
    """
    def __init__(self, in_channels: int = 3, upscale_factor: int = 4):
        super(SatelliteSRModel, self).__init__()
        
        # Feature extraction
        self.feature_extraction = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=5, padding=2),
            nn.PReLU(),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.PReLU()
        )
        
        # Upsampling layer
        self.upsample = nn.Sequential(
            nn.Conv2d(64, in_channels * (upscale_factor ** 2), kernel_size=3, padding=1),
            nn.PixelShuffle(upscale_factor)
        )
        
    def forward(self, x):
        # x is expected to be shape [B, C, H, W]
        features = self.feature_extraction(x)
        out = self.upsample(features)
        # Residual connection (bicubic upscale of original + learned residual)
        # For simplicity in this scaffold, we just return the direct upsample output.
        return out
