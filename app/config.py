from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    retailcrm_url: str = Field(..., description="URL RetailCRM")
    retailcrm_api_key: str = Field(..., description="API ключ")
    redis_url: str = Field("redis://localhost:6379", description="URL Redis")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
