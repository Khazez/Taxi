from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import uuid


client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)

BUCKET_NAME = "driver-docs"


def ensure_bucket():
    """Создаёт bucket если не существует."""
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)


def upload_file(file_data: bytes, filename: str, content_type: str) -> str:
    """Загружает файл в MinIO и возвращает ссылку."""
    ensure_bucket()
    unique_name = f"{uuid.uuid4()}_{filename}"
    
    import io
    client.put_object(
        BUCKET_NAME,
        unique_name,
        io.BytesIO(file_data),
        length=len(file_data),
        content_type=content_type,
    )
    return f"http://{settings.MINIO_ENDPOINT}/{BUCKET_NAME}/{unique_name}"