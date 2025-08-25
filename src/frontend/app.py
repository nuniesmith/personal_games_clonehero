import streamlit as st
import os
from dotenv import load_dotenv
from src.frontend.sidebar import setup_sidebar

# Load environment variables
load_dotenv()

# Configure Streamlit App
st.set_page_config(
    page_title="Clone Hero Manager",
    page_icon="assets/ch_icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

selected_page = setup_sidebar()

# Render the selected page
selected_page()