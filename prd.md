# PRD — GeoSR-AI
## Trustworthy Satellite Super-Resolution & Mapping Platform

**Team:** Eklavya  
**Competition:** TEKATHON-5.0 — 2026  
**Problem Statement ID:** 26142  
**Problem Statement:** Deep Learning Based Super Resolution Mapping (SRM) from Medium Resolution Satellite Imageries  
**Theme:** Space Technology  
**Category:** Software

---

# 1. Product Overview

GeoSR-AI is an AI-powered geospatial platform designed to transform medium-resolution Sentinel-2 satellite imagery, typically at 10 m spatial resolution, into sharper information-rich products targeting approximately 2.5–4 m output resolution.

The product is explicitly designed as a **trustworthy super-resolution system**, not a conventional image upscaler. It combines:

- Geospatial preprocessing
- Multispectral feature learning
- CNN-based local feature extraction
- Spectral attention
- Transformer-based global spatial context
- Progressive super-resolution
- Controlled generative refinement using GAN and/or diffusion approaches
- Geographic consistency checking
- Spectral consistency validation
- Image-quality and downstream-task evaluation
- Uncertainty/confidence estimation
- Interactive GIS visualization
- Offline AI assistance through Ollama
- Local RAG knowledge retrieval

The system must clearly distinguish between **observed satellite information** and **AI-inferred fine-scale information**.

---

# 2. Problem Statement

Medium-resolution satellite imagery is valuable because of its broad coverage and frequent revisit capability, but 10–30 m imagery can be insufficient for fine-scale applications.

Important details may be difficult to interpret, including:

- Small buildings
- Narrow roads
- Field boundaries
- Water edges
- Localized damage
- Fine urban structures

A major challenge with generative super-resolution is that visually convincing details may be inferred or hallucinated by the model. Therefore, a useful system must improve spatial interpretability while maintaining the original imagery's geographic and spectral consistency and communicating uncertainty.

The source project presentation identifies three central concerns:

1. Resolution gap
2. AI hallucination risk
3. Lack of trust/confidence indication

GeoSR-AI addresses these through controlled SR, consistency validation, and confidence/uncertainty visualization.

---

# 3. Product Goals

## Primary Goals

1. Accept Sentinel-2 10 m imagery as input.
2. Preserve geospatial metadata and coordinate reference information.
3. Preprocess and align multispectral satellite bands.
4. Generate a target super-resolved product in the 2.5–4 m range.
5. Preserve spectral relationships as much as possible.
6. Enforce consistency with the original low-resolution observation.
7. Provide scientific validation metrics.
8. Produce an uncertainty/confidence layer.
9. Allow users to visually compare original, enhanced, reference, and uncertainty layers.
10. Provide an offline AI assistant through Ollama.
11. Support export of enhanced GeoTIFF and analysis results.

## Secondary Goals

- Support urban mapping
- Support crop monitoring
- Support disaster assessment
- Support environmental monitoring
- Demonstrate downstream analytical utility
- Provide a scalable architecture for future models

---

# 4. Non-Goals

The initial version should NOT claim that:

- Every generated feature is ground truth.
- Super-resolution creates genuinely observed 2.5 m satellite measurements.
- Ollama trains the super-resolution model.
- The system replaces high-resolution reference imagery.
- Visual sharpness alone proves scientific correctness.

The product should describe the output as an **AI-enhanced / super-resolved product** and communicate uncertainty.

---

# 5. Core Product Principle

## Evidence-Constrained Super Resolution

The central trust mechanism is:

```text
Original Sentinel-2 Input
        |
        v
AI Super-Resolution
        |
        v
Enhanced Output
        |
        v
Downsample Enhanced Output
        |
        v
Compare with Original Input
```

The principle is:

```text
Downsample(SR_Output) ≈ Original_Input
```

This reconstruction constraint should discourage the model from freely inventing unsupported structures.

---

# 6. Target Users

## Primary Users

- Remote sensing researchers
- GIS analysts
- Agriculture analysts
- Urban planners
- Disaster-response teams
- Environmental monitoring teams
- Geospatial students and researchers

## Secondary Users

- Government agencies
- Academic institutions
- Space-tech organizations
- Geospatial software teams

---

# 7. Key User Stories

### Upload

As a user, I want to upload a Sentinel-2 GeoTIFF so that I can run super-resolution analysis.

