import streamlit as st
from frontend.components.verification import verify_metric

def show_memo(data):

    verification = data["verification"]

    st.title("🤖 Investment Memo")

    st.divider()

    # ================= Company Overview =================

    st.subheader("🏢 Company Overview")

    with st.container(border=True):

        c1, c2 = st.columns([1, 3])

        with c1:
            st.write("**🏢 Company**")
        with c2:
            st.write(data["company"])

        st.divider()

        c1, c2 = st.columns([1, 3])

        with c1:
            st.write("**🏭 Sector**")
        with c2:
            st.write(data["sector"])

        st.divider()

        c1, c2 = st.columns([1, 3])

        with c1:
            st.write("**📌 Decision**")

        with c2:
            if data["decision"] == "GO":
                st.success("GO")
            else:
                st.error("NO GO")

    st.divider()

    # ================= Executive Summary =================

    st.subheader("📝 Executive Summary")

    with st.container(border=True):

        st.write(data["executive_summary"])

    st.divider()

    # ================= Source Verification =================

    st.subheader("🔍 Source Verification")

    verify_metric("Revenue", verification)

    verify_metric("EBITDA", verification)

    verify_metric("Growth", verification)

    st.divider()

    # ================= Final Recommendation =================

    if data["decision"] == "GO":
        st.success("✅ Final Recommendation : GO")
    else:
        st.error("❌ Final Recommendation : NO GO")