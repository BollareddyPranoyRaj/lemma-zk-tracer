import streamlit as st

from components.header import show_header
from components.verdict import show_verdict
from components.metrics import show_metrics
from components.memo import show_memo
from components.pdf_viewer import show_pdf


def show_dashboard(uploaded_file, data):

    # ================= Header =================
    show_header()

    st.divider()

    # ================= Verdict =================
    show_verdict(
        data["decision"],
        data["confidence"]
    )

    st.divider()

    # ================= Financial Metrics =================
    show_metrics(data["metrics"])

    st.divider()

    # ================= Split Screen =================
    left, right = st.columns([6, 4], gap="large")

    with left:
        show_pdf(uploaded_file)

    with right:
        show_memo(data)

        st.divider()

        # ================= Footer =================
        st.caption(
            "© 2026 AI Due Diligence Platform | Secure Hash Verification | Built for Hackathon Demo"
        )