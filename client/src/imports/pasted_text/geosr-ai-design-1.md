Design a modern, premium, dark-themed web application UI called “GeoSR-AI – Trustworthy Satellite Super-Resolution & Mapping.”

The platform is an AI-powered geospatial application that takes 10m Sentinel-2 satellite GeoTIFF imagery and generates enhanced 2.5m–4m super-resolution imagery, while preserving geographic and spectral consistency and showing uncertainty/confidence of AI-generated details.

The design should feel like a combination of:

NASA / space technology dashboard
Modern AI platform
Professional GIS software
Premium SaaS application

Use a dark space-inspired interface with deep navy/black backgrounds, subtle grid patterns, satellite imagery, glowing map elements, and accents of electric blue, cyan, purple, and green. Avoid excessive gradients or gaming-style visuals. The interface should look scientifically reliable, professional, and hackathon-demo ready.

Create a complete responsive desktop web application with the following screens:
1. Landing / Home Page

Create a premium landing page introducing GeoSR-AI.

Hero Section

Large heading:

Turn Medium-Resolution Satellite Data into Trustworthy High-Resolution Insights.

Subheading:

GeoSR-AI enhances Sentinel-2 imagery from 10m resolution to 2.5m–4m using AI-powered super-resolution while preserving geospatial and spectral consistency and clearly visualizing uncertainty.

Add two CTA buttons:

Launch GeoSR-AI
Explore Technology

Include a visually impressive satellite image transformation:

10m Input → AI Processing → Enhanced 2.5m Output

Show a before-and-after satellite imagery slider or split comparison.

Add small floating metric cards:

10m → 2.5m–4m
Spectral Aware
Geo-Consistent
Confidence-Aware
Offline AI Assistant

Below the hero section, show four feature cards:

Controlled Super Resolution

AI-generated details remain constrained by the original satellite observation.

Multispectral Intelligence

Uses Sentinel-2 spectral bands instead of treating imagery as a normal RGB image.

Scientific Validation

Measures PSNR, SSIM, LPIPS, SAM spectral accuracy, and edge/boundary accuracy.

Uncertainty Heatmap

Highlights regions where AI-generated details have lower confidence.

2. Main GeoSR-AI Dashboard

Create a full-screen GIS-style dashboard.

Left Sidebar Navigation

Logo: GeoSR-AI

Navigation items with modern icons:

Dashboard
New Analysis
Projects
Satellite Imagery
Validation
Reports
GeoAssist AI
Settings

At the bottom:

User Profile
System Status: AI Engine Online
Main Workspace

At the top:

Project: Chandigarh Urban Analysis

Display metadata chips:

Sentinel-2
Resolution: 10m
Output: 2.5m
RGB + NIR
CRS Preserved

Include action buttons:

Upload GeoTIFF
Select AOI
Run Enhancement
3. Interactive Satellite Map

The central part of the dashboard should contain a large interactive satellite map.

Create a before/after comparison slider.

Left side:

Original Sentinel-2 – 10m

Right side:

GeoSR-AI Enhanced – 2.5m

Show realistic satellite imagery containing:

Urban buildings
Roads
Agricultural fields
Water bodies

Add map controls:

Zoom in/out
Layers
Fullscreen
Compare mode

Create layer toggles:

Enhanced Image
Original Image
Uncertainty Map
Confidence Layer
Reference Image
NDVI / Spectral Layer
4. Analysis Control Panel

On the right side, create an AI processing panel.

Processing Pipeline

Display a vertical stepper:

Geo Preprocessing ✓
Cloud Masking ✓
Band Alignment ✓
Multispectral Feature Extraction ✓
Super Resolution ✓
Geo-Consistency Check ✓
Validation ✓

Show the current processing status with animated progress indicators.

Add:

Run Super Resolution

Primary glowing CTA button.

5. AI Results Dashboard

Below or beside the map, create a clean metrics section.

Resolution Improvement

Large visual:

10m → 2.5m

Validation Metrics

Create premium data cards:

PSNR
32.8 dB

SSIM
0.91

Spectral Consistency
94%

Average Confidence
87%

