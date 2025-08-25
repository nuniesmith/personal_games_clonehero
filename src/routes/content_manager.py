from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
import os
import aiofiles
import tempfile
import uuid
import httpx
from loguru import logger
from dotenv import load_dotenv
from typing import Dict, Any
from pydantic import BaseModel
from src.services.content_manager import process_and_store_content
from src.services.content_utils import extract_content, list_all_content

# Load environment variables
load_dotenv()

router = APIRouter()

# Allowed content types
ALLOWED_CONTENT_TYPES = {"backgrounds", "colors", "highways", "songs"}
ALLOWED_EXTENSIONS = {".zip", ".rar", ".png", ".jpg"}

# File size limits
MAX_FILE_SIZE_GB = int(os.getenv("MAX_FILE_SIZE_GB", 10))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_GB * 1024 * 1024 * 1024


def get_temp_file(file_name: str) -> str:
    """Returns a secure temp file path in the system temp directory."""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file_name}")


def validate_file_extension(file_name: str):
    """Ensure the uploaded/downloaded file has a valid extension"""
    ext = os.path.splitext(file_name)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file extension: {ext}")


async def validate_file_size(file: UploadFile):
    """Check if uploaded file exceeds the allowed size limit."""
    size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    while chunk := await file.read(chunk_size):
        size += len(chunk)
        if size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=413, detail=f"File too large (max {MAX_FILE_SIZE_GB}GB)")
    file.file.seek(0)  # Reset pointer after checking


@router.post("/upload_content/", summary="Upload Clone Hero Content", tags=["Upload"])
async def upload_content(
    request: Request,
    file: UploadFile = File(...),
    content_type: str = Form(...)
) -> Dict[str, Any]:  # Ensure return type is Dict
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid content type: {content_type}")

    await validate_file_size(file)
    validate_file_extension(file.filename)
    temp_file_path = get_temp_file(file.filename)

    logger.info(f"📤 Received upload for {content_type}, file={file.filename}")

    try:
        async with aiofiles.open(temp_file_path, "wb") as buffer:
            while chunk := await file.read(65536):  # Read in 64KB chunks
                await buffer.write(chunk)

        logger.info(f"✅ File saved temporarily at: {temp_file_path}")

        # Extract content and process files
        result = await extract_content(temp_file_path, content_type)

        # If songs, process further
        if content_type == "songs":
            result = await process_and_store_content(temp_file_path, content_type)

        if not isinstance(result, dict):  # Ensure result is a dictionary
            raise ValueError(f"Invalid response format from processing functions: {result}")

        return result

    except Exception as e:
        logger.exception(f"❌ Error processing file {file.filename}: {e}")
        return {"status": "error", "message": "Internal Server Error"}
    
    finally:
        try:
            os.remove(temp_file_path)
            logger.info(f"🗑️ Removed temporary file: {temp_file_path}")
        except FileNotFoundError:
            pass

class URLDownloadRequest(BaseModel):
    url: str


@router.post("/download/", summary="Download and Extract Content", tags=["Download"])
async def download_and_extract(request: URLDownloadRequest) -> Dict[str, Any]:
    """
    Download an archive (zip/rar) from a provided URL, save it temporarily,
    process it by extracting its content, and return the result.
    """
    file_name = request.url.split("/")[-1]  # Extract filename from URL
    validate_file_extension(file_name)

    temp_file_path = get_temp_file(file_name)
    logger.info(f"Downloading file from: {request.url}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(request.url, timeout=60)
            response.raise_for_status()

            async with aiofiles.open(temp_file_path, "wb") as f:
                await f.write(response.content)

        logger.info(f"✅ File downloaded to: {temp_file_path}")

        # Extract content
        result = await extract_content(temp_file_path, "songs")

        # If songs, process them into the database
        if "songs" in request.url:
            result = await process_and_store_content(temp_file_path, "songs")

        return result

    except Exception as e:
        logger.exception(f"❌ Download failed for {request.url}: {e}")
        raise HTTPException(status_code=500, detail="Download failed")

    finally:
        try:
            os.remove(temp_file_path)
            logger.info(f"🗑️ Removed temporary file: {temp_file_path}")
        except FileNotFoundError:
            pass


@router.get("/content/", summary="List All Content", tags=["Content"])
async def list_content(skip: int = 0, limit: int = 10) -> Dict[str, Any]:
    """
    List all stored content (songs, backgrounds, highways, colors) with pagination.
    """
    try:
        content = await list_all_content()  # Run DB query asynchronously
        paginated_content = content[skip: skip + limit]

        return {
            "total": len(content),
            "returned": len(paginated_content),
            "content": paginated_content
        }

    except Exception as e:
        logger.exception("❌ Error listing content")
        raise HTTPException(status_code=500, detail="Failed to fetch content")