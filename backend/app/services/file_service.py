import os
import uuid
import magic
import boto3
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

ALLOWED_MIME_TYPES = {
    # PDF
    "application/pdf",
    # Audio
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    # Video
    "video/mp4", "video/quicktime", "video/x-msvideo", "video/avi", "video/x-flv"
}

class FileService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
        # Initialize Boto3 client if Bucket is provided
        self.s3_client = boto3.client('s3') if settings.AWS_BUCKET_NAME else None

    async def validate_and_save_file(self, file: UploadFile) -> dict:
        # 1. Read first file chunk to determine true MIME using magic
        chunk = await file.read(2048)
        mime_type = magic.from_buffer(chunk, mime=True)
        
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {mime_type}"
            )
        
        # Reset file cursor back to the beginning
        await file.seek(0)
        
        # 2. Setup UUID filename and destination path
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        # 3. Stream save the file securely enforcing max size
        file_size = 0
        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024) # 1MB chunks
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > max_size_bytes:
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
                    )
                f.write(chunk)
        
        return {
            "file_path": file_path,
            "filename": unique_filename,
            "original_filename": file.filename,
            "size_bytes": file_size,
            "mime_type": mime_type
        }

    def upload_to_s3(self, file_path: str, key: str):
        if not self.s3_client or not settings.AWS_BUCKET_NAME:
            return None
        self.s3_client.upload_file(file_path, settings.AWS_BUCKET_NAME, key)
        return f"s3://{settings.AWS_BUCKET_NAME}/{key}"

file_service = FileService()