Low Confidence Regions
12

Use subtle mini charts, progress bars, and scientific visualization styling.

6. Uncertainty & Confidence Page

Create a dedicated scientific analysis screen.

Show:

Enhanced Satellite Image

Beside:

AI Uncertainty Heatmap

Use a heatmap visualization:

Green = High Confidence
Yellow = Medium Confidence
Red = Low Confidence

Add an information panel:

AI Trust Analysis

Example:

High confidence regions: 72%
Medium confidence regions: 21%
Low confidence regions: 7%

Add an explanation:

Generated details in low-confidence regions should be interpreted as AI-inferred information rather than confirmed ground truth.

Include a “Why is this region uncertain?” button.

7. Validation Page

Create a scientific validation dashboard.

Show comparison between:

Original Input
vs
Enhanced Output
vs
High-Resolution Reference

Display charts for:

PSNR
SSIM
LPIPS
SAM Spectral Accuracy
Edge Accuracy

Also include:

Geo-Consistency Validation

Create a visual flow:

Enhanced Output → Downsample → Compare with Original Sentinel-2 Input

Display:

Geo-Consistency Score: 96%

Explain visually that the enhanced output must remain consistent with the original satellite observation.

8. GeoAssist AI Page

Create an offline AI assistant interface powered by Ollama.

The assistant should be called:

GeoAssist

Subtitle:

Offline AI Assistant for Satellite Image Interpretation

Create a modern AI chat interface.

Show example messages:

User:
Why is this area marked as low confidence?

GeoAssist:
This region shows high prediction variance and weaker agreement with surrounding spectral patterns. The enhanced details in this area should be treated as inferred rather than directly observed.

Add suggested prompts:

Explain validation results
Analyze uncertainty
What does SAM score mean?
Compare original vs enhanced image
Generate analysis report

On the side, show contextual information:

Current Analysis Context
Input: Sentinel-2 GeoTIFF
Resolution: 10m
Enhanced Resolution: 2.5m
Spectral Consistency: 94%
Confidence: 87%

Include a small badge:

Running Locally via Ollama

9. Project History Page

Create a table/grid of previous satellite analysis projects.

Example projects:

Chandigarh Urban Mapping

10m → 2.5m
Confidence: 89%

Punjab Crop Monitoring

10m → 4m
Confidence: 92%

Flood Damage Assessment

10m → 2.5m
Confidence: 78%

Each project card should show:

Satellite preview thumbnail
Location
Input resolution
Output resolution
Date
Confidence score
Status
10. Export Report Modal

Create a premium modal for exporting results.

Title:

Export Analysis

Selectable options:

☑ Enhanced GeoTIFF

☑ Validation Metrics

☑ Uncertainty Heatmap

☑ Confidence Map

☑ GeoAssist AI Summary

☑ Metadata & CRS Information

Buttons:

Cancel
Generate Report
Design System

Use:

Typography

Modern sans-serif fonts such as Inter, Manrope, or Geist.

Colors

Primary background:

Deep Navy / Almost Black

Secondary surfaces:

Dark Blue
Charcoal

Accent colors:

Electric Blue
Cyan
Emerald Green
Purple

Use green primarily for:

High confidence
Successful validation

Use yellow/orange for:

Medium confidence
Warnings

Use red only for:

Low confidence
Errors
UI Style
Glassmorphism only subtly
Rounded cards, approximately 12–16px radius
Soft shadows
Thin borders
Minimal gradients
Clean scientific data visualizations
Premium enterprise SaaS quality
Spacious layout
Strong visual hierarchy
Important UX Requirements

The UI must clearly communicate that:

GeoSR-AI does not simply make satellite images visually sharper.

It provides:

AI-powered super-resolution
Multispectral preservation
Geographic consistency
Scientific validation
Uncertainty visualization
Confidence-aware outputs

Make the Before vs After satellite comparison the visual centerpiece of the application.

The final design should look like a polished product similar to a professional geospatial intelligence platform, suitable for demonstrating at a national-level hackathon and convincing technical judges that the system is scientifically reliable, innovative, and production-ready.