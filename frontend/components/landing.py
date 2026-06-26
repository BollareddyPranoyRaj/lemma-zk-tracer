import streamlit as st

def show_landing():

    st.markdown("""
<div style="
background:linear-gradient(135deg,#1E293B,#0F172A);
padding:25px;
border-radius:18px;
border:1px solid #334155;
box-shadow:0 8px 25px rgba(0,0,0,.35);
margin-bottom:20px;
">

<h3 style="margin-top:0;color:white;">
📝 Executive Summary
</h3>

<p style="
font-size:17px;
line-height:1.8;
color:#CBD5E1;
">

{}
</p>

</div>
""".format(data["executive_summary"]), unsafe_allow_html=True)