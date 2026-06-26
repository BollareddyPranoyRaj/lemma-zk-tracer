import streamlit as st

def show_metrics(metrics):

    st.markdown("## 📊 Financial Snapshot")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 Revenue",
            value=metrics["Revenue"]
        )

    with col2:
        st.metric(
            label="📈 EBITDA",
            value=metrics["EBITDA"]
        )

    with col3:
        st.metric(
            label="📊 YoY Growth",
            value=metrics["Growth"]
        )

    with col4:
        st.metric(
            label="⚠️ Risk",
            value=metrics["Risk"]
        )