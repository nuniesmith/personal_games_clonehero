import os
import shutil
import uuid
import configparser
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any
from src.database import get_connection
from psycopg2.extras import Json, DictCursor

# Optional metadata fields for songs
OPTIONAL_FIELDS = [
    "genre", "year", "album_track", "playlist_track", "charter", "icon",
    "diff_guitar", "diff_rhythm", "diff_bass", "diff_guitar_coop", "diff_drums",
    "diff_drums_real", "diff_guitarghl", "diff_bassghl", "diff_rhythm_ghl",
    "diff_guitar_coop_ghl", "diff_keys", "song_length", "preview_start_time",
    "video_start_time", "modchart", "loading_phrase", "delay"
]

def parse_song_ini(ini_path: Path) -> Dict[str, Any]:
    """Parse the song.ini file to retrieve metadata."""
    config = configparser.ConfigParser()
    try:
        with ini_path.open("r", encoding="utf-8-sig") as f:
            config.read_file(f)
    except Exception as e:
        logger.error(f"❌ Failed to read {ini_path}: {e}")
        return {}

    if not config.has_section("song"):
        logger.warning(f"⚠️ Missing [song] section in {ini_path}")
        return {}

    name = config.get("song", "name", fallback=None)
    artist = config.get("song", "artist", fallback=None)
    album = config.get("song", "album", fallback=None)

    if not name or not artist or not album:
        logger.warning(f"⚠️ Missing required fields in {ini_path}, skipping file.")
        return {}

    metadata = {
        field: config.get("song", field, fallback=None)
        for field in OPTIONAL_FIELDS if config.has_option("song", field)
    }

    return {
        "title": name.strip(),
        "artist": artist.strip(),
        "album": album.strip(),
        "metadata": {k: v.strip() for k, v in metadata.items() if v is not None}
    }

def add_content_to_db(title: str, artist: str, album: str, file_path: str, metadata: dict = None) -> int:
    """Insert content into the database and return its ID."""
    metadata = metadata or {}

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(
                    "SELECT id FROM songs WHERE title = %s AND artist = %s AND album = %s",
                    (title, artist, album)
                )
                existing_song = cursor.fetchone()
                if existing_song:
                    logger.warning(f"⚠️ Duplicate detected, skipping insert: {file_path}")
                    return existing_song[0]

                cursor.execute(
                    """
                    INSERT INTO songs (title, artist, album, file_path, metadata)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                    """,
                    (title, artist, album, file_path, Json(metadata))
                )
                content_id = cursor.fetchone()[0]
                conn.commit()

        logger.success(f"✅ Content added: {title} - {artist} ({album})")
        return content_id
    except Exception as e:
        logger.exception(f"❌ Error inserting content: {e}")
        return -1

async def process_and_store_content(temp_extract_dir: str, content_type: str) -> List[Dict[str, Any]]:
    """Process and store content, including songs and visual assets."""
    from src.services.content_utils import get_final_directory  # Import inside function to prevent circular imports

    stored_content = []
    temp_extract_dir = Path(temp_extract_dir)

    for ini_path in temp_extract_dir.rglob("song.ini"):
        parsed = parse_song_ini(ini_path)
        if not parsed:
            continue  # Skip if parsing failed

        title, artist, album, metadata = parsed["title"], parsed["artist"], parsed["album"], parsed["metadata"]

        # Ensure unique file storage
        artist_dir = Path(get_final_directory("songs")) / artist
        artist_dir.mkdir(parents=True, exist_ok=True)
        final_dir = artist_dir / f"{title}_{uuid.uuid4().hex[:8]}"

        try:
            shutil.move(str(ini_path.parent), str(final_dir))
            content_id = add_content_to_db(title, artist, album, str(final_dir), metadata)

            if content_id != -1:
                stored_content.append({
                    "id": content_id,
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "folder_path": str(final_dir),
                    "metadata": metadata
                })
        except Exception as e:
            logger.error(f"❌ Error moving file {ini_path.parent} to {final_dir}: {e}")
    
    return stored_content

def fetch_content_from_db(skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch paginated content from the database."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, title, artist, album, file_path, metadata
                    FROM songs
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, skip)
                )
                content = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "artist": row["artist"],
                "album": row["album"],
                "file_path": row["file_path"],
                "metadata": row["metadata"] if row["metadata"] else {}
            }
            for row in content
        ]
    except Exception as e:
        logger.exception(f"❌ Error fetching content: {e}")
        return []