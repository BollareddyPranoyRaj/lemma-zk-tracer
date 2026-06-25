import streamlit as st
from frontend.components.verification import verify_metric


def show_memo(data):

    verification = data["verification"]

    st.title("🤖 Investment Memo")

    st.divider()

    # ================= Company Overview =================

    st.subheader("🏢 Company Overview")

    with st.container(border=True):

        st.markdown(f"### {data['company']}")

        st.write(f"**🏥 Sector:** {data['sector']}")

        st.write(f"**📌 Decision:** {data['decision']}")

    st.divider()

    # ================= Financial Highlights =================

    st.subheader("📊 Financial Highlights")

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "💰 Revenue",
            data["metrics"]["Revenue"]
        )

    with c2:
        st.metric(
            "📈 EBITDA",
            data["metrics"]["EBITDA"]
        )

    c3, c4 = st.columns(2)

    with c3:
        st.metric(
            "📊 Growth",
            data["metrics"]["Growth"]
        )

    with c4:
        st.metric(
            "⚠️ Risk",
            data["metrics"]["Risk"]
        )

    st.divider()

    # ================= Executive Summary =================

    st.subheader("📝 Executive Summary")

    with st.container(border=True):

        st.markdown(f"""
### 📊 Investment Highlights

- 💰 **Revenue:** {data["metrics"]["Revenue"]}

- 📈 **EBITDA:** {data["metrics"]["EBITDA"]}

- 📊 **Growth:** {data["metrics"]["Growth"]}

- 🏥 **Sector:** {data["sector"]}

- ⚠️ **Risk:** {data["metrics"]["Risk"]}

- 🚀 **Recommendation:** **{data["decision"]}**
""")

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