import os
import librosa
import numpy as np
from pathlib import Path
from loguru import logger
from typing import Dict, Any

OUTPUT_DIR = Path("/app/data/clonehero_content/generator")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NOTE_MAPPING = 6  # Number of note types in Clone Hero

def analyze_audio(file_path: str) -> Dict[str, Any]:
    """Analyze audio to detect tempo, beats, and note positions."""
    try:
        y, sr = librosa.load(file_path, sr=None)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)

        return {
            "tempo": tempo,
            "beat_times": beat_times
        }
    except Exception as e:
        logger.error(f"Error analyzing audio: {str(e)}")
        raise

def generate_notes_chart(song_name, beat_times, output_path):
    """Generate a notes.chart file based on detected beats."""
    try:
        with output_path.open("w") as f:
            f.write(f"[Song]\n{{\n  Name = {song_name}\n  Artist = Unknown\n  Charter = AI\n}}\n")
            f.write("\n[SyncTrack]\n{\n")
            for time in beat_times:
                f.write(f"  {int(time * 1000)} = TS {int(time * 1000)}\n")
            f.write("}\n")
    except Exception as e:
        logger.error(f"Error writing notes.chart: {str(e)}")
        raise

def process_song_file(file_path: str) -> Dict[str, Any]:
    """Process an uploaded song file and generate Clone Hero assets."""
    try:
        logger.info(f"Processing song file: {file_path}")

        analysis = analyze_audio(file_path)
        tempo, beat_times = analysis["tempo"], analysis["beat_times"]

        song_name = Path(file_path).stem
        song_output_dir = OUTPUT_DIR / song_name
        song_output_dir.mkdir(parents=True, exist_ok=True)
        notes_chart_path = song_output_dir / "notes.chart"

        generate_notes_chart(song_name, beat_times, notes_chart_path)

        # Import store_content inside function to avoid circular imports
        from src.services.service_manager import store_content
        store_content(str(song_output_dir), "song")

        return {
            "message": "Song processed successfully",
            "notes_chart": str(notes_chart_path),
            "tempo": tempo
        }
    except Exception as e:
        logger.error(f"Error processing song: {str(e)}")
        return {"error": str(e)}