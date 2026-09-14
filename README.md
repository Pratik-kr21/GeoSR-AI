# 🛰️ GeoSR-AI

**GeoSR-AI** is a high-performance, full-stack application designed to upscale and enhance satellite imagery (like Sentinel-2 10m resolution data) using advanced AI Super-Resolution (SRCNN/GANs). 

It is designed to handle massive geospatial datasets (multi-gigabyte GeoTIFFs) efficiently through tiled streaming inference and robust background job processing.

![Dashboard Preview](client/public/favicon.ico) *(Place a screenshot of the dashboard here)*

## ✨ Key Features

- **Tiled ML Inference Engine**: Uses PyTorch to perform super-resolution on massive GeoTIFFs without memory crashes. Images are processed in 1024x1024 chunks and streamed directly to disk.
- **Dynamic Map Integration**: Integrates flawlessly with Leaflet. Server-side thumbnail decimation and automatic CRS reprojection (UTM to WGS84) allow instant preview of 4GB Enhanced TIFFs directly on the web map.
- **Quantitative Validation Dashboard**: Automatically tracks and visualizes scientific quality metrics including PSNR, SSIM, LPIPS, and Spatial Attention (SAM) to validate that the AI reconstruction adheres to ground-truth physics.
- **Uncertainty & Confidence Mapping**: Highlights regions where the AI had low confidence during upscaling (due to clouds, shadows, or edge ambiguity) ensuring analysts know which pixels to trust.
- **Self-Supervised Dataset Generation**: Includes a script to automatically ingest raw European Space Agency (ESA) `.SAFE` datasets or massive GeoTIFFs, and slice them into paired low-res/high-res tiles for custom model training.
- **Scalable Architecture**: Fully containerized using Docker, with asynchronous queues (Celery/Redis) and S3-compatible object storage (MinIO) capable of scaling to petabytes of satellite data.

## 🏗️ Architecture Stack

- **Frontend**: React (Vite), Tailwind CSS, Recharts, React-Leaflet
- **Backend API**: FastAPI, Python 3.10, SQLAlchemy, Rasterio, GDAL
- **Machine Learning**: PyTorch (SRCNN Architecture)
- **Task Queue**: Celery & Redis
- **Database**: PostgreSQL
- **Storage**: MinIO (S3-Compatible Object Storage)

## 🚀 Quick Start

The entire infrastructure (Database, Queues, Storage, Backend, and Frontend) is containerized for a one-click startup.

### 1. Start the System
Ensure you have [Docker](https://www.docker.com/) installed, then run:
```bash
docker-compose up -d --build
```

This will spin up:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- MinIO Console: `http://localhost:9001` (User: `minioadmin`, Pass: `minioadmin`)
- PostgreSQL database
- Redis cache
- Celery ML Worker

### 2. Prepare the Database & MinIO Buckets
Seed the initial database and configure the necessary storage buckets by running:
```bash
docker-compose exec backend python seed_dataset.py
```

### 3. Generate a Training Dataset (Optional)
If you want to train the model from scratch on a raw Sentinel-2 GeoTIFF (`server/data/test_input.tif`), you can slice it into thousands of training pairs:
```bash
docker-compose exec backend python generate_dataset.py
```

### 4. Train the Model (Optional)
Train the PyTorch SRCNN model on the generated dataset:
```bash
docker-compose exec backend python train.py
```

## 🌐 Usage

1. Open `http://localhost:5173` in your browser.
2. Click **Upload GeoTIFF** to upload a raw satellite image.
3. Click **Run Enhancement** to trigger the background ML worker.
4. Watch as the enhanced high-resolution image is overlaid onto the interactive Leaflet map!
5. Navigate to the **Validation** tab on the left sidebar to view the SSIM/PSNR metrics of your AI generation.

---

*Developed for the Smart India Hackathon (SIH).*
