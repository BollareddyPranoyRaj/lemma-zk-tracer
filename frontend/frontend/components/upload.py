import streamlit as st

def upload_pdf():

    st.markdown(
        "<h1 class='title'>AI Investment Memo Generator</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p class='subtitle'>Upload Confidential Information Memorandum (CIM)</p>",
        unsafe_allow_html=True
    )

    st.divider()

    uploaded_file = st.file_uploader(
        "📄 Upload PDF",
        type=["pdf"]
    )

    return uploaded_file