import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "GeoSR-AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "geosrai")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "geosrai")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5433")
    
    @property
    def DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # Ollama
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "geosrai-data")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    # Ollama
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")

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