### AOI

As a user, I want to select an area of interest so that I can process only the required region.

### Enhancement

As a user, I want to run super-resolution so that fine spatial patterns become easier to interpret.

### Comparison

As a user, I want to compare original and enhanced imagery using a slider so that I can visually inspect improvements.

### Validation

As a user, I want to see PSNR, SSIM, LPIPS, SAM, edge accuracy, and geographic consistency so that I can assess output quality.

### Uncertainty

As a user, I want to see confidence/uncertainty on the map so that I know which generated regions require caution.

### Explanation

As a user, I want to ask an offline AI assistant why a region has low confidence.

### Export

As a user, I want to export the enhanced GeoTIFF, uncertainty layer, metrics, and report.

---

# 8. End-to-End Product Flow

```text
User
 |
 v
React Web Application
 |
 v
FastAPI API
 |
 +-------------------------+
 |                         |
 v                         v
Geospatial Pipeline       Job Manager
 |                         |
 v                         v
Rasterio/GDAL             Redis
 |
 v
Preprocessed Sentinel-2
 |
 v
PyTorch GeoSR Model
 |
 v
Super-Resolved Product
 |
 +----------------------+----------------------+
 |                      |                      |
 v                      v                      v
Validation          Uncertainty            GeoTIFF
 |                      |                      |
 v                      v                      v
Metrics              Confidence             Export
 |
 v
FastAPI
 |
 +-----------------------+
 |
 v
Ollama / GeoAssist
 |
 v
Natural-language explanation
```

---

# 9. Frontend Product Requirements

## 9.1 Frontend Stack

Recommended:

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack Query
- Zustand
- Leaflet or MapLibre GL / OpenLayers
- Axios
- Recharts
- Lucide React
- react-dropzone

Optional:

- deck.gl for advanced geospatial visualization
- Framer Motion for subtle animations

---

# 10. Frontend Design Language

The UI should combine:

- Space technology
- Professional GIS
- AI platform
- Scientific dashboard

Visual direction:

- Deep navy / near-black background
- Dark blue/charcoal surfaces
- Electric blue/cyan primary accents
- Purple secondary accent
- Green for high confidence
- Yellow/orange for medium confidence
- Red for low confidence
- 12–16 px card radius
- Thin borders
- Subtle shadows
- Minimal glassmorphism
- Clean data visualization
- High information density without clutter

Avoid a gaming-style appearance.

---

# 11. Frontend Pages

## 11.1 Landing Page

Hero:

**Turn Medium-Resolution Satellite Data into Trustworthy High-Resolution Insights.**

Subheading:

**GeoSR-AI enhances Sentinel-2 imagery from 10 m toward 2.5–4 m while preserving geospatial and spectral consistency and visualizing uncertainty.**

CTA:

- Launch GeoSR-AI
- Explore Technology

Hero visualization:

```text
10 m Sentinel-2
      |
      v
   GeoSR-AI
      |
      v
2.5–4 m Enhanced Product
```

Feature cards:

- Controlled Super Resolution
- Multispectral Intelligence
- Scientific Validation
- Uncertainty Heatmap

---

# 12. Dashboard

## Sidebar

- Dashboard
- New Analysis
- Projects
- Satellite Imagery
- Validation
- Reports
- GeoAssist AI
- Settings

Footer:

- Profile
- AI Engine Status

## Dashboard Header

Example:

**Project: Chandigarh Urban Analysis**

Metadata:

- Sentinel-2
- Input: 10 m
- Target: 2.5–4 m
- Bands
- CRS

Actions:

- Upload GeoTIFF
- Select AOI
- Run Enhancement

---

# 13. GIS Map Viewer

The central workspace must be a large map.

Supported layers:

- Original Image
- Enhanced Image
- Reference Image
- Uncertainty Map
- Confidence Layer
- NDVI / spectral layer

Map controls:

- Zoom
- Pan
- Layer toggle
- Fullscreen
- Fit to AOI

## Before/After Slider

Left:

**Original Sentinel-2 — 10 m**

Right:

**GeoSR-AI Enhanced — 2.5–4 m**

The slider should be one of the primary demo features.

---

# 14. Processing Panel

Display a vertical progress stepper:

