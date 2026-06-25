import streamlit as st

from components.upload import upload_pdf
from components.dashboard import show_dashboard
from components.loader import processing_animation
from data.mock_data import mock_data

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="AI Investment Memo Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Load CSS ----------------
def load_css():
    try:
        with open("assets/style.css") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )
    except FileNotFoundError:
        pass

load_css()

# ---------------- Session State ----------------
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = False

# ---------------- Sidebar ----------------
with st.sidebar:

    st.title("📊 Analysis Pipeline")

    if st.session_state.uploaded_file:
        st.success("✅ PDF Uploaded")
    else:
        st.info("⏳ Waiting for PDF")

    if st.session_state.show_dashboard:
        st.success("✅ Hash Generated")
        st.success("✅ Revenue Extracted")
        st.success("✅ EBITDA Extracted")
        st.success("✅ Investment Memo Generated")
    else:
        st.info("⏳ Waiting for Analysis")

# ---------------- Upload Screen ----------------
if not st.session_state.show_dashboard:

    uploaded_file = upload_pdf()

    if uploaded_file:

        st.session_state.uploaded_file = uploaded_file

        st.success(f"📄 Uploaded: {uploaded_file.name}")

        if st.button("🚀 Generate Investment Memo"):

            processing_animation()

            st.session_state.show_dashboard = True

            st.rerun()

# ---------------- Dashboard ----------------
else:

    show_dashboard(
        st.session_state.uploaded_file,
        mock_data
    )