import streamlit as st

def upload_pdf():
    # 1. Main visual header
    st.markdown("""
        <div style="text-align: center; padding: 20px 0 10px 0;">
            <h2 style="font-size: 38px; margin-bottom: 8px; background: linear-gradient(135deg, #FFFFFF 0%, #A37EF5 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Secure Document Ingestion
            </h2>
            <p style="font-size: 15px; color: #A1A1AA; max-width: 600px; margin: 0 auto 30px auto;">
                Analyze a Prospectus, Confidential Information Memorandum (CIM), or Financial Statement.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 2. Main upload card
    st.markdown("""
        <div class="glass-card" style="padding: 24px; margin-bottom: 24px;">
            <h4 style="margin: 0 0 12px 0; font-size: 16px; color: white;">INSTRUCTIONS</h4>
            <ul style="color: #A1A1AA; font-size: 14px; padding-left: 20px; line-height: 1.6; margin-bottom: 0;">
                <li>Files are securely indexed directly onto your dedicated Lemma Pod filesystem.</li>
                <li>Verify your <strong>Mandate Thresholds</strong> in the left sidebar prior to running the memo generator.</li>
                <li>For testing, you can use the generated <strong>test_prospectus.pdf</strong> in the root folder.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    # 3. Streamlit uploader
    uploaded_file = st.file_uploader(
        "Upload PDF Document",
        type=["pdf"],
        label_visibility="collapsed"
    )

    return uploaded_file