import streamlit as st
import requests
from loguru import logger
from src.utils import API_URL, display_exception
import itertools

# Constants
PAGE_SIZE = 10  # Number of songs per page
ALLOWED_EXTENSIONS = ["zip", "rar"]
MAX_FILE_SIZE_GB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_GB * 1024 * 1024 * 1024  # 10GB limit

@st.cache_data(ttl=300)
def fetch_songs(skip=0, limit=PAGE_SIZE):
    """Fetch song list from the API with pagination."""
    try:
        logger.info(f"Fetching song list from API (skip={skip}, limit={limit}).")
        response = requests.get(f"{API_URL}/content/", params={"skip": skip, "limit": limit}, timeout=30)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and "content" in data:
            songs = data["content"]
        elif isinstance(data, list):
            songs = data
        else:
            logger.error(f"Unexpected API response format: {data}")
            return []
        
        logger.success(f"Fetched {len(songs)} songs from the database.")
        return songs
    except requests.RequestException as e:
        logger.error(f"Failed to fetch songs: {e}")
        st.error("Error fetching songs. Please try again later.")
        return []

def display_songs():
    """Display songs grouped by artist and album with pagination."""
    songs = fetch_songs(st.session_state.page * PAGE_SIZE, PAGE_SIZE)
    if not songs:
        st.info("No songs found in the library.")
        return

    total_songs = len(songs)
    total_pages = (total_songs + PAGE_SIZE - 1) // PAGE_SIZE

    # Pagination State
    if "page" not in st.session_state:
        st.session_state.page = 0

    # Pagination Controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous", disabled=st.session_state.page == 0):
            st.session_state.page = max(st.session_state.page - 1, 0)
            st.rerun()

    with col3:
        if st.button("Next ➡️", disabled=(st.session_state.page + 1) >= total_pages):
            st.session_state.page += 1
            st.rerun()

    st.subheader(f"📚 Song Library (Page {st.session_state.page + 1}/{total_pages})")
    
    songs.sort(key=lambda s: (s.get('artist', 'N/A').lower(),
                              s.get('album', 'N/A').lower(),
                              s.get('title', 'N/A').lower()))
    
    for artist, artist_group in itertools.groupby(songs, key=lambda s: s.get('artist', 'N/A')):
        st.markdown(f"## 🎸 {artist}")
        artist_songs = list(artist_group)
        for album, album_group in itertools.groupby(artist_songs, key=lambda s: s.get('album', 'N/A')):
            st.markdown(f"### 📀 {album}")
            for song in album_group:
                with st.container():
                    st.markdown(f"**🎵 Title:** {song.get('title', 'N/A')}")
                    st.write(f"📁 **Folder Path:** `{song.get('file_path', 'N/A')}`")
                    metadata = song.get("metadata", {})
                    if metadata:
                        with st.expander("🔍 Show Metadata"):
                            st.json(metadata, expanded=False)
                st.write("---")

def upload_song():
    """Handles song upload UI."""
    st.header("📤 Upload a Song")
    uploaded_file = st.file_uploader("Choose a .zip or .rar file", type=ALLOWED_EXTENSIONS)
    
    if uploaded_file:
        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            st.error(f"File size exceeds {MAX_FILE_SIZE_GB}GB limit.")
            return
        
        logger.info(f"Uploading file: {uploaded_file.name}")
        
        files = {"file": (uploaded_file.name, uploaded_file, "application/octet-stream")}
        data = {"content_type": "songs"}  # Ensure this matches the API expectation

        with st.spinner("Uploading song..."):
            try:
                response = requests.post(f"{API_URL}/upload_content/", files=files, data=data, timeout=300)
                
                if response.status_code == 200:
                    resp_json = response.json()
                    if "error" in resp_json:
                        st.error(f"Upload error: {resp_json['error']}")
                        logger.error(f"Upload error: {resp_json['error']}")
                    else:
                        st.success("✅ Song uploaded successfully!")
                        logger.success(f"Successfully uploaded: {uploaded_file.name}")
                        st.rerun()
                else:
                    st.error(f"Upload failed: {response.text}")
                    logger.error(f"Upload failed: {uploaded_file.name}, Status Code: {response.status_code}")
            except Exception as e:
                display_exception(e, f"An error occurred while uploading {uploaded_file.name}")

def songs_page():
    """Streamlit UI for managing Clone Hero songs."""
    st.title("🎶 Clone Hero Song Manager")

    # Tabs for Upload and Library
    tab1, tab2 = st.tabs(["📤 Upload", "🎼 Song Library"])

    with tab1:
        upload_song()

    with tab2:
        display_songs()

    # Add information on how the system works
    st.markdown("---")
    st.subheader("📖 How It Works")
    st.write(
        """
        ### **Step-by-Step Process**
        1️⃣ **Upload a Song Archive (.zip or .rar)**  
           - The system accepts **.zip** or **.rar** files containing Clone Hero-compatible songs.  
           - The uploaded archive must contain a `song.ini` file with metadata.
        
        2️⃣ **Automatic Song Processing**  
           - The system extracts the archive and processes the `song.ini` file.  
           - Metadata such as **title, artist, album, and difficulty levels** are read.  
           - The song is automatically stored in the appropriate **artist/album folder**.

        3️⃣ **Database Storage & Organization**  
           - All songs are stored in a PostgreSQL database.  
           - Song metadata is saved, and duplicate entries are **automatically detected and skipped**.

        4️⃣ **View & Manage Your Songs**  
           - Browse uploaded songs in the **Song Library tab**.  
           - Use pagination to navigate **large collections**.

        5️⃣ **Download Processed Files (Future Feature)**  
           - A feature will be added to allow **downloading converted files** in Clone Hero format.  
        """
    )

    st.info("💡 Need help? Ensure the file format is correct, and try again. If issues persist, check the server logs.")   