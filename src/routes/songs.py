import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException
from loguru import logger
from src.services.service_manager import process_song, store_content

router = APIRouter()

TEMP_DIR = "/tmp"  # Define temporary directory


async def save_temp_file(file: UploadFile) -> str:
    """Asynchronously save uploaded file to a temp directory."""
    file_ext = os.path.splitext(file.filename)[-1].lower()
    temp_file_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}{file_ext}")

    try:
        async with aiofiles.open(temp_file_path, "wb") as buffer:
            while chunk := await file.read(65536):  # Read in 64KB chunks
                await buffer.write(chunk)

        logger.info(f"📁 File saved temporarily at: {temp_file_path}")
        return temp_file_path

    except Exception as e:
        logger.exception(f"❌ Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")


@router.post("/upload_song/")
async def upload_song(file: UploadFile = File(...)):
    """Upload a song file and process it for Clone Hero."""
    temp_file_path = await save_temp_file(file)

    try:
        result = await process_song(temp_file_path)
        return result
    except Exception as e:
        logger.exception(f"❌ Error processing song: {e}")
        raise HTTPException(status_code=500, detail="Error processing song")
    finally:
        try:
            os.remove(temp_file_path)
            logger.info(f"🗑️ Removed temporary song file: {temp_file_path}")
        except FileNotFoundError:
            pass


@router.post("/extract_content/")
async def extract_content(file: UploadFile = File(...), content_type: str = "songs"):
    """Upload and extract song content (e.g., .zip/.rar archives)."""
    temp_file_path = await save_temp_file(file)

    try:
        result = await store_content(temp_file_path, content_type)
        return result
    except Exception as e:
        logger.exception(f"❌ Error extracting content: {e}")
        raise HTTPException(status_code=500, detail="Error extracting content")
    finally:
        try:
            os.remove(temp_file_path)
            logger.info(f"🗑️ Removed temporary extracted file: {temp_file_path}")
        except FileNotFoundError:
            pass