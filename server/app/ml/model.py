import torch
import torch.nn as nn

class SatelliteSRModel(nn.Module):
    """
    A lightweight Super-Resolution architecture for Satellite Imagery.
    Uses PixelShuffle to upsample by a factor of 4.
    """
    def __init__(self, in_channels: int = 3, upscale_factor: int = 4):
        super(SatelliteSRModel, self).__init__()
        self.upscale_factor = upscale_factor
        
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
        import torch.nn.functional as F
        # x is expected to be shape [B, C, H, W]
        features = self.feature_extraction(x)
        res = self.upsample(features)
        
        # Global Residual Connection: Bicubic upscale of original + learned residual
        base = F.interpolate(x, scale_factor=self.upscale_factor, mode='bicubic', align_corners=False)
        out = base + res
        
        return out