```text
✓ Geo Preprocessing
✓ Cloud Handling
✓ Band Alignment
✓ Multispectral Feature Extraction
✓ Super Resolution
✓ Geo-Consistency Check
✓ Validation
```

Processing states:

- Pending
- Running
- Completed
- Failed

---

# 15. Results Dashboard

Show:

### Resolution

10 m → 2.5–4 m

### Metrics

- PSNR
- SSIM
- LPIPS
- Spectral Consistency / SAM
- Edge Accuracy
- Geo-Consistency
- Average Confidence

Metrics should be presented as cards and supporting charts.

---

# 16. Uncertainty Page

Display:

- Enhanced image
- Uncertainty heatmap
- Confidence map

Legend:

- Green = high confidence
- Yellow = medium confidence
- Red = low confidence

Summary:

```text
High confidence regions: XX%
Medium confidence regions: XX%
Low confidence regions: XX%
```

The UI must show a clear warning:

**AI-generated details in low-confidence regions are inferred information and should not be treated as confirmed ground truth.**

---

# 17. Validation Page

Compare:

```text
Original Input
      |
Enhanced Output
      |
High-Resolution Reference
```

Metrics:

- PSNR
- SSIM
- LPIPS
- SAM
- Edge Accuracy
- Geo-Consistency

## Geo-Consistency Visualization

```text
Enhanced Output
       |
       v
Downsample
       |
       v
Compare with Original Sentinel-2
```

Show a consistency score.

---

# 18. Project History

Each project should show:

- Name
- Location
- Satellite source
- Input resolution
- Output resolution
- Date
- Confidence
- Status
- Thumbnail

Example:

```text
Chandigarh Urban Mapping
10 m → 2.5 m
Confidence: 89%
Status: Completed
```

---

# 19. GeoAssist UI

Title:

**GeoAssist**

Subtitle:

**Offline AI Assistant for Satellite Image Interpretation**

Example prompt:

> Why is this region marked as low confidence?

Assistant context should include:

- Input resolution
- Output resolution
- Validation metrics
- Confidence statistics
- Uncertainty statistics
- Land-cover information if available

Badge:

**Running Locally via Ollama**

Suggested prompts:

- Explain validation results
- Analyze uncertainty
- Explain SAM score
- Compare original and enhanced image
- Generate analysis report

---

# 20. Export Modal

Options:

- Enhanced GeoTIFF
- Validation metrics
- Uncertainty heatmap
- Confidence map
- GeoAssist summary
- Metadata and CRS

Output formats:

- GeoTIFF
- CSV/JSON metrics
- PDF/HTML report where implemented

---

# 21. Backend Requirements

## Backend Stack

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic
- PyTorch
- TorchVision
- NumPy
- OpenCV
- Rasterio
- GDAL
- Shapely
- GeoPandas
- pyproj
- Pillow
- SciPy
- scikit-image
- scikit-learn
- LPIPS
- Redis
- PostgreSQL
- PostGIS
- SQLAlchemy
- Alembic
- Celery for long-running jobs
- httpx for Ollama API communication

Optional:

- MLflow
- TensorBoard
- Prometheus
- MinIO for object storage

---

