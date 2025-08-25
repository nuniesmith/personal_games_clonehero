import asyncio
from loguru import logger
from src.services.song_generator import process_song_file
from src.services.content_manager import process_and_store_content


async def process_song(file_path: str):
    """Wrapper to process a song file asynchronously."""
    try:
        logger.info(f"🎵 Processing song file: {file_path}")
        result = await asyncio.to_thread(process_song_file, file_path)
        return result
    except Exception as e:
        logger.error(f"❌ Error processing song file {file_path}: {e}")
        return {"error": str(e)}


async def store_content(temp_extract_dir: str, content_type: str):
    """Wrapper to process and store extracted content asynchronously."""
    try:
        logger.info(f"📦 Storing extracted content: {content_type} at {temp_extract_dir}")
        result = await asyncio.to_thread(process_and_store_content, temp_extract_dir, content_type)
        return result
    except Exception as e:
        logger.error(f"❌ Error storing content {content_type} at {temp_extract_dir}: {e}")
        return {"error": str(e)}