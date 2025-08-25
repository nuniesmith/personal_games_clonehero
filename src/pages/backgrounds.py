import streamlit as st
from loguru import logger
import requests
from src.utils import display_exception, API_URL

# Constants
FILE_EXTENSIONS = {
    "Image": ["png", "jpg", "jpeg", "zip", "rar"],
    "Video": ["webm", "mp4", "avi", "mpeg", "zip", "rar"]
}

def fetch_uploaded_backgrounds(bg_type):
    """Fetch previously uploaded backgrounds from the API."""
    try:
        response = requests.get(f"{API_URL}/list_content/?content_type={bg_type}", timeout=30)
        response.raise_for_status()
        return response.json().get("files", [])
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {bg_type} backgrounds: {e}")
        return []

def upload_background(uploaded_file, bg_type):
    """Handle background upload and provide UI feedback."""
    try:
        logger.info(f"Uploading {bg_type} background: {uploaded_file.name}")
        files = {"file": uploaded_file}
        data = {"content_type": "image_backgrounds" if bg_type == "Image" else "video_backgrounds"}

        with st.spinner("Uploading..."):
            response = requests.post(
                f"{API_URL}/upload_content/", files=files, data=data, timeout=60
            )

        if response.status_code == 200:
            resp_json = response.json()
            if "error" in resp_json:
                st.error(f"Upload failed: {resp_json['error']}")
                logger.error(f"Server error: {resp_json['error']}")
            else:
                st.success("✅ Background uploaded successfully!")
                st.rerun()  # Refresh UI to show newly uploaded backgrounds
        else:
            st.error(f"Upload failed: {response.text}")
            logger.error(f"Upload failed for {uploaded_file.name}, Status Code: {response.status_code}")
    except Exception as e:
        display_exception(e, f"Error uploading {bg_type} background")

def backgrounds_page():
    """
    Streamlit UI for managing backgrounds.
    Allows users to upload Image/Video backgrounds and view existing uploads.
    """
    st.title("🎨 Backgrounds Manager")

    tab1, tab2 = st.tabs(["🖼️ Image Backgrounds", "🎥 Video Backgrounds"])

    for tab, bg_type in zip([tab1, tab2], ["Image", "Video"]):
        with tab:
            st.subheader(f"{bg_type} Backgrounds")
            
            # Upload Section
            uploaded_file = st.file_uploader(
                f"Upload a {bg_type} background", type=FILE_EXTENSIONS[bg_type]
            )
            if uploaded_file:
                upload_background(uploaded_file, bg_type)

            # Display Existing Backgrounds
            st.write(f"📂 **Existing {bg_type} Backgrounds**")
            uploaded_backgrounds = fetch_uploaded_backgrounds(bg_type)

            if uploaded_backgrounds:
                for bg in uploaded_backgrounds:
                    st.markdown(f"- `{bg}`")
            else:
                st.info(f"No {bg_type.lower()} backgrounds found.")