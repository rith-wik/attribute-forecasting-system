"""Azure Blob Storage service for dataset management"""
import logging
from typing import Optional, BinaryIO, List
from datetime import datetime, timedelta
from io import BytesIO

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceNotFoundError, AzureError
from azure.identity import DefaultAzureCredential

from app.config import settings

logger = logging.getLogger(__name__)


class AzureBlobStorage:
    """Azure Blob Storage client for dataset files"""

    def __init__(self):
        self.container_name = settings.azure_storage_container_name
        self.blob_service_client = self._get_blob_service_client()
        self._ensure_container_exists()

    def _get_blob_service_client(self) -> BlobServiceClient:
        """Initialize BlobServiceClient with connection string or managed identity"""
        try:
            if settings.azure_storage_connection_string:
                # Use connection string (for development/testing)
                return BlobServiceClient.from_connection_string(
                    settings.azure_storage_connection_string
                )
            elif settings.azure_storage_account_name:
                # Use managed identity (recommended for production)
                account_url = f"https://{settings.azure_storage_account_name}.blob.core.windows.net"
                credential = DefaultAzureCredential()
                return BlobServiceClient(account_url=account_url, credential=credential)
            else:
                raise ValueError(
                    "Azure Storage configuration missing. Provide either "
                    "AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_NAME"
                )
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob Storage client: {e}")
            raise

    def _ensure_container_exists(self):
        """Create container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Created container: {self.container_name}")
        except Exception as e:
            logger.error(f"Failed to ensure container exists: {e}")
            raise

    def upload_file(
        self,
        file_data: BinaryIO,
        blob_name: str,
        overwrite: bool = True,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Upload a file to Azure Blob Storage

        Args:
            file_data: File-like object to upload
            blob_name: Name of the blob (file path in storage)
            overwrite: Whether to overwrite if blob exists
            metadata: Optional metadata to attach to blob

        Returns:
            dict with upload information
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            # Upload the file
            blob_client.upload_blob(
                file_data,
                overwrite=overwrite,
                metadata=metadata or {}
            )

            # Get blob properties
            properties = blob_client.get_blob_properties()

            logger.info(f"Successfully uploaded blob: {blob_name}")
            return {
                "blob_name": blob_name,
                "size": properties.size,
                "last_modified": properties.last_modified,
                "content_type": properties.content_settings.content_type,
                "url": blob_client.url
            }
        except Exception as e:
            logger.error(f"Failed to upload blob {blob_name}: {e}")
            raise

    def download_file(self, blob_name: str) -> bytes:
        """
        Download a file from Azure Blob Storage

        Args:
            blob_name: Name of the blob to download

        Returns:
            File content as bytes
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            download_stream = blob_client.download_blob()
            content = download_stream.readall()

            logger.info(f"Successfully downloaded blob: {blob_name}")
            return content
        except ResourceNotFoundError:
            logger.error(f"Blob not found: {blob_name}")
            raise
        except Exception as e:
            logger.error(f"Failed to download blob {blob_name}: {e}")
            raise

    def download_file_stream(self, blob_name: str) -> BytesIO:
        """
        Download a file as a stream

        Args:
            blob_name: Name of the blob to download

        Returns:
            BytesIO stream
        """
        content = self.download_file(blob_name)
        return BytesIO(content)

    def list_files(self, prefix: Optional[str] = None) -> List[dict]:
        """
        List all files in the container

        Args:
            prefix: Optional prefix to filter blobs

        Returns:
            List of blob information dictionaries
        """
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )

            blobs = []
            for blob in container_client.list_blobs(name_starts_with=prefix):
                blobs.append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None,
                    "metadata": blob.metadata
                })

            logger.info(f"Listed {len(blobs)} blobs with prefix: {prefix}")
            return blobs
        except Exception as e:
            logger.error(f"Failed to list blobs: {e}")
            raise

    def file_exists(self, blob_name: str) -> bool:
        """
        Check if a file exists in storage

        Args:
            blob_name: Name of the blob to check

        Returns:
            True if blob exists, False otherwise
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            return blob_client.exists()
        except Exception as e:
            logger.error(f"Failed to check blob existence {blob_name}: {e}")
            return False

    def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from storage

        Args:
            blob_name: Name of the blob to delete

        Returns:
            True if deleted successfully
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            logger.info(f"Successfully deleted blob: {blob_name}")
            return True
        except ResourceNotFoundError:
            logger.warning(f"Blob not found for deletion: {blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete blob {blob_name}: {e}")
            raise

    def get_file_metadata(self, blob_name: str) -> dict:
        """
        Get metadata for a blob

        Args:
            blob_name: Name of the blob

        Returns:
            Blob properties and metadata
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            properties = blob_client.get_blob_properties()

            return {
                "name": blob_name,
                "size": properties.size,
                "last_modified": properties.last_modified,
                "content_type": properties.content_settings.content_type,
                "metadata": properties.metadata,
                "etag": properties.etag
            }
        except Exception as e:
            logger.error(f"Failed to get blob metadata {blob_name}: {e}")
            raise

    def generate_download_url(self, blob_name: str, expiry_hours: int = 1) -> str:
        """
        Generate a temporary download URL with SAS token

        Args:
            blob_name: Name of the blob
            expiry_hours: Hours until the URL expires

        Returns:
            Temporary download URL
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            # Generate SAS token if using account key
            if settings.azure_storage_account_key:
                sas_token = generate_blob_sas(
                    account_name=settings.azure_storage_account_name,
                    container_name=self.container_name,
                    blob_name=blob_name,
                    account_key=settings.azure_storage_account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
                )
                return f"{blob_client.url}?{sas_token}"
            else:
                # For managed identity, return the direct URL
                return blob_client.url
        except Exception as e:
            logger.error(f"Failed to generate download URL for {blob_name}: {e}")
            raise


# Singleton instance
_azure_storage: Optional[AzureBlobStorage] = None


def get_azure_storage() -> AzureBlobStorage:
    """Get or create Azure Storage singleton instance"""
    global _azure_storage
    if _azure_storage is None:
        _azure_storage = AzureBlobStorage()
    return _azure_storage
