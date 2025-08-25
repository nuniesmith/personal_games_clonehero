import streamlit as st
import requests
from loguru import logger
from src.utils import API_URL, display_exception

def process_song(file) -> dict:
    """Uploads a song to the backend for processing into Clone Hero format."""
    try:
        files = {"file": file}
        with st.spinner("Uploading and processing song..."):
            response = requests.post(f"{API_URL}/process_song/", files=files, timeout=60)
        
        response.raise_for_status()
        result = response.json()

        if not isinstance(result, dict):
            raise ValueError(f"Invalid response format: {result}")

        return result
    except requests.RequestException as e:
        logger.error(f"Failed to process song: {e}")
        return {"error": str(e)}
    except ValueError as e:
        logger.error(f"Unexpected response format: {e}")
        return {"error": "Invalid server response format."}

def song_generation_page():
    """Streamlit UI for processing songs into Clone Hero format."""
    st.title("🎸 Clone Hero Song Processor")
    st.write("Upload a song file, and we'll process it into Clone Hero format!")

    # Upload song file
    st.header("📤 Upload a Song for Processing")
    uploaded_file = st.file_uploader(
        "Choose a song file (MP3, WAV, OPUS, FLAC, OGG)", 
        type=["mp3", "wav", "opus", "flac", "ogg"]
    )

    if uploaded_file:
        st.write(f"**Processing:** {uploaded_file.name}")
        with st.spinner("Analyzing audio and generating notes..."):
            result = process_song(uploaded_file)

        if "error" in result:
            st.error(f"🚨 Error processing song: {result['error']}")
            display_exception(result["error"], "An error occurred while processing the song.")
        else:
            st.success("✅ Song processed successfully!")
            st.write(f"🎵 **Generated Notes Chart:** `{result.get('notes_chart', 'N/A')}`")
            st.write(f"🎶 **Detected Tempo:** `{result.get('tempo', 'Unknown')} BPM`")
            
            # Ensure download URL is valid before requesting
            notes_chart_url = result.get("notes_chart")
            if notes_chart_url:
                try:
                    response = requests.get(notes_chart_url, timeout=10)
                    response.raise_for_status()
                    st.download_button(
                        "⬇️ Download notes.chart",
                        data=response.content,
                        file_name="notes.chart",
                        mime="text/plain"
                    )
                except requests.RequestException as e:
                    st.error(f"⚠️ Failed to retrieve the generated notes.chart file: {e}")

    st.markdown("---")
    st.subheader("📖 How It Works")
    st.write(
        """
        ### **Step-by-Step Process**
        1️⃣ **Upload a Song File**  
           - Supported formats: **MP3, WAV, OPUS, FLAC, OGG**.  
           - The file is analyzed for **tempo, beat detection, and key recognition**.  

        2️⃣ **Automatic Note Generation**  
           - The system detects **BPM (beats per minute)** and extracts rhythm patterns.  
           - **AI-powered** note generation maps the song structure to Clone Hero format.  

        3️⃣ **Download & Play**  
           - Once processing is complete, you can download the **notes.chart** file.  
           - The file is **Clone Hero-compatible** and ready to be played!  

        ### **🔍 Features of the Processor**
        ✅ **Automatic Charting** based on tempo and rhythm analysis.  
        ✅ **Supports Multi-Instrument Tracks** (future expansion).  
        ✅ **Handles Variable Tempos** using advanced time signature detection.  
        ✅ **Error Detection & Prevention** to avoid incorrect mappings.  
        """
    )

    st.info("💡 Need help? Ensure the file format is correct, and try again. If issues persist, check the server logs.")   