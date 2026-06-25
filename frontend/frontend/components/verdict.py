import streamlit as st

def show_verdict(decision, confidence):

    if decision == "GO":

        st.success(
            f"🟢 GO DECISION | Confidence : {confidence}%"
        )

    else:

        st.error(
            f"🔴 NO GO | Confidence : {confidence}%"
        )