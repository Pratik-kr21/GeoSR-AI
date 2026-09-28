import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "GeoSR-AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost").strip()
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "geosrai").strip()
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password").strip()
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "geosrai").strip()
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432").strip()
    
    @property
    def DATABASE_URI(self) -> str:
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{encoded_password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost").strip()
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6380").strip())
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "").strip()
    REDIS_SSL: bool = os.getenv("REDIS_SSL", "true").strip().lower() == "true"

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            # Azure Redis requires SSL and password
            return f"rediss://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"



    # Azure Blob Storage (replaces MinIO)
    AZURE_STORAGE_ACCOUNT_NAME: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    AZURE_STORAGE_ACCOUNT_KEY: str = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "geosrai-data")
    

    # ─── CDSE (Copernicus Data Space Ecosystem) ────────────────────────────────
    # Register free at https://dataspace.copernicus.eu/
    # Create an OAuth client at https://shapps.dataspace.copernicus.eu/dashboard/#/account/settings
    # Leave empty to gracefully disable real-time Sentinel-2 fetching.
    CDSE_CLIENT_ID: str = os.getenv("CDSE_CLIENT_ID", "")
    CDSE_CLIENT_SECRET: str = os.getenv("CDSE_CLIENT_SECRET", "")

    @property
    def CDSE_ENABLED(self) -> bool:
        """Real-time Sentinel-2 download is available only when credentials are set."""
        return bool(self.CDSE_CLIENT_ID and self.CDSE_CLIENT_SECRET)

    # ─── Open-Meteo (free, no API key required) ───────────────────────────────
    OPEN_METEO_BASE_URL: str = os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast")

    # ─── Google Earth Engine ────────────────────────────────
    GEE_PROJECT_ID: str = os.getenv("GEE_PROJECT_ID", "")
    GEE_SERVICE_ACCOUNT_EMAIL: str = os.getenv("GEE_SERVICE_ACCOUNT_EMAIL", "")
    GEE_CREDENTIALS_PATH: str = os.getenv("GEE_CREDENTIALS_PATH", "/run/secrets/gee-service-account.json")
    GEE_EXPORT_BUCKET: str = os.getenv("GEE_EXPORT_BUCKET", "")

    class Config:
        case_sensitive = True

settings = Settings()
