from pydantic_settings import BaseSettings
from typing import Optional, Literal

class Settings(BaseSettings):
    data_dir: str = "./data/seed"
    model_path: str = "./artifacts/model.pt"
    db_url: Optional[str] = None
    redis_url: Optional[str] = None

    # Azure Storage Configuration
    storage_mode: Literal["local", "azure"] = "local"
    azure_storage_connection_string: Optional[str] = None
    azure_storage_container_name: str = "datasets"
    azure_storage_account_name: Optional[str] = None
    azure_storage_account_key: Optional[str] = None

    # Upload Configuration
    max_upload_size_mb: int = 50
    allowed_file_extensions: list[str] = [".csv", ".xlsx"]

    class Config:
        env_file = ".env"

settings = Settings()
