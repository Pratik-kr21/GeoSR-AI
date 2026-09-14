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

storage_service = StorageService()
