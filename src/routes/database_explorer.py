from fastapi import APIRouter, HTTPException, Query
from src.services.database_explorer import get_all_songs, delete_song_by_id
from loguru import logger

router = APIRouter()

@router.get("/songs/")
async def fetch_songs(
    search: str = Query(None, title="Search Query", description="Filter by title, artist, or album"),
    limit: int = Query(50, ge=1, le=100, title="Limit", description="Number of results to return"),
    offset: int = Query(0, ge=0, title="Offset", description="Pagination offset")
):
    """Fetch all songs from the database with optional search and pagination."""
    try:
        songs = get_all_songs(search_query=search.strip() if search else None, limit=limit, offset=offset)
        total_songs = len(songs)
        
        if total_songs == 0:
            return {"message": "⚠️ No songs found.", "total": 0, "songs": []}
        
        return {"total": total_songs, "songs": songs}
    except Exception as e:
        logger.exception(f"❌ Error fetching songs: {e}")
        raise HTTPException(status_code=500, detail="Error fetching songs")

@router.delete("/songs/{song_id}")
async def delete_song(song_id: int):
    """Delete a song by ID from the database, ensuring it exists before deletion."""
    try:
        deleted = delete_song_by_id(song_id)
        if not deleted:
            logger.warning(f"⚠️ Attempted to delete non-existent song ID {song_id}.")
            raise HTTPException(status_code=404, detail="Song not found")
        
        return {"message": f"✅ Song ID {song_id} deleted successfully."}
    except Exception as e:
        logger.exception(f"❌ Error deleting song ID {song_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting song")