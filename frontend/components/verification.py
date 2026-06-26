import streamlit as st

def verify_metric(metric_name, verification):

    info = verification[metric_name]

    with st.expander(f"🔍 Verify {metric_name}"):

        if info["verified"]:

            st.success("Verification Successful")

            st.markdown(f"**📄 Page:** {info['page']}")

            st.markdown("**🔐 SHA-256 Hash**")

            st.code(info["hash"])

            st.markdown("**📑 Source Sentence**")

            st.info(info["source"])

        else:

            st.error("Verification Failed")

            st.warning("No matching source found.")