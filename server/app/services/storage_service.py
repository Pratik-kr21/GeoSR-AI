from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timezone
from app.config import settings

class StorageService:
    def __init__(self):
        self.client = BlobServiceClient(
            account_url=f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
            credential=settings.AZURE_STORAGE_ACCOUNT_KEY
        )
        self.container_name = settings.MINIO_BUCKET_NAME
        self._ensure_container_exists()

    def _ensure_container_exists(self):
        container_client = self.client.get_container_client(self.container_name)
        if not container_client.exists():
            self.client.create_container(self.container_name)

    def upload_file(self, file_path: str, object_name: str):
        """
        Uploads a local file to Azure Blob Storage.
        Returns the object name on success.
        """
        blob_client = self.client.get_blob_client(
            container=self.container_name,
            blob=object_name
        )
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        return object_name

    def download_file(self, object_name: str, file_path: str):
        """
        Downloads a file from Azure Blob Storage to a local path.
        """
        blob_client = self.client.get_blob_client(
            container=self.container_name,
            blob=object_name
        )
        with open(file_path, "wb") as f:
            data = blob_client.download_blob()
            data.readinto(f)
        return file_path

    def get_presigned_url(self, object_name: str, expires_delta=None):
        """
        Generates a presigned SAS URL for downloading a blob directly from Azure.
        """
        from datetime import timedelta
        if expires_delta is None:
            expires_delta = timedelta(hours=1)

        sas_token = generate_blob_sas(
            account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
            container_name=self.container_name,
            blob_name=object_name,
            account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + expires_delta
        )
        url = (
            f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
            f"/{self.container_name}/{object_name}?{sas_token}"
        )
        return url

storage_service = StorageService()
