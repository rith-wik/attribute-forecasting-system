from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    data_dir: str = "./data/seed"
    model_path: str = "./artifacts/model.pt"
    db_url: Optional[str] = None
    redis_url: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
