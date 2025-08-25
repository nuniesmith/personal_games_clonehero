import streamlit as st
from loguru import logger
import requests
from src.utils import display_exception, API_URL

# Allowed file types
ALLOWED_EXTENSIONS = ["ini", "zip", "rar"]

def fetch_uploaded_colors():
    """Fetch previously uploaded color profiles from the API."""
    try:
        response = requests.get(f"{API_URL}/list_content/?content_type=colors", timeout=30)
        response.raise_for_status()
        return response.json().get("files", [])
    except requests.RequestException as e:
        logger.error(f"Failed to fetch color profiles: {e}")
        return []

def upload_color_profile(uploaded_file):
    """Handle color profile upload and provide UI feedback."""
    try:
        logger.info(f"Uploading color profile: {uploaded_file.name}")
        files = {"file": uploaded_file}
        data = {"content_type": "colors"}

        with st.spinner("Uploading..."):
            response = requests.post(f"{API_URL}/upload_content/", files=files, data=data, timeout=60)

        if response.status_code == 200:
            resp_json = response.json()
            if "error" in resp_json:
                st.error(f"Upload failed: {resp_json['error']}")
                logger.error(f"Server error: {resp_json['error']}")
            else:
                st.success("✅ Color profile uploaded successfully!")
                st.rerun()  # Refresh UI to show newly uploaded profiles
        else:
            st.error(f"Upload failed: {response.text}")
            logger.error(f"Upload failed for {uploaded_file.name}, Status Code: {response.status_code}")
    except Exception as e:
        display_exception(e, "Error uploading color profile")

def delete_color_profile(profile_name):
    """Delete a color profile via API request."""
    try:
        response = requests.delete(f"{API_URL}/delete_content/?content_type=colors&file={profile_name}", timeout=30)
        response.raise_for_status()
        st.success(f"🗑️ Deleted `{profile_name}` successfully!")
        st.rerun()
    except requests.RequestException as e:
        logger.error(f"Failed to delete {profile_name}: {e}")
        st.error(f"Failed to delete `{profile_name}`. Please try again.")

def colors_page():
    """Streamlit UI for managing color profiles."""
    st.title("🎨 Color Profile Manager")

    # Upload Section
    uploaded_file = st.file_uploader(
        "Upload a color profile (.ini) or an archive (.zip/.rar) with multiple .ini files",
        type=ALLOWED_EXTENSIONS
    )
    if uploaded_file:
        upload_color_profile(uploaded_file)

    # Display Existing Color Profiles
    st.write("📂 **Existing Color Profiles**")
    uploaded_profiles = fetch_uploaded_colors()

    if uploaded_profiles:
        for profile in uploaded_profiles:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- `{profile}`")
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{hash(profile)}"):
                    delete_color_profile(profile)
    else:
        st.info("No color profiles found.")