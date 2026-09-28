FROM python:3.11-slim

# Install system dependencies for GDAL/Rasterio and Postgres
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set env vars for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

# Install the new libraries separately so we don't invalidate the 20-minute Docker cache layer above
RUN pip install --default-timeout=1000 requests>=2.31.0 sentinel-images-downloader
# Copy application code
COPY . .

# Make the worker startup script executable and fix Windows line endings
RUN sed -i 's/\r$//' /app/worker-start.sh && chmod +x /app/worker-start.sh

# Make the backend startup script executable and fix Windows line endings
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

# Run migrations then start the application (override with /app/worker-start.sh for the Celery worker)
CMD ["/app/start.sh"]
