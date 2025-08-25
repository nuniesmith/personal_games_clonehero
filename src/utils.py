import os
import sys
import streamlit as st
from loguru import logger
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Loguru logging
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE_SIZE = os.getenv("LOG_FILE_SIZE", "10MB")
LOG_RETENTION = os.getenv("LOG_RETENTION", "5")
LOG_COMPRESSION = os.getenv("LOG_COMPRESSION", "zip")

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "streamlit_app.log")
logger.add(LOG_FILE, rotation=LOG_FILE_SIZE, retention=LOG_RETENTION, compression=LOG_COMPRESSION, level=LOG_LEVEL)

# Enable console logging only in debug mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
if DEBUG_MODE:
    logger.add(sys.stdout, level="DEBUG")
    logger.debug("🚀 Running in DEBUG mode")

# API Base URL
API_URL = os.getenv("API_URL", "http://clonehero_api:8000")
logger.info(f"🌐 API Base URL: {API_URL}")

def make_api_request(endpoint: str, method="GET", data=None, files=None, params=None):
    """
    Handles API requests with better error handling.
    
    Args:
        endpoint (str): API endpoint (e.g., "songs/")
        method (str): HTTP method (GET, POST, PUT, DELETE)
        data (dict, optional): JSON data payload for POST/PUT
        files (dict, optional): Files for multipart uploads
        params (dict, optional): Query parameters for GET requests

    Returns:
        dict: Response JSON or an error message.
    """
    url = f"{API_URL}/{endpoint}"
    try:
        headers = {"Accept": "application/json"}
        
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=data,
            files=files,
            params=params,
            timeout=60 if method.upper() == "POST" else 30
        )
        
        response.raise_for_status()
        return response.json()
    
    except requests.Timeout:
        logger.error(f"API request timeout: {method} {url}")
        return {"error": "Request timed out. Please try again."}
    
    except requests.RequestException as e:
        logger.error(f"API request failed: {method} {url} - {e}")
        return {"error": f"API request failed: {str(e)}"}

def display_exception(e, user_msg: str):
    """
    Log and display an error from an exception in Streamlit.
    Shows a generic message in production for security.
    
    Args:
        e (Exception): The exception object.
        user_msg (str): User-friendly message to display.
    """
    logger.exception(f"{user_msg}: {str(e)}")
    
    if DEBUG_MODE:
        st.error(f"{user_msg}: {str(e)}")  # Show detailed error in debug mode
    else:
        st.error(user_msg)  # Generic error message for production
    
    st.toast("❌ An error occurred. Please check logs for details.", icon="⚠️")