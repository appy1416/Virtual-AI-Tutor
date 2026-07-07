import os
import shutil
import uuid
from fastapi import UploadFile

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage", "audio")

def ensure_storage_exists():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR, exist_ok=True)

async def upload_to_cloud(file: UploadFile, session_id: str) -> str:
    """
    Saves audio file locally for development, returning path-based mock URL.
    """
    ensure_storage_exists()
    
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".mp3"
    filename = f"{session_id}_{uuid.uuid4().hex}{file_ext}"
    dest_path = os.path.join(STORAGE_DIR, filename)

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Return local storage reference string
    return f"/storage/audio/{filename}"

async def delete_from_cloud(file_url: str) -> bool:
    """
    Deletes the local audio file.
    """
    if not file_url:
        return False
    filename = os.path.basename(file_url)
    file_path = os.path.join(STORAGE_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