# 22. Backend Architecture

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   │
│   ├── api/
│   │   ├── health.py
│   │   ├── projects.py
│   │   ├── upload.py
│   │   ├── preprocessing.py
│   │   ├── super_resolution.py
│   │   ├── validation.py
│   │   ├── uncertainty.py
│   │   ├── reports.py
│   │   └── assistant.py
│   │
│   ├── schemas/
│   │   ├── project.py
│   │   ├── analysis.py
│   │   ├── metrics.py
│   │   └── assistant.py
│   │
│   ├── services/
│   │   ├── raster_service.py
│   │   ├── preprocessing_service.py
│   │   ├── inference_service.py
│   │   ├── validation_service.py
│   │   ├── uncertainty_service.py
│   │   ├── report_service.py
│   │   └── ollama_service.py
│   │
│   ├── ml/
│   │   ├── model.py
│   │   ├── losses.py
│   │   ├── transforms.py
│   │   └── checkpoint.py
│   │
│   └── workers/
│       └── tasks.py
│
├── tests/
├── requirements.txt
└── Dockerfile
```

---

# 23. REST API

## Health

```http
GET /api/v1/health
```

## Create Project

```http
POST /api/v1/projects
```

## Upload

```http
POST /api/v1/projects/{project_id}/upload
Content-Type: multipart/form-data
```

Return:

- file ID
- resolution
- dimensions
- bands
- CRS
- bounds

## AOI

```http
POST /api/v1/projects/{project_id}/aoi
```

## Preprocess

```http
POST /api/v1/projects/{project_id}/preprocess
```

## Start SR

```http
POST /api/v1/projects/{project_id}/super-resolution
```

Return:

```json
{
  "job_id": "...",
  "status": "queued"
}
```

## Job Status

```http
GET /api/v1/jobs/{job_id}
```

## Metrics

```http
GET /api/v1/projects/{project_id}/metrics
```

## Uncertainty

```http
GET /api/v1/projects/{project_id}/uncertainty
```

## Layer

```http
GET /api/v1/projects/{project_id}/layers/{layer_name}
```

## GeoAssist

```http
POST /api/v1/projects/{project_id}/assistant
```

Request:

```json
{
  "message": "Why is this region low confidence?"
}
```

## Export

```http
POST /api/v1/projects/{project_id}/export
```

---

# 24. Geospatial Processing Pipeline

Input:

- Sentinel-2 GeoTIFF
- Multispectral bands
- Metadata

Steps:

1. Validate file.
2. Read CRS.
3. Read transform.
4. Read bounds.
5. Read band metadata.
6. Check resolution.
7. Align bands.
8. Normalize values.
9. Handle invalid/no-data pixels.
10. Apply cloud/cloud-shadow handling when masks are available.
11. Crop into overlapping tiles.
12. Run inference.
13. Stitch tiles.
14. Restore geotransform.
15. Write GeoTIFF.

The output must preserve:

- CRS
- Transform
- Bounds
- Band metadata
- NoData where appropriate

---

# 25. Model Architecture

## Proposed GeoSR-Former

```text
Sentinel-2 10m Input
        |
        v
Geo Preprocessing
        |
        v
Multispectral CNN Encoder
        |
        v
Spectral Attention
        |
        v
Swin Transformer
        |
        v
Global Spatial Context
        |
        v
Progressive SR Decoder
        |
        v
Controlled GAN / Diffusion Refinement
        |
        v
Enhanced 2.5–4m Product
        |
        v
Trust Layer
```

---

# 26. Multispectral Input

Initial supported bands can include:

- B2 — Blue
- B3 — Green
- B4 — Red
- B8 — Near Infrared

Optional future support:

- Red-edge bands
- Additional Sentinel-2 bands

The system should be designed so that the number of channels is configurable.

---

# 27. Model Training

## Training Pair

Preferred conceptual pair:

```text
High-Resolution Reference
          |
          v
Synthetic Degradation
          |
          v
Synthetic Medium-Resolution Input
          |
          v
GeoSR Model
          |
          v
Predicted High-Resolution Output
```

Degradation can model:

- Blur
- Noise
- Downsampling
- Sensor characteristics
- Compression
- Misalignment

The exact degradation model must be validated against the available training data.

---

# 28. Training Dataset

The project should use paired or pseudo-paired imagery where licensing permits.

Potential data sources for research/prototyping may include:

- Sentinel-2
- High-resolution aerial imagery
- Open geospatial datasets
- UAV imagery
- SpaceNet-style datasets
- Other appropriately licensed reference imagery

The implementation must document:

- Dataset source
- Geographic coverage
- Resolution
- Band availability
- Licensing
- Train/validation/test split

Do not claim that every source provides a direct Sentinel-2 10 m to 2.5 m pair unless it actually does.

---

# 29. Loss Function

Recommended combined objective:

```text
L_total =
    α L_pixel
  + β L_perceptual
  + γ L_adversarial
  + δ L_spectral
  + ε L_edge
  + ζ L_geo
```

## Pixel Loss

Preserve reconstruction fidelity.

## Perceptual Loss

Preserve meaningful structural features.

## Adversarial Loss

Encourage realistic textures when a GAN approach is used.

## Spectral Loss

Preserve spectral relationships.

Possible implementation:

- Spectral Angle Mapper based loss
- Band relationship loss

## Edge Loss

Emphasize boundaries:

- Roads
- Buildings
- Fields
- Water boundaries

## Geo-Consistency Loss

```text
L_geo =
Distance(
    Downsample(SR_Output),
    Original_Input
)
```

This is one of the core trust mechanisms.

---

# 30. Progressive Upscaling

Instead of one large scaling operation:

```text
10m
 ↓
