from minio import Minio
from app.config import settings

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def upload_file(self, file_path: str, object_name: str):
        """
        Uploads a local file to MinIO.
        Returns the object name on success.
        """
        self.client.fput_object(
            self.bucket_name,
            object_name,
            file_path,
        )
        return object_name
        
    def download_file(self, object_name: str, file_path: str):
        """
        Downloads a file from MinIO to a local path.
        """
        self.client.fget_object(
            self.bucket_name,
            object_name,
            file_path,
        )
        return file_path

    def get_presigned_url(self, object_name: str, expires_delta=None):
        """
        Generates a presigned URL for downloading an object directly from MinIO.
        """
        from datetime import timedelta
        if expires_delta is None:
            expires_delta = timedelta(hours=1)
        # For localhost deployment, we might need to replace minio:9000 with localhost:9000
        # if the frontend is accessing it from outside the docker network
        url = self.client.presigned_get_object(
            self.bucket_name,
            object_name,
            expires=expires_delta
        )
        
        # Hack for local dev: replace internal docker hostname with localhost
        if "minio:9000" in url:
            url = url.replace("minio:9000", "localhost:9000")
            
        return url

storage_service = StorageService()
