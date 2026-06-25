import streamlit as st

from frontend.components.header import show_header
from frontend.components.verdict import show_verdict
from frontend.components.metrics import show_metrics
from frontend.components.memo import show_memo
from frontend.components.pdf_viewer import show_pdf


def show_dashboard(uploaded_file, data):

    # Header
    show_header()

    st.divider()

    # Verdict
    show_verdict(
        data["decision"],
        data["confidence"]
    )

    st.divider()

    # Financial Metrics
    show_metrics(data["metrics"])

    st.divider()

    # Split Screen
    left, right = st.columns(
        [1.7, 1],
        gap="large"
    )

    with left:
        st.subheader("📄 Original PDF")
        show_pdf(uploaded_file)

    with right:
        show_memo(data)

    st.divider()

    st.caption(
        "© 2026 AI Due Diligence Platform | Secure Hash Verification | Built for Hackathon Demo"
    )