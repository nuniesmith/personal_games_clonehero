import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from loguru import logger
from src.services.song_generator import process_song_file

router = APIRouter()

OUTPUT_DIR = Path("/app/data/clonehero_content/generator")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_FORMATS = {".mp3", ".ogg", ".wav", ".flac"}


async def save_uploaded_file(uploaded_file: UploadFile) -> Path:
    """Asynchronously saves an uploaded file with a unique name."""
    file_ext = Path(uploaded_file.filename).suffix.lower()

    if file_ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format: {file_ext}. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    unique_file_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = OUTPUT_DIR / unique_file_name

    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            while chunk := await uploaded_file.read(1024 * 1024):  # Read in 1MB chunks
                await out_file.write(chunk)

        logger.info(f"📥 Uploaded song saved: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"❌ Error saving file {uploaded_file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Error saving uploaded file.")


@router.post("/process_song/")
async def process_song(file: UploadFile = File(...)):
    """Handles song uploads and processes them into Clone Hero format."""
    temp_file_path = await save_uploaded_file(file)

    try:
        logger.info(f"🎵 Processing song: {file.filename}")
        result = await process_song_file(str(temp_file_path))

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "message": "Song processed successfully",
            "notes_chart": result["notes_chart"],
            "tempo": result["tempo"],
            "file_name": file.filename
        }

    except HTTPException:
        raise  # Re-raise known FastAPI errors
    except Exception as e:
        logger.error(f"❌ Unexpected error processing song {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during song processing.")
    finally:
        try:
            os.remove(temp_file_path)
            logger.info(f"🗑️ Removed temporary song file: {temp_file_path}")
        except FileNotFoundError:
            pass