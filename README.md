# 🛰️ GeoSR-AI — Satellite Super-Resolution Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-SRCNN-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![SIH](https://img.shields.io/badge/Smart_India-Hackathon-FF6B35?style=for-the-badge)

**A full-stack AI platform for upscaling satellite imagery from 10m to 2.5m resolution using PyTorch SRCNN, with an interactive geospatial dashboard and an offline AI assistant.**

[Features](#-key-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API Docs](#-api-reference) • [Usage](#-usage-guide)

</div>

---

## 🔭 Overview

**GeoSR-AI** is a production-grade platform built for the **Smart India Hackathon (SIH)** that applies deep learning-based super-resolution (SR) to Sentinel-2 satellite GeoTIFFs. It upscales the native 10m/pixel resolution to **2.5m/pixel (4× enhancement)** using a trained **SRCNN (Super-Resolution Convolutional Neural Network)** model, making it viable for precision agriculture, urban planning, disaster response, and defence applications.

The system is engineered to handle **multi-gigabyte GeoTIFFs** efficiently through **tiled streaming inference** — tiles are processed in 1024×1024 chunks and written directly to disk, preventing out-of-memory errors that would otherwise crash naive implementations.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🧠 **Tiled ML Inference** | Processes massive GeoTIFFs tile-by-tile using PyTorch SRCNN without OOM errors. Supports 4-channel (RGB+NIR) Sentinel-2 inputs. |
| 🗺️ **Interactive Map Viewer** | React-Leaflet integration with server-side CRS reprojection (UTM → WGS84) and percentile-normalized thumbnails for live web preview. |
| 📊 **Quantitative Validation** | Auto-calculates PSNR, SSIM, Geo-Consistency, Avg Confidence, and Edge Accuracy metrics for every enhancement job. |
| 🌡️ **Uncertainty Mapping** | Heatmap overlay showing per-pixel confidence scores from the SR model, highlighting clouds, shadows, and edge ambiguities. |
| 🤖 **GeoAssist (Offline LLM)** | Conversational AI assistant powered by **Ollama** (fully local, no data leaves your machine) for interpreting validation results and satellite anomalies. |
| 📁 **Project Management** | Full CRUD lifecycle for satellite analysis projects with metadata (location, resolution, timestamps) stored in PostgreSQL. |
| 📤 **One-Click Export** | Download the enhanced GeoTIFF and validation JSON report directly from the dashboard. |
| ⚙️ **Async Job Queue** | Celery + Redis queue ensures SR jobs never block the API. The frontend polls for real-time progress updates. |
| ☁️ **S3-Compatible Storage** | All input and output GeoTIFFs are stored in MinIO — horizontally scalable to petabytes of satellite data. |
| 🐳 **Fully Dockerized** | One `docker-compose up` starts every service: DB, Redis, MinIO, Ollama, Backend, and Worker. |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (React + Vite)                   │
│   Landing → Dashboard → Validation → Uncertainty → GeoAssist    │
│                    React-Leaflet Map Viewer                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (Axios)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                         │
│  /projects  /upload  /super-resolution  /map  /validation       │
│              /assistant (Ollama proxy)                          │
└──────┬────────────────────────────────────────┬─────────────────┘
       │                                        │
       ▼                                        ▼
┌─────────────┐   Job Queue (Redis)   ┌────────────────────────┐
│  PostgreSQL │ ◄──────────────────── │   Celery ML Worker     │
│  (Projects, │                       │   PyTorch SRCNN        │
│   Jobs, DB) │ ──────────────────── ►│   Tiled Inference      │
└─────────────┘                       └───────────┬────────────┘
                                                   │ read/write
                                                   ▼
┌──────────────────────────────────────────────────────────────┐
│             MinIO Object Storage (S3-Compatible)              │
│   projects/1/inputs/<uuid>_file.tif                          │
│   projects/1/outputs/sr_<uuid>_file.tif                      │
└──────────────────────────────────────────────────────────────┘
                                    │
                              Ollama (Local LLM)
                         http://ollama:11434 (GPU/CPU)
```

---

## 🧠 ML Model — SRCNN

The core model is a **Super-Resolution Convolutional Neural Network (SRCNN)** adapted for satellite imagery.

- **Input**: 3-band normalized float tensor `[B, 3, H, W]` (RGB channels from Sentinel-2)
- **Architecture**: Feature extraction → Non-linear mapping → Reconstruction conv layers
- **Upscale Factor**: 4× (10m → 2.5m)
- **Output**: `uint8` 3-band GeoTIFF with identical CRS and updated geo-transform
- **Training Data**: Self-generated paired low-res/high-res tiles from raw Sentinel-2 GeoTIFFs
- **Device**: CUDA GPU (auto-falls back to CPU if no GPU available)

> **Note**: The trained weights (`srcnn_weights.pth`) are loaded from `/app/weights/`. The model gracefully slices 4-channel (RGB+NIR) inputs to 3 channels to match the weight architecture.

---

## 🏗️ Technology Stack

### 🎨 Frontend (`/client`)
| Tech | Purpose |
|------|---------|
| React 18 + Vite | SPA framework with HMR dev server |
| Tailwind CSS | Custom design system with dark mode & glassmorphism |
| React-Leaflet | Interactive satellite map with image overlays |
| Axios | HTTP client for REST API calls |

### ⚙️ Backend API (`/server`)
| Tech | Purpose |
|------|---------|
| FastAPI | High-performance async REST API |
| SQLAlchemy (Async) | ORM for PostgreSQL |
| Rasterio / GDAL | GeoTIFF parsing, CRS reprojection, thumbnail generation |
| Pydantic v2 | Request/response validation and serialization |
| MinIO SDK | S3-compatible object storage client |

### 🧠 Machine Learning
| Tech | Purpose |
|------|---------|
| PyTorch | SRCNN model training and inference |
| NumPy | Band data manipulation and normalization |
| Rasterio | Tiled read/write of massive GeoTIFFs |

### 🗄️ Infrastructure
| Service | Image | Port |
|---------|-------|------|
| PostgreSQL + PostGIS | `postgis/postgis:15-3.3` | `5433` |
| Redis | `redis:alpine` | `6379` |
| MinIO | `quay.io/minio/minio:latest` | `9000`, `9001` |
| Ollama | `ollama/ollama:latest` | `11434` |
| FastAPI Backend | `./server` (custom build) | `8000` |
| Celery Worker | `./server` (custom build) | — |

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker Compose)
- NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) *(optional, but strongly recommended for fast inference)*

### 1. Clone & Start

```bash
git clone https://github.com/Pratik-kr21/GeoSR-AI.git
cd GeoSR-AI
docker-compose up -d --build
```

This starts all 6 services. Wait ~30 seconds for them to become healthy.

### 2. Initialize the Database & Storage

```bash
# Create DB tables and MinIO buckets
docker-compose exec backend python seed_dataset.py
```

### 3. (Optional) Create a Sample Test File

If you don't have a Sentinel-2 GeoTIFF, generate a synthetic test tile:

```bash
docker-compose exec backend python create_center_test.py
```

This creates `server/data/center_test.tif` — a 1024×1024 synthetic 4-band GeoTIFF.

### 4. (Optional) Train the Model

```bash
# Generate paired training tiles from a raw GeoTIFF
docker-compose exec backend python generate_dataset.py

# Train the SRCNN model (saves weights to /app/weights/srcnn_weights.pth)
docker-compose exec backend python train.py
```

### 5. Open the App

| Service | URL | Credentials |
|---------|-----|-------------|
| 🌐 Web App | http://localhost:5173 | — |
| 📡 API Docs (Swagger) | http://localhost:8000/docs | — |
| 🗄️ MinIO Console | http://localhost:9001 | `minioadmin` / `minioadmin` |

---

## 🌐 Usage Guide

### Uploading & Enhancing

1. Open **http://localhost:5173** and click **Get Started**
2. On the **Dashboard**, click **Upload GeoTIFF** and select your `.tif` file
3. The file is uploaded to MinIO under `projects/1/inputs/`
4. Click **Run Enhancement** — this enqueues a Celery job
5. The **Processing Pipeline** panel on the right tracks progress:
   - Upload GeoTIFF ✓
   - Geo Preprocessing ✓
   - Band Alignment ✓
   - Super Resolution ✓ *(SRCNN inference runs here)*
   - Geo-Consistency Check ✓
   - Validation ✓

### Viewing Results on Map

Once enhanced:
- The original (blurred, 10m) and enhanced (sharp, 2.5m) layers appear on the Leaflet map
- Use the **Layer Toggles** below the map to show/hide each layer
- The map auto-flies to the image bounds

### Validation Metrics

Navigate to **Validation** in the left sidebar to view:
- **PSNR** (Peak Signal-to-Noise Ratio) in dB — higher is better
- **SSIM** (Structural Similarity Index) — 0 to 1, closer to 1 is better
- **Geo-Consistency** — measures spatial alignment with input CRS
- **Avg Confidence** — mean model confidence across all pixels
- **Edge Accuracy** — sharpness of enhanced edge features

### Uncertainty Map

Navigate to **Uncertainty** to view a heatmap showing pixel-level confidence. Red = low confidence (clouds, shadow edges), blue = high confidence.

### GeoAssist (Offline AI)

Navigate to **GeoAssist** and ask questions like:
- *"Explain my PSNR score"*
- *"What does low geo-consistency mean?"*
- *"Analyze uncertainty hotspots"*

The AI runs locally via Ollama — **no data leaves your machine**.

### Exporting Results

Click **Export** on the Dashboard to download:
- `enhanced_<filename>.jpg` — the enhanced output as a JPEG
- `validation_report.json` — full metrics in JSON format

---

## 📡 API Reference

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/projects/` | List all projects |
| `POST` | `/projects/` | Create a new project |
| `GET` | `/projects/{id}` | Get a project by ID |
| `POST` | `/upload/{project_id}` | Upload a GeoTIFF to MinIO |
| `POST` | `/super-resolution/{project_id}/enhance` | Trigger SR Celery job |
| `GET` | `/super-resolution/jobs/{job_id}/status` | Poll job status |
| `GET` | `/map/{project_id}/outputs/{filename}/thumbnail` | Fetch enhanced thumbnail (PNG) |
| `GET` | `/map/{project_id}/inputs/{filename}/thumbnail` | Fetch original thumbnail (PNG) |
| `GET` | `/map/{project_id}/outputs/{filename}/bounds` | Get geographic bounds |
| `GET` | `/validation/{project_id}/metrics` | Get all quality metrics |
| `POST` | `/assistant/{project_id}/query` | Query GeoAssist LLM |

Full interactive Swagger docs at: **http://localhost:8000/docs**

---

## 📁 Project Structure

```
GeoSR-AI/
├── client/                    # React frontend (Vite)
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.tsx          # Main upload + map viewer
│       │   ├── ValidationPage.tsx     # Metrics + image comparison
│       │   ├── UncertaintyPage.tsx    # Confidence heatmap
│       │   ├── GeoAssistPage.tsx      # Offline LLM chat
│       │   ├── ProjectsPage.tsx       # Project management
│       │   └── LandingPage.tsx        # Marketing landing page
│       ├── components/
│       │   ├── MapViewer.tsx          # React-Leaflet map
│       │   ├── Sidebar.tsx            # Navigation sidebar
│       │   └── ExportModal.tsx        # Download modal
│       └── services/
│           └── api.ts                 # Axios API client
│
└── server/                    # FastAPI backend
    ├── app/
    │   ├── api/                       # REST route handlers
    │   │   ├── projects.py
    │   │   ├── upload.py
    │   │   ├── super_resolution.py
    │   │   ├── map.py
    │   │   ├── validation.py
    │   │   └── assistant.py
    │   ├── services/                  # Business logic
    │   │   ├── inference_service.py   # PyTorch SRCNN runner
    │   │   ├── raster_service.py      # GDAL/Rasterio tools
    │   │   ├── storage_service.py     # MinIO client
    │   │   └── ollama_service.py      # LLM proxy
    │   ├── workers/
    │   │   ├── celery_app.py          # Celery instance
    │   │   └── tasks.py               # Background job definitions
    │   ├── ml/
    │   │   └── model.py               # SRCNN PyTorch architecture
    │   └── models.py                  # SQLAlchemy DB models
    ├── generate_dataset.py            # Training data generator
    ├── train.py                       # Model training script
    ├── create_center_test.py          # Synthetic test tile creator
    └── seed_dataset.py                # DB + MinIO initializer
```

---

## 🔧 Configuration

All backend environment variables are set in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_SERVER` | `db` | PostgreSQL hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `REDIS_HOST` | `redis` | Redis hostname |
| `MINIO_ENDPOINT` | `minio:9000` | MinIO hostname:port |
| `OLLAMA_URL` | `http://ollama:11434` | Ollama API base URL |

GPU support is enabled by default in `docker-compose.yml` via the `deploy.resources.reservations.devices` block. If no GPU is available, the Celery worker and Ollama will automatically fall back to CPU.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run the TypeScript check: `cd client && npx tsc --noEmit`
5. Commit and push: `git push origin feature/my-feature`
6. Open a Pull Request

---

## 📜 License

This project was developed for the **Smart India Hackathon (SIH)** and is open-source for educational and research purposes.

---

<div align="center">
Made with ❤️ for Smart India Hackathon
</div>
