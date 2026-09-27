git add server/app/services/gee_service.py server/app/config.py server/GEE_SETUP.md server/app/services/historical_service.py
git commit -m "feat(backend): integrate Google Earth Engine for cloud-free composites and historical Landsat analysis"

git add server/app/services/sar_service.py
git commit -m "feat(backend): implement Sentinel-1 SAR backscatter processing"

git add server/app/services/terrain_service.py
git commit -m "feat(backend): implement Copernicus DEM elevation and slope extraction"

git add server/app/services/realtime_service.py
git commit -m "fix(backend): fix bounding box parsing and extend CDSE realtime fetching for multiple sensors"

git add server/app/workers/tasks.py
git commit -m "feat(backend): add Celery background tasks for SAR, DEM, and GEE composites"

git add server/app/api/realtime.py server/app/api/export.py server/app/models.py
git commit -m "feat(backend): add realtime API endpoints and multi-sensor CSV export routes"

git add client/src/pages/MultiSensorDataPage.tsx client/src/App.tsx client/src/components/Sidebar.tsx
git commit -m "feat(frontend): create Multi-Sensor Data Export page and update navigation"

git add client/src/pages/HistoricalComparisonPage.tsx
git commit -m "feat(frontend): add Historical Comparison page for multi-decadal NDVI time-series"

git add client/src/components/FetchRealtimePanel.tsx client/src/services/api.ts
git commit -m "feat(frontend): update realtime panel to support Sentinel-1, DEM, and GEE with proper API hooks"

git add client/src/pages/Dashboard.tsx client/src/components/MapViewer.tsx client/src/components/ExportModal.tsx
git commit -m "fix(frontend): sync bounding box area drawing with map coordinates and enhance Dashboard UX"

git add server/requirements.txt .env.example
git commit -m "chore: update dependencies and environment examples for new API keys"

git add README.md
git commit -m "docs: overhaul README with updated architecture, multi-sensor integration, and usage guides"

git add server/app/services/risk_service.py
git commit -m "feat(backend): enhance GeoRisk calculation weights"

git push
