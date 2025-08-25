import streamlit as st
from src.pages.song_generator import song_generation_page
from src.pages.songs import songs_page
from src.pages.database_explorer import database_explorer_page
from src.pages.colors import colors_page
from src.pages.backgrounds import backgrounds_page
from src.pages.highways import highways_page

def setup_sidebar():
    """Define sidebar UI elements using native Streamlit components."""
    st.sidebar.image("assets/ch_icon.png", width=50)
    st.sidebar.title("Clone Hero Manager")

    # Navigation Menu (Pages First)
    st.sidebar.markdown("---")    
    st.sidebar.markdown("### 📂 Navigation")
    PAGES = {
        "📁 Database Explorer": database_explorer_page,
        "📤 Upload Songs": songs_page,
        "🎵 Generate Songs": song_generation_page,
        "🎨 Colors": colors_page,
        "🌆 Backgrounds": backgrounds_page,
        "🛣️ Highways": highways_page,
    }
    
    menu_selection = st.sidebar.radio("📌 Select a Page", list(PAGES.keys()))
    
    # Refresh & Cache Clearing Options
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh App"):
        st.rerun()

    if st.sidebar.button("♻️ Clear Cache"):
        st.cache_data.clear()
        st.rerun()

    # Footer Info
    st.sidebar.markdown("---")
    st.sidebar.write("🛠️ **Clone Hero Manager** - v1.0.0")
    st.sidebar.write("🚀 Developed with ❤️ using Streamlit")

    return PAGES[menu_selection]