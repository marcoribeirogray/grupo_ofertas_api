from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(..., alias="DATABASE_URL")
    api_secret_key: str = Field("change-me", alias="API_SECRET_KEY")
    default_timezone: str = Field("America/Sao_Paulo", alias="DEFAULT_TIMEZONE")

    default_amazon_tag: str | None = Field(None, alias="DEFAULT_AMAZON_TAG")
    default_ml_app_id: str | None = Field(None, alias="DEFAULT_ML_APP_ID")
    default_ml_secret: str | None = Field(None, alias="DEFAULT_ML_SECRET")
    default_awin_source_id: str | None = Field(None, alias="DEFAULT_AWIN_SOURCE_ID")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
