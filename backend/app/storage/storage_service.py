"""Storage service abstraction for local and Azure storage"""
import os
import shutil
from pathlib import Path
from typing import Optional, BinaryIO, List
from datetime import datetime
from io import BytesIO

from app.config import settings
from app.storage.azure_blob import get_azure_storage, AzureBlobStorage
from app.storage.fs import ensure_dir


class StorageService:
    """Unified storage service that works with both local and Azure storage"""

    def __init__(self):
        self.mode = settings.storage_mode
        self.local_dir = settings.data_dir
        self.azure_storage: Optional[AzureBlobStorage] = None

        if self.mode == "azure":
            self.azure_storage = get_azure_storage()
        else:
            ensure_dir(self.local_dir)

    def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        subfolder: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Upload a file to storage

        Args:
            file_data: File-like object
            filename: Name of the file
            subfolder: Optional subfolder path
            metadata: Optional metadata

        Returns:
            Upload information dictionary
        """
        blob_name = f"{subfolder}/{filename}" if subfolder else filename

        if self.mode == "azure":
            return self.azure_storage.upload_file(
                file_data=file_data,
                blob_name=blob_name,
                overwrite=True,
                metadata=metadata
            )
        else:
            # Local storage
            file_path = os.path.join(self.local_dir, blob_name)
            ensure_dir(os.path.dirname(file_path))

            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file_data, f)

            file_stat = os.stat(file_path)
            return {
                "blob_name": blob_name,
                "size": file_stat.st_size,
                "last_modified": datetime.fromtimestamp(file_stat.st_mtime),
                "content_type": "application/octet-stream",
                "url": file_path
            }

    def download_file(self, filename: str, subfolder: Optional[str] = None) -> bytes:
        """
        Download a file from storage

        Args:
            filename: Name of the file
            subfolder: Optional subfolder path

        Returns:
            File content as bytes
        """
        blob_name = f"{subfolder}/{filename}" if subfolder else filename

        if self.mode == "azure":
            return self.azure_storage.download_file(blob_name)
        else:
            file_path = os.path.join(self.local_dir, blob_name)
            with open(file_path, 'rb') as f:
                return f.read()

    def download_file_stream(self, filename: str, subfolder: Optional[str] = None) -> BytesIO:
        """
        Download a file as a stream

        Args:
            filename: Name of the file
            subfolder: Optional subfolder path

        Returns:
            BytesIO stream
        """
        content = self.download_file(filename, subfolder)
        return BytesIO(content)

    def list_files(self, subfolder: Optional[str] = None) -> List[dict]:
        """
        List all files in storage

        Args:
            subfolder: Optional subfolder to filter

        Returns:
            List of file information dictionaries
        """
        if self.mode == "azure":
            return self.azure_storage.list_files(prefix=subfolder)
        else:
            search_dir = os.path.join(self.local_dir, subfolder) if subfolder else self.local_dir
            files = []

            if os.path.exists(search_dir):
                for root, _, filenames in os.walk(search_dir):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(file_path, self.local_dir)
                        file_stat = os.stat(file_path)

                        files.append({
                            "name": rel_path.replace("\\", "/"),
                            "size": file_stat.st_size,
                            "last_modified": datetime.fromtimestamp(file_stat.st_mtime),
                            "content_type": "application/octet-stream",
                            "metadata": {}
                        })

            return files

    def file_exists(self, filename: str, subfolder: Optional[str] = None) -> bool:
        """
        Check if a file exists

        Args:
            filename: Name of the file
            subfolder: Optional subfolder path

        Returns:
            True if file exists
        """
        blob_name = f"{subfolder}/{filename}" if subfolder else filename

        if self.mode == "azure":
            return self.azure_storage.file_exists(blob_name)
        else:
            file_path = os.path.join(self.local_dir, blob_name)
            return os.path.exists(file_path)

    def delete_file(self, filename: str, subfolder: Optional[str] = None) -> bool:
        """
        Delete a file from storage

        Args:
            filename: Name of the file
            subfolder: Optional subfolder path

        Returns:
            True if deleted successfully
        """
        blob_name = f"{subfolder}/{filename}" if subfolder else filename

        if self.mode == "azure":
            return self.azure_storage.delete_file(blob_name)
        else:
            file_path = os.path.join(self.local_dir, blob_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False

    def get_file_metadata(self, filename: str, subfolder: Optional[str] = None) -> dict:
        """
        Get file metadata

        Args:
            filename: Name of the file
            subfolder: Optional subfolder path

        Returns:
            File metadata dictionary
        """
        blob_name = f"{subfolder}/{filename}" if subfolder else filename

        if self.mode == "azure":
            return self.azure_storage.get_file_metadata(blob_name)
        else:
            file_path = os.path.join(self.local_dir, blob_name)
            if os.path.exists(file_path):
                file_stat = os.stat(file_path)
                return {
                    "name": blob_name,
                    "size": file_stat.st_size,
                    "last_modified": datetime.fromtimestamp(file_stat.st_mtime),
                    "content_type": "application/octet-stream",
                    "metadata": {},
                    "etag": None
                }
            raise FileNotFoundError(f"File not found: {blob_name}")


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create StorageService singleton instance"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
