# 🛰️ GeoSR-AI — Advanced GeoIntelligence Decision Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-SRCNN-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Google Earth Engine](https://img.shields.io/badge/Google_Earth_Engine-Integration-34A853?style=for-the-badge&logo=google&logoColor=white)

**A full-stack, multi-sensor AI platform for satellite intelligence. Combines deep learning super-resolution (10m → 2.5m) with Sentinel-1 SAR, Copernicus DEM, Google Earth Engine Historical Analysis, and live real-time Sentinel-2 fetching via the Copernicus Sentinel Hub (CDSE).**

[Features](#-key-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API Docs](#-api-reference) • [Usage](#-usage-guide)

</div>

---

## 🔭 Overview

**GeoSR-AI** is a production-grade **GeoIntelligence Decision Platform** built for the **Smart India Hackathon (SIH)**. 

Originally an image enhancement tool, the platform applies PyTorch-based **Super-Resolution (SRCNN)** to upscale Sentinel-2 satellite GeoTIFFs from 10m to 2.5m/pixel. It has now evolved into a massive multi-sensor analytical engine that fetches **Sentinel-1 (SAR)**, **Copernicus DEM (Terrain)**, and generates **Google Earth Engine Cloud-Free Composites**. 

The system leverages a modern tech stack to handle **multi-gigabyte GeoTIFFs** efficiently through tiled streaming inference, executes heavy workloads asynchronously using **Celery & Redis**, and provides deep historical insights through **Landsat multi-decadal time-series analysis**.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🧠 **Global Residual SRCNN** | Processes massive Sentinel-2 GeoTIFFs tile-by-tile using PyTorch SRCNN with global residual connections (bicubic skip) for vastly sharper edges (10m to 2.5m). |
| 🛰️ **Live Multi-Sensor Fetching**| Instantly crop and download live Sentinel-2 (Optical), Sentinel-1 (SAR), and Copernicus DEM imagery for any drawn coordinate using the **Copernicus Process API (CDSE)**. |
| 🌍 **Google Earth Engine Integration** | Automatically generate highly accurate **Cloud-Free Composites** using GEE's HARMONIZED datasets to bypass weather interference. |
| 🕰️ **Multi-Decadal Historical Analysis** | Query Landsat datasets via GEE to instantly map historical NDVI distributions across 30+ years (1990-2023) for long-term climate tracking. |
| 📊 **Multi-Sensor Statistics Export** | Automatically fuses NDVI (Vegetation), SAR Backscatter (Moisture/Texture), and DEM Elevation data into a unified, downloadable CSV export. |
| ⚠ **Multi-Modal GeoRisk** | Calculates a holistic prototype risk index combining vegetation, water, flood terrain risk, slope instability, and **live Open-Meteo weather data**. |
| 🗺️ **Interactive Map Viewer** | React-Leaflet integration with custom drawing tools (Bounding Box/AOI), synchronized coordinates, server-side CRS reprojection, and sharp image overlays. |
| 🌡️ **Quantitative Validation** | Auto-calculates PSNR, SSIM, Geo-Consistency, and generates pixel-level uncertainty metrics for model outputs. |
| 📁 **Project Management** | Full CRUD lifecycle for projects and observations. Data stored securely in PostgreSQL and S3-compatible **MinIO**. |
| 🐳 **Fully Dockerized** | One `docker-compose up` starts every service: DB, Redis, MinIO, FastAPI Backend, and Celery ML Worker. |

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (React + Vite)                   │
│      Dashboard → Historical Comparison → Multi-Sensor Export    │
│            React-Leaflet Map Viewer & Area Draw Tools           │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (Axios)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                        │
│   /projects  /upload  /super-resolution  /map  /validation      │
│   /realtime/fetch-sar   /fetch-dem   /fetch-cloudfree           │
└──────┬────────────────────────────────────────┬─────────────────┘
       │                                        │
       ▼                                        ▼
┌─────────────┐   Job Queue (Redis)   ┌────────────────────────┐
│  PostgreSQL │ ◄──────────────────── │   Celery ML Worker     │
│  (Projects, │                       │   PyTorch SRCNN,       │
│ Analytics)  │ ──────────────────── ►│   GEE Python API, CDSE │
└─────────────┘                       └───────────┬────────────┘
                                                   │ read/write
                                                   ▼
┌──────────────────────────────────────────────────────────────┐
│             MinIO Object Storage (S3-Compatible)             │
│   projects/1/inputs/sar_uuid.tif                             │
│   projects/1/inputs/realtime_uuid.tif                        │
│   projects/1/outputs/sr_realtime_uuid.tif                    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Technology Stack

### 🎨 Frontend (`/client`)
| Tech | Purpose |
|------|---------|
| **React 18 + Vite** | SPA framework with HMR dev server |
| **Tailwind CSS** | Custom design system with dark mode & glassmorphism |
| **React-Leaflet** | Interactive satellite map with image overlays & BBox Draw controls |
| **Axios** | HTTP client for REST API calls |

### ⚙️ Backend API (`/server`)
| Tech | Purpose |
|------|---------|
| **FastAPI** | High-performance async REST API |
| **SQLAlchemy (Async)** | ORM for PostgreSQL & Alembic Migrations |
| **Celery + Redis** | Background job queueing for heavy ML and API fetching |
| **Rasterio / GDAL** | GeoTIFF parsing, CRS reprojection, and bounds extraction |
| **MinIO SDK** | S3-compatible object storage client |

### 🧠 Machine Learning, Earth Engine, & Analytics
| Tech | Purpose |
|------|---------|
| **PyTorch** | SRCNN model inference for super-resolving Sentinel-2 imagery |
| **Google Earth Engine (earthengine-api)** | Cloud-masked composite generation and historical Landsat analysis |
| **Sentinel Hub (oauthlib)** | OAuth2 authentication and OData API interaction for CDSE |
| **NumPy** | High-speed analytical matrix operations (NDVI, Backscatter, Slope calculations) |

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Access to **Copernicus Data Space Ecosystem (CDSE)** credentials (added to `.env`)
- Access to **Google Earth Engine** service account credentials (`gee-key.json` added to backend config)

### 1. Clone & Configure

```bash
git clone https://github.com/Pratik-kr21/GeoSR-AI.git
cd GeoSR-AI
```
Create a `.env` file in the root directory following the format in `.env.example`. Be sure to insert your CDSE client ID/secret.

### 2. Start Services

```bash
docker-compose up -d --build
```
Wait ~30 seconds for all services to become healthy.

### 3. Initialize the Database & Storage

```bash
# Run Alembic migrations to build schemas
docker-compose exec backend alembic upgrade head

# Seed initial projects and MinIO buckets
docker-compose exec backend python seed_dataset.py
```

### 4. Open the App

| Service | URL | Credentials |
|---------|-----|-------------|
| 🌐 Web App | http://localhost:5173 | — |
| 📡 API Docs | http://localhost:8000/docs | — |
| 🗄️ MinIO | http://localhost:9001 | `minioadmin` / `minioadmin` |

---

## 🌐 Usage Guide

### 1. Live Fetching & Bounding Box (AOI) Draw
1. On the **Dashboard**, use the map's **Rectangle Draw Tool** to select an Area of Interest (AOI). The exact center coordinates will be instantly saved in the background.
2. Click the **🛰 Fetch Realtime** button to open the live data panel.
3. Select your desired sensor:
   - **Sentinel-2 (Optical)**
   - **Sentinel-1 (SAR)**
   - **Copernicus DEM (Terrain)**
   - **Cloud-Masked Composite (GEE)**
4. Click **Fetch Imagery**. The backend will instantly crop, download, and render the GeoTIFF tightly within your drawn bounding box.

### 2. Super-Resolution Enhancement
1. After fetching **Sentinel-2** imagery, click **Run Enhancement**.
2. A background Celery job will spin up, process the multi-gigabyte TIFF through the PyTorch SRCNN model in overlapping tiles, and dynamically overlay the sharpened 2.5m resolution output on top of the map.

### 3. Multi-Sensor Data Export
1. On the **Dashboard**, click **Export** to access the Multi-Sensor Data Hub.
2. Click **Generate Unified Export**. The backend merges calculated NDVI (Sentinel-2), SAR Backscatter (Sentinel-1), and Elevation Stats (DEM) into a singular CSV report.

### 4. Historical Comparison (Landsat Multi-Decadal)
1. After drawing your AOI on the Dashboard, navigate to the **Historical Comparison** page.
2. The coordinates of your AOI will be **automatically populated**.
3. Select target decades (e.g., 1990, 2000, 2023) and click **Run Historical Analysis**.
4. The system queries Google Earth Engine's Landsat archives and plots long-term vegetation (NDVI) shifts in a dynamic chart.

---

## 📡 API Reference

Base URL: `http://localhost:8000/api/v1`

| Module | Endpoints |
|--------|-----------|
| **Projects** | `GET /projects/`, `POST /projects/` |
| **Realtime Data (CDSE & GEE)**| `POST /realtime/fetch-and-process/{id}`, `POST /realtime/fetch-sar/{id}`, `POST /realtime/fetch-dem/{id}`, `POST /realtime/fetch-cloudfree/{id}` |
| **Historical & Intelligence** | `POST /realtime/historical-analysis/{id}`, `POST /intelligence/{id}/analyze` |
| **GeoRisk**| `GET /risk/{id}` |
| **Map visual layers** | `GET /map/{id}/inputs/{file_id}/thumbnail`, `GET /map/{id}/inputs/{file_id}/bounds` |
| **Data Export** | `POST /export/multi-sensor/{id}`, `GET /export/download/{id}` |

Full interactive Swagger docs at: **http://localhost:8000/docs**

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/awesome-feature`
3. Make your changes and run `npx tsc --noEmit` in `/client`
4. Commit and push: `git push origin feature/awesome-feature`
5. Open a Pull Request

---

## 📜 License

Developed for the **Smart India Hackathon (SIH)**. Open-source for educational and research purposes.

---

<div align="center">
Made with ❤️ for Smart India Hackathon
</div>