5m
 ↓
2.5–4m
```

This can make the architecture easier to control and validate.

The exact scale should be configurable based on the training dataset and model.

---

# 31. Controlled Generative Refinement

The generative component should be conditional on the original observation and learned features.

Concept:

```text
Original Sentinel
      +
CNN Features
      +
Transformer Features
      |
      v
Controlled Generator
      |
      v
Fine Detail
```

The system must not be presented as recovering information that was physically observed at the target resolution.

---

# 32. Validation System

Required metrics:

### PSNR

Pixel-level reconstruction quality.

### SSIM

Structural similarity.

### LPIPS

Perceptual similarity.

### SAM

Spectral Angle Mapper / spectral consistency.

### Edge Accuracy

Boundary preservation.

### Geo-Consistency

Agreement after degrading SR output back to input resolution.

---

# 33. Downstream Validation

The strongest evaluation is not only image metrics.

Evaluate whether the SR output improves downstream tasks.

Example:

```text
Original 10m
     |
     v
Building/Road/Crop Analysis
     |
     v
Accuracy A

SR Output
     |
     v
Building/Road/Crop Analysis
     |
     v
Accuracy B
```

Report:

```text
Improvement = B - A
```

Possible tasks:

- Building detection
- Road segmentation
- Crop classification
- Flood/damage mapping
- Land-cover classification

---

# 34. Uncertainty Engine

The system should estimate uncertainty using one or more methods.

Recommended prototype approach:

## MC Dropout

Run inference multiple times with stochastic dropout.

```text
Input
 |
 +--> Prediction 1
 +--> Prediction 2
 +--> Prediction 3
 +--> Prediction 4
 +--> Prediction 5
 |
 v
Prediction Variance
 |
 v
Uncertainty Map
```

Alternative:

- Ensemble models
- Diffusion sample variance
- Reconstruction error

The architecture should allow multiple uncertainty methods.

---

# 35. Confidence Score

Create a normalized confidence layer from relevant uncertainty/validation signals.

Conceptually:

```text
Confidence =
f(
  prediction stability,
  spectral consistency,
  reconstruction consistency,
  local error
)
```

The exact formula must be calibrated on validation data rather than arbitrarily interpreted as probability.

Avoid calling an uncalibrated score a statistically calibrated probability.

---

# 36. Ollama Offline AI

## Critical Architecture Rule

Ollama is NOT the super-resolution model.

PyTorch handles:

- Training
- Model inference
- Image enhancement

Ollama handles:

- Natural-language explanations
- Metric interpretation
- Uncertainty explanation
- Remote-sensing knowledge assistance
- Report generation
- Offline interaction

Architecture:

```text
React
 |
 v
FastAPI
 |
 +----------------------+
 |                      |
 v                      v
GeoSR PyTorch        Ollama
                       |
                       v
                    Local LLM
```

---

# 37. Ollama Docker Setup

Recommended local architecture:

```text
docker-compose
 |
 +-- frontend
 |
 +-- backend
 |
 +-- worker
 |
 +-- redis
 |
 +-- postgres/postgis
 |
 +-- ollama
```

Example service:

```yaml
ollama:
  image: ollama/ollama
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
```

For GPU deployment, configure the container runtime and Ollama service for the host's NVIDIA GPU where available.

The exact GPU configuration should be adapted to the target machine.

---

# 38. Ollama Model Strategy

Do not train a large language model from scratch.

Use a compact local instruct model supported by the available Ollama runtime.

The model should be configured with a GeoAssist system instruction:

```text
You are GeoAssist, an offline remote sensing AI assistant.

You specialize in:
- Sentinel-2 imagery
- Satellite super-resolution
- Spectral analysis
- Geospatial validation
- Uncertainty interpretation
- Land-cover analysis

Never claim AI-generated details are ground truth.
Clearly distinguish observed information from model-inferred information.
When discussing confidence, explain that confidence is model-derived unless statistically calibrated.
```

---

# 39. Ollama RAG

Use local retrieval rather than relying entirely on model memory.

Potential local knowledge:

- Sentinel-2 documentation
- Project documentation
- Model documentation
- Validation methodology
- Remote sensing research papers
- Internal FAQs
- Metrics explanations

Recommended stack:

- ChromaDB or FAISS
- Local embedding model
- Ollama generation model
- FastAPI orchestration

Flow:

```text
User Question
      |
      v
