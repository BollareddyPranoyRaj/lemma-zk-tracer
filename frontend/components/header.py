import streamlit as st

def show_header(ai_score=None):

    left, right = st.columns([5,1])

    with left:
        st.markdown("# 🏢 AI Due Diligence Platform")
        st.caption("Enterprise Investment Analysis Engine")

    with right:
        score_str = f"{ai_score}%" if ai_score is not None else "N/A"
        st.metric("AI Score", score_str)