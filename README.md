# 🛰️ GeoSR-AI — GeoIntelligence Decision Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-SRCNN-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![SIH](https://img.shields.io/badge/Smart_India-Hackathon-FF6B35?style=for-the-badge)

**A full-stack AI platform for satellite intelligence. Combines deep learning super-resolution (10m → 2.5m) with multi-layered spectral analytics, change detection, anomaly identification, and a GeoRisk decision indicator.**

[Features](#-key-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API Docs](#-api-reference) • [Usage](#-usage-guide)

</div>

---

## 🔭 Overview

**GeoSR-AI** is a production-grade **GeoIntelligence Decision Platform** built for the **Smart India Hackathon (SIH)**. 

Originally an enhancement tool, the platform applies PyTorch-based **Super-Resolution (SRCNN)** to upscale Sentinel-2 satellite GeoTIFFs from 10m to 2.5m/pixel. It now additionally features a multi-layered analytical engine that computes **Spectral Indices (NDVI/NDWI)**, detects **Temporal Changes**, highlights **Statistical Anomalies**, and calculates a weighted **GeoRisk Index** incorporating live weather data. 

The system leverages a modern tech stack to handle **multi-gigabyte GeoTIFFs** efficiently through tiled streaming inference and integrates a **Tool-Augmented Offline LLM (Ollama)** to help users interpret the vast amount of generated intelligence.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🧠 **Global Residual SRCNN** | Processes massive GeoTIFFs tile-by-tile using PyTorch SRCNN with global residual connections (bicubic skip) for vastly sharper edges without OOM errors. |
| 📊 **Multi-Layered Intelligence** | Computes NDVI (Vegetation) and NDWI (Water) indices, tracks temporal observation timelines, and identifies statistical anomalies using original Sentinel-2 data. |
| ⇌ **Temporal Change Detection** | Compares observations at pixel level to detect critical spectral shifts, outputting quantitative change metrics and hotspots. |
| ⚠ **GeoRisk Assessment** | Calculates a holistic prototype risk index combining vegetation stress, water stress, anomaly density, and Open-Meteo weather indicators. |
| 🤖 **Tool-Augmented GeoAssist** | Conversational AI powered by **Ollama** that dynamically fetches real database analytics to interpret satellite anomalies and validation metrics natively. |
| 🗺️ **Interactive Map Viewer** | React-Leaflet integration with server-side CRS reprojection, percentile-normalized thumbnails, and live analytical heatmap overlays. |
| 📦 **Instant ZIP Exports** | Generates sub-second packaged exports containing enhanced GeoTIFFs, metadata, and mock confidence maps for downstream integration. |
| 🌡️ **Quantitative Validation** | Auto-calculates PSNR, SSIM, Geo-Consistency, and generates pixel-level uncertainty heatmaps for model outputs. |
| 📁 **Project Management** | Full CRUD lifecycle for projects and observations. Data stored securely in PostgreSQL and S3-compatible MinIO. |
| 🐳 **Fully Dockerized** | One `docker-compose up` starts every service: DB, Redis, MinIO, Ollama, Backend, and Worker. |

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (React + Vite)                   │
│   Dashboard → Intelligence → Risk → Change Detection → GeoAssist│
│                    React-Leaflet Map Viewer                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (Axios)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                        │
│   /projects  /upload  /super-resolution  /map  /validation      │
│   /intelligence  /risk  /change-detection  /anomalies           │
│              /assistant (Tool-Augmented Ollama)                 │
└──────┬────────────────────────────────────────┬─────────────────┘
       │                                        │
       ▼                                        ▼
┌─────────────┐   Job Queue (Redis)   ┌────────────────────────┐
│  PostgreSQL │ ◄──────────────────── │   Celery ML Worker     │
│  (Projects, │                       │   PyTorch SRCNN        │
│ Analytics)  │ ──────────────────── ►│   Tiled Inference      │
└─────────────┘                       └───────────┬────────────┘
                                                   │ read/write
                                                   ▼
┌──────────────────────────────────────────────────────────────┐
│             MinIO Object Storage (S3-Compatible)             │
│   projects/1/inputs/<uuid>_file.tif                          │
│   projects/1/outputs/sr_<uuid>_file.tif                      │
└──────────────────────────────────────────────────────────────┘
```

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
| SQLAlchemy (Async) | ORM for PostgreSQL & Alembic Migrations |
| Rasterio / GDAL | GeoTIFF parsing, CRS reprojection, thumbnail generation |
| Pydantic v2 | Request/response validation and serialization |
| MinIO SDK | S3-compatible object storage client |

### 🧠 Machine Learning & Analytics
| Tech | Purpose |
|------|---------|
| PyTorch | SRCNN model training and inference |
| NumPy | High-speed analytical matrix operations (NDVI, NDWI, Z-scores) |
| Rasterio | Tiled read/write of massive GeoTIFFs |
| Ollama | Local LLM inference augmented with database tools |

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) *(optional, but recommended)*

### 1. Clone & Start

```bash
git clone https://github.com/Pratik-kr21/GeoSR-AI.git
cd GeoSR-AI
docker-compose up -d --build
```
Wait ~30 seconds for all services to become healthy.

### 2. Initialize the Database & Storage

```bash
# Run Alembic migrations to build schemas
docker-compose exec backend alembic upgrade head

# Seed initial projects and MinIO buckets
docker-compose exec backend python seed_dataset.py
```

### 3. Open the App

| Service | URL | Credentials |
|---------|-----|-------------|
| 🌐 Web App | http://localhost:5173 | — |
| 📡 API Docs | http://localhost:8000/docs | — |
| 🗄️ MinIO | http://localhost:9001 | `minioadmin` / `minioadmin` |

---

## 🌐 Usage Guide

### 1. Uploading & Enhancing
1. On the **Dashboard**, click **Upload GeoTIFF** and select your Sentinel-2 `.tif` file.
2. Click **Run Enhancement** to trigger the PyTorch SRCNN Celery job.
3. The original (10m) and enhanced (2.5m) layers will appear on the Leaflet map.

### 2. GeoIntelligence Analytics
- Navigate to the **Intelligence** page and click **Run Intelligence Analysis**.
- View **NDVI**, **NDWI**, **Change Metrics**, and a breakdown of **Anomaly Zones**.
- The analysis utilizes the original 10m Sentinel-2 bands to ensure scientific accuracy, completely separated from the SRCNN outputs.

### 3. Risk Assessment
- Go to **Risk Analysis** to see the unified **GeoRisk Index**.
- This index scores out of 100 based on vegetation stress, temporal changes, anomalies, and live **Open-Meteo weather data**.

### 4. Temporal Intelligence
- Use **Change Detection** to contrast two different MinIO objects, surfacing critical spectral shifts and hotspots.
- Use **Timeline** to view historical spectral index records across analysis runs via Sparkline charts.

### 5. Tool-Augmented GeoAssist
Navigate to **GeoAssist** and ask complex questions like:
- *"Why is the GeoRisk score high today?"*
- *"Explain the current satellite analysis and vegetation anomalies."*
- *"What does the validation PSNR score indicate about the AI enhancement?"*

The AI runs locally via Ollama, using provided Python tools to read real database metrics before answering.

---

## 📡 API Reference

Base URL: `http://localhost:8000/api/v1`

| Module | Endpoints |
|--------|-----------|
| **Projects & Files** | `GET /projects/`, `POST /projects/`, `POST /upload/{id}` |
| **Super-Resolution** | `POST /super-resolution/{id}/enhance`, `GET /jobs/{id}/status` |
| **Intelligence** | `POST /intelligence/{id}/analyze`, `GET /intelligence/{id}/summary` |
| **Change Detection** | `POST /change-detection/{id}`, `GET /change-detection/{id}` |
| **GeoRisk & Anomalies**| `GET /risk/{id}`, `GET /anomalies/{id}` |
| **Map & Visuals** | `GET /map/{id}/.../thumbnail`, `GET /map/{id}/ndvi-heatmap` |
| **GeoAssist LLM** | `POST /assistant/{id}/query` |

Full interactive Swagger docs at: **http://localhost:8000/docs**

---

## 📁 Project Structure

```text
GeoSR-AI/
├── client/src/
│   ├── pages/
│   │   ├── Dashboard.tsx          # Upload + Map + Intel Summary
│   │   ├── IntelligencePage.tsx   # NDVI, NDWI, Anomalies
│   │   ├── RiskAnalysisPage.tsx   # GeoRisk gauge + weather
│   │   ├── ChangeDetectionPage.tsx# Temporal difference analysis
│   │   ├── TimelinePage.tsx       # Historical sparklines
│   │   ├── GeoAssistPage.tsx      # Tool-augmented LLM chat
│   │   └── ValidationPage.tsx     # PSNR/SSIM metrics
│   └── components/MapViewer.tsx   # React-Leaflet with dynamic layers
│
└── server/app/
    ├── api/                       # FastAPI route handlers (intelligence, risk, assistant)
    ├── services/
    │   ├── inference_service.py   # PyTorch SRCNN runner
    │   ├── spectral_service.py    # NDVI/NDWI computations
    │   ├── risk_service.py        # GeoRisk weighting & Open-Meteo
    │   ├── anomaly_service.py     # Statistical stress detection
    │   ├── change_service.py      # Temporal comparisons
    │   └── ollama_service.py      # Tool-augmented LLM integration
    ├── workers/                   # Celery queue and background tasks
    └── models.py                  # PostgreSQL DB Schema definitions
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/intelligence-update`
3. Make your changes and run `npx tsc --noEmit` in `/client`
4. Commit and push: `git push origin feature/intelligence-update`
5. Open a Pull Request

---

## 📜 License

Developed for the **Smart India Hackathon (SIH)**. Open-source for educational and research purposes.

---

<div align="center">
Made with ❤️ for Smart India Hackathon
</div>