FastAPI
      |
      v
Embedding Model
      |
      v
Vector Search
      |
      v
Relevant Local Documents
      |
      v
Prompt + Project Metrics
      |
      v
Ollama
      |
      v
Answer
```

---

# 40. Ollama Context Injection

The backend should provide structured project context.

Example:

```json
{
  "input_resolution_m": 10,
  "output_resolution_m": 2.5,
  "psnr_db": 32.8,
  "ssim": 0.91,
  "spectral_consistency": 0.94,
  "geo_consistency": 0.96,
  "average_confidence": 0.87,
  "low_confidence_region_percentage": 7.0
}
```

The LLM should explain the supplied measurements rather than inventing measurements.

---

# 41. Docker Architecture

Recommended repository:

```text
GeoSR-AI/
├── frontend/
├── backend/
├── training/
├── ollama/
├── data/
├── models/
├── scripts/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Containers

### frontend

React application.

### backend

FastAPI API.

### worker

Celery worker for long-running SR jobs.

### redis

Task queue.

### postgres

Application database.

### postgis

Geospatial database capability, either through a PostGIS-enabled PostgreSQL image or the project's database service.

### ollama

Offline LLM runtime.

### Optional

MinIO for local object storage.

---

# 42. Docker Volumes

Persistent volumes:

```text
ollama_data
postgres_data
redis_data
model_data
project_data
```

Never store large training datasets inside the Docker image.

Mount them as volumes.

---

# 43. Environment Variables

Example:

```env
APP_ENV=development

DATABASE_URL=postgresql+psycopg://geosr:password@postgres:5432/geosr

REDIS_URL=redis://redis:6379/0

OLLAMA_BASE_URL=http://ollama:11434

OLLAMA_MODEL=<local-model-name>

MODEL_PATH=/models/geosr_model.pt

DATA_DIR=/data

OUTPUT_DIR=/data/outputs

MAX_UPLOAD_SIZE_MB=2048
```

Secrets must not be committed.

Provide `.env.example`.

---

# 44. Job Processing

Super-resolution can be computationally expensive.

Do not block the FastAPI request until inference finishes.

Use:

```text
FastAPI
  |
  v
Redis Queue
  |
  v
Celery Worker
  |
  v
GPU / PyTorch
```

API returns:

```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

Frontend polls or uses WebSocket/SSE to display progress.

---

# 45. Database Model

## Project

Fields:

- id
- name
- description
- location
- created_at
- status

## ImageAsset

- id
- project_id
- filename
- path/object key
- CRS
- width
- height
- bands
- resolution
- bounds

## AnalysisJob

- id
- project_id
- status
- progress
- model_version
- started_at
- completed_at
- error

## Metrics

- job_id
- PSNR
- SSIM
- LPIPS
- SAM
- edge_accuracy
- geo_consistency
- confidence

## OutputAsset

- id
- job_id
- type
- path/object key
- metadata

---

# 46. Security Requirements

- Validate uploaded file type.
- Restrict upload size.
- Sanitize filenames.
- Never execute uploaded files.
- Validate raster structure.
- Isolate processing workers.
- Do not expose Ollama directly to the public internet.
- Keep model endpoints internal.
- Use environment variables for credentials.
- Add authentication if deployed beyond a demo environment.

---

# 47. Performance Requirements

For prototype:

- Process small AOIs interactively.
- Use tiled inference.
- Use GPU when available.
- Display job progress.
- Cache generated outputs.
- Avoid repeatedly processing identical input + model configuration.

Large scenes should be processed asynchronously.

---

# 48. Error Handling

Common cases:

### Invalid file

Return:

> Unsupported or invalid GeoTIFF.

### Missing CRS

Return:

> Input imagery does not contain sufficient geospatial reference metadata.

### Unsupported bands

Return:

> Required multispectral bands are unavailable.

### GPU memory error

Automatically reduce tile size or return a clear recommendation.

### Model unavailable

Display:

> Super-resolution model is currently unavailable.

### Ollama unavailable

GeoSR processing must continue independently.

Display:

> GeoAssist unavailable; core satellite processing remains operational.

---

# 49. Observability

Add:

- FastAPI logs
- Worker logs
- Job status
- Model inference duration
- GPU memory usage where available
- Failed job tracking
- Model version tracking

Optional:

- Prometheus
- Grafana
- MLflow

---

# 50. Model Versioning

Every result should record:

- Model name
- Model version
- Training dataset version
- Configuration
- Input bands
- Scale factor
- Inference timestamp

Example:

```text
Model:
GeoSR-Former-v0.1

