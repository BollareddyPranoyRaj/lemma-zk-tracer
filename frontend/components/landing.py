import streamlit as st

def show_landing():
    # Setup columns matching the screenshot layout
    col_left, col_mid, col_right = st.columns([0.8, 2.0, 1.0], gap="large")
    
    # ---------------- LEFT COLUMN: Pipeline Tracker ----------------
    with col_left:
        st.markdown('<div class="badge-secure">SECURE WORKFLOW</div>', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-top:0; font-size: 20px;">Analysis Pipeline</h3>', unsafe_allow_html=True)
        st.markdown(
            '<p class="pipeline-desc">Track document ingestion, extraction, verification, and memo generation from one place.</p>', 
            unsafe_allow_html=True
        )
        
        # Ingestion step status
        if st.session_state.uploaded_file:
            st.markdown(
                '<div class="pipeline-step success"><span>✓</span> PDF Ingested</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="pipeline-step active"><span>•</span> Waiting for PDF</div>',
                unsafe_allow_html=True
            )
            
        # Analysis step status
        st.markdown(
            '<div class="pipeline-step"><span>•</span> Waiting for analysis</div>',
            unsafe_allow_html=True
        )

    # ---------------- CENTER COLUMN: Main Workspace ----------------
    with col_mid:
        st.markdown('<div class="badge-capsule">AI DUE DILIGENCE WORKSPACE</div>', unsafe_allow_html=True)
        st.markdown(
            '<h1 class="main-title">Premium investment memo analysis for modern deal teams.</h1>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<p class="main-subtitle">Upload a Confidential Information Memorandum and turn it into a cryptographically verified investment view.</p>',
            unsafe_allow_html=True
        )
        
        # 3-column features pill cards
        st.markdown("""
            <div class="feature-row">
                <div class="feature-pill-card">
                    <h5>Verified source traceability</h5>
                    <p>Hash-bound metrics</p>
                </div>
                <div class="feature-pill-card">
                    <h5>Fast memo generation</h5>
                    <p>One-click analysis</p>
                </div>
                <div class="feature-pill-card">
                    <h5>Responsive layout</h5>
                    <p>Desktop to mobile</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Upload card section
        st.markdown('<h3 style="font-size: 18px; margin-bottom: 12px;">Upload confidential memorandum</h3>', unsafe_allow_html=True)
        
        # Streamlit Native File Uploader wrapped in custom CSS styling
        uploaded_file = st.file_uploader(
            "Upload PDF",
            type=["pdf"],
            label_visibility="collapsed"
        )
        
        st.markdown(
            '<p style="font-size: 11px; color: var(--text-muted); margin-top: 12px;">Accepted format: PDF. The analysis step will freeze the interface and display a full-screen loader.</p>',
            unsafe_allow_html=True
        )
        
        return uploaded_file

    # ---------------- RIGHT COLUMN: Metadata Info Stack ----------------
    with col_right:
        st.markdown("""
            <div class="info-stacked-card">
                <label>Input</label>
                <div class="value">PDF CIM upload</div>
            </div>
            <div class="info-stacked-card">
                <label>Outputs</label>
                <div class="value">Revenue, EBITDA, Growth, Risk</div>
            </div>
            <div class="info-stacked-card">
                <label>Verification</label>
                <div class="value">Source pages + SHA-256 hashes</div>
            </div>
        """, unsafe_allow_html=True)
        
        return None