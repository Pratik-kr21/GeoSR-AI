# GeoSR-AI — Real-Time Satellite Data Setup

This guide explains how to connect GeoSR-AI to live Sentinel-2 satellite imagery
from the **Copernicus Data Space Ecosystem (CDSE)** — the official European Space
Agency platform. Registration and data access are **completely free**.

---

## 1. Register a Free CDSE Account

1. Visit **https://dataspace.copernicus.eu/**
2. Click **Sign up** in the top-right corner.
3. Fill in your email, password, first/last name, and organisation.
4. Verify your email address.

---

## 2. Create an OAuth Client (API Key)

1. Log in and go to your account settings:
   **https://shapps.dataspace.copernicus.eu/dashboard/#/account/settings**
2. In the left sidebar, click **OAuth Clients**.
3. Click **Add Client**.
4. Enter any application name (e.g. `GeoSR-AI Local`).
5. You will be shown a **Client ID** and a **Client Secret** — copy both immediately.
   The Client Secret is only shown once.

---

## 3. Add Credentials to Your `.env` File

At the root of this repository, create a `.env` file (copy `.env.example`):

```bash
cp .env.example .env
```

Then open `.env` and fill in your credentials:

```dotenv
CDSE_CLIENT_ID=your_actual_client_id
CDSE_CLIENT_SECRET=your_actual_client_secret
OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast
```

> ⚠️ **Never commit your `.env` file.** It is in `.gitignore` by default.

---

## 4. Rebuild and Restart the Backend

```bash
# Rebuild to install new Python dependencies (requests, sentinel-images-downloader)
docker-compose build backend worker

# Restart both services with the new environment variables
docker-compose up -d backend worker
```

---

## 5. Test the Integration

### Test weather (no credentials needed)
```bash
curl "http://localhost:8000/api/v1/realtime/check-availability?latitude=28.6&longitude=77.2&days_back=30&max_cloud_cover=20"
```
This should return a JSON response within 3 seconds showing whether a Sentinel-2
scene exists for Delhi and live Open-Meteo weather data.

### Test with Delhi coordinates
```bash
curl -X POST http://localhost:8000/api/v1/realtime/fetch/1 \
  -H "Content-Type: application/json" \
  -d '{"latitude": 28.6139, "longitude": 77.2090, "buffer_km": 5, "days_back": 30, "max_cloud_cover": 20}'
```

### Check the CDSE capability flag
```bash
curl http://localhost:8000/api/v1/realtime/status
```
Expected response when credentials are configured:
```json
{"cdse_enabled": true, "open_meteo_available": true, "message": "Real-time Sentinel-2 fetching is available."}
```

---

## 6. Using the Frontend

1. Open the Dashboard at **http://localhost:5173/**
2. In the top toolbar, click **🛰 Fetch Realtime** to switch modes.
3. Click **Pick Location** and then click anywhere on the map — the coordinates
   will be automatically filled in the panel.
4. Adjust **Search radius**, **Days back**, and **Max cloud %** as needed.
5. Click **Check Availability** first (fast, no download) to confirm a scene exists.
6. Click **Fetch Latest Imagery** to download the raw Sentinel-2 data.
7. Once the raw image is loaded, click **Enhance Imagery (Super-Resolution)** to upscale it and compute indices.

---

## 7. Understanding Sentinel-2 Data Latency

> **Sentinel-2 has a 5-day revisit cycle.** This means that for any given
> location on Earth, a new observation is captured approximately every 5 days.
> The most recent clear-sky image is typically **5–10 days old** — this is the
> freshest data physically possible from this satellite.

There is no workaround for this latency — it is a fundamental property of the
satellite's orbital period. If you need more frequent coverage, ESA's Sentinel-1
(SAR, weather-independent) has a 6-day cycle, and commercial providers like
Planet Labs offer daily imagery (paid).

---

## 8. Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `cdse_not_configured` | `CDSE_CLIENT_ID` / `SECRET` not set | Check `.env` file and restart backend |
| `cdse_auth_failed (401)` | Wrong credentials | Re-copy from CDSE dashboard |
| `no_scene_found` | No clear scene in date range | Increase `days_back` or `max_cloud_cover` |
| `cdse_download_failed` | Network / download error | Check Docker network and retry |
| `storage_failed` | MinIO is down | `docker-compose ps` and restart MinIO |
| Weather shows "unavailable" | Open-Meteo unreachable | Retry; GeoRisk uses neutral 0.0 score |

---

## 9. API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/realtime/status` | GET | Check capability flags |
| `/api/v1/realtime/check-availability` | GET | Fast catalog check, no download |
| `/api/v1/realtime/fetch/{project_id}` | POST | Download + store scene |
| `/api/v1/realtime/latest/{project_id}` | GET | Last fetched observation |
| `/api/v1/realtime/fetch-and-process/{project_id}` | POST | Full pipeline |
