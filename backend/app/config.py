from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://msp_user:msp_password@localhost:5432/msp_registry"
    sync_database_url: str = "postgresql://msp_user:msp_password@localhost:5432/msp_registry"
    upload_dir: str = "/app/uploads"

    class Config:
        env_file = ".env"


settings = Settings()