Scale:
4x

Input:
Sentinel-2 RGB + NIR

Output:
2.5m equivalent target
```

---

# 51. Prototype Development Phases

## Phase 1 — UI

Build:

- Landing page
- Dashboard
- Upload
- GIS viewer
- Before/after slider
- Results cards
- Uncertainty page
- GeoAssist page

Use mock data initially.

## Phase 2 — Backend

Build:

- FastAPI
- Upload API
- Raster metadata extraction
- Project database
- Job system
- GeoTIFF output

## Phase 3 — AI

Start with a baseline SR model.

Then progressively add:

- Multispectral support
- Spectral attention
- Transformer module
- Geo-consistency loss
- Generative refinement

## Phase 4 — Validation

Implement:

- PSNR
- SSIM
- LPIPS
- SAM
- Edge accuracy
- Geo-consistency

## Phase 5 — Uncertainty

Implement:

- MC Dropout / ensemble
- Prediction variance
- Confidence visualization

## Phase 6 — Ollama

Implement:

- Ollama Docker
- Local instruct model
- GeoAssist prompt
- Local RAG
- Project-context injection

## Phase 7 — Integration

Connect:

```text
React
 ↕
FastAPI
 ↕
Celery
 ↕
PyTorch
 ↕
GeoTIFF
```

and:

```text
FastAPI
 ↕
Ollama
 ↕
RAG
```

---

# 52. Hackathon MVP Scope

The recommended MVP is:

```text
React
+
FastAPI
+
Rasterio/GDAL
+
PyTorch SR model
+
GeoTIFF input/output
+
Before/After Viewer
+
Validation Metrics
+
Basic Uncertainty
+
Ollama GeoAssist
```

The following should be presented as advanced/scalable components if not fully implemented:

- Full custom GeoSR-Former
- Diffusion refinement
- Large-scale production inference
- Extensive downstream-task validation
- Full statistical confidence calibration

This prevents overclaiming.

---

# 53. Demo Scenario

Use a recognizable test case such as an urban or agricultural AOI.

Demo sequence:

```text
1. Open GeoSR-AI
2. Create project
3. Upload Sentinel-2 GeoTIFF
4. Display metadata
5. Select AOI
6. Run preprocessing
7. Start super-resolution
8. Show progress
9. Show enhanced output
10. Use before/after slider
11. Zoom into buildings/roads/fields
12. Open validation
13. Show metrics
14. Enable uncertainty layer
15. Click low-confidence region
16. Ask GeoAssist why
17. Export GeoTIFF + report
```

---

# 54. Success Metrics

## Product

- Successful GeoTIFF upload rate
- Processing completion rate
- Average inference time
- Export success rate

## Model

- PSNR
- SSIM
- LPIPS
- SAM
- Edge accuracy
- Geo-consistency
- Downstream-task improvement

## Trust

- Percentage of low-confidence regions correctly flagged
- Agreement between uncertainty and validation error
- Calibration quality if confidence is presented probabilistically

---

# 55. Acceptance Criteria

The MVP is considered successful when:

### Input

- User can upload valid Sentinel-2 GeoTIFF.
- System reads CRS and raster metadata.

### Processing

- System preprocesses the input.
- Model produces an enhanced raster.
- Output retains geospatial reference.

### Visualization

- User can compare original and enhanced imagery.
- User can toggle uncertainty layer.

### Validation

- Metrics are calculated and displayed.
- Geo-consistency check is performed.

### AI Assistant

- Ollama runs locally.
- GeoAssist can explain supplied metrics.
- GeoAssist clearly distinguishes inference from observation.

### Export

- Enhanced GeoTIFF can be exported.
- Metrics can be exported.
- Uncertainty layer can be exported.

---

# 56. Recommended Technical Stack Summary

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| Styling | Tailwind CSS |
| State | Zustand |
| API Data | TanStack Query |
| Maps | MapLibre GL / Leaflet / OpenLayers |
| Charts | Recharts |
| Backend | FastAPI |
| Async Jobs | Celery |
| Queue | Redis |
| Database | PostgreSQL + PostGIS |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| AI Training | PyTorch |
| Vision | TorchVision / OpenCV |
| Raster | Rasterio + GDAL |
| Geospatial | GeoPandas + Shapely + pyproj |
| Metrics | scikit-image + LPIPS + custom SAM |
| LLM Runtime | Ollama |
| RAG | ChromaDB or FAISS |
| Embeddings | Local embedding model |
| Containers | Docker + Docker Compose |
| GPU | NVIDIA CUDA where available |
| Testing | Pytest + Vitest |
| API Docs | FastAPI OpenAPI |
| Experiment Tracking | MLflow / TensorBoard |
| Object Storage | Local filesystem / MinIO |

---

# 57. Suggested Package List

## Frontend

```text
react
react-dom
typescript
vite
tailwindcss
react-router-dom
@tanstack/react-query
zustand
axios
react-dropzone
lucide-react
recharts
maplibre-gl
```

Use only the mapping library actually selected for the implementation.

## Backend

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-multipart
sqlalchemy
psycopg
alembic
redis
celery
httpx
numpy
scipy
pillow
opencv-python-headless
rasterio
geopandas
shapely
pyproj
scikit-image
scikit-learn
lpips
```

