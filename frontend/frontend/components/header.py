import streamlit as st

def show_header():

    left, right = st.columns([5,1])

    with left:
        st.markdown("# 🏢 AI Due Diligence Platform")
        st.caption("Enterprise Investment Analysis Engine")

    with right:
        st.metric("AI Score", "94%")