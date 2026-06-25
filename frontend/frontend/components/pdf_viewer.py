import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

def show_pdf(uploaded_file):

    st.subheader("📄 Original PDF")

    pdf_viewer(
        uploaded_file.read(),
        width="100%",
        height=950
    )