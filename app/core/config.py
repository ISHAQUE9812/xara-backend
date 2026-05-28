from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # MongoDB connection string (use MONGODB_URL env var)
    MONGODB_URL: str = "mongodb://localhost:27017"
    # Database name (required for Motor client)
    DATABASE_NAME: str = "xara_db"
    # JWT configuration
    JWT_SECRET: str = "your_secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3000

    @property
    def SECRET_KEY(self) -> str:
        return self.JWT_SECRET

    @property
    def ALGORITHM(self) -> str:
        return self.JWT_ALGORITHM

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
