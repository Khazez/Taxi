from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET_KEY: str
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-key.json"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()