## AI

```text
torch
torchvision
timm
einops
```

Optional, depending on architecture:

```text
diffusers
transformers
accelerate
```

Do not add every optional library unless the implementation actually requires it.

## RAG

```text
chromadb
sentence-transformers
```

or a lighter FAISS-based implementation:

```text
faiss-cpu
sentence-transformers
```

---

# 58. Testing Strategy

## Frontend

Test:

- Upload component
- Map layer controls
- Slider
- Metrics rendering
- Chat interface
- Export modal

## Backend

Test:

- Upload validation
- Metadata extraction
- API schemas
- Job state transitions
- Metric calculations
- Ollama failure handling

## AI

Test:

- Model input dimensions
- Output dimensions
- GeoTIFF metadata preservation
- Numerical stability
- Reproducibility
- Validation metrics

## Integration

Test:

```text
Upload
 →
Preprocess
 →
Inference
 →
Validation
 →
Uncertainty
 →
Export
```

---

# 59. Key Innovation Claims

The product should emphasize these six innovations:

## 1. GeoSR-Former

Hybrid multispectral CNN + spectral attention + transformer-based global context.

## 2. Evidence-Constrained SR

The generated output is constrained against the original observation.

## 3. Spectral Preservation

Satellite imagery is treated as multispectral information rather than ordinary RGB photography.

## 4. Uncertainty-Aware Output

The platform identifies regions where AI-generated details are less reliable.

## 5. Analytical Validation

The system evaluates whether enhancement actually improves downstream geospatial analysis.

## 6. Offline GeoAssist

Ollama provides local AI assistance without requiring continuous cloud LLM access.

---

# 60. Final Product Positioning

GeoSR-AI should be positioned as:

> **A trustworthy, evidence-aware satellite super-resolution and mapping platform that enhances 10 m Sentinel-2 imagery toward 2.5–4 m products while preserving spectral/geospatial consistency, validating output quality, and explicitly communicating uncertainty.**

The product is not simply:

> "AI image upscaling."

It is:

> **Super-resolution + geospatial integrity + validation + uncertainty + analytical utility + offline AI assistance.**

---

# 61. Reference Basis

The current project presentation supplied for this PRD identifies:

- TEKATHON-5.0 2026
- Problem Statement ID 26142
- Deep Learning Based Super Resolution Mapping from Medium Resolution Satellite Imageries
- Space Technology theme
- Software category
- Team Eklavya

It also identifies the project as **GeoSR-AI — Trustworthy Satellite Super-Resolution & Mapping**, and its research/reference slide includes Sentinel-2 Handbook / Copernicus Mission, DSen2, Sentinel-2 SISR, LPIPS, MC Dropout, Bicubic, ESRGAN, and SwinIR. The implementation details in this PRD expand the architecture and engineering plan discussed during project planning; they should be treated as the proposed technical specification rather than claims that every component is already implemented.

