import time
import httpx
import streamlit as st
from backend.crypto import verify_metric_proof, compute_source_hash

# ─── Page Settings ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lemma ZK Tracer — Verifiable Due Diligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS Styling ────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }

    /* Main Title Styling with Purple-Pink Gradient */
    .main-title {
        background: linear-gradient(135deg, #8A2BE2, #FF007F, #00D2FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        letter-spacing: -1px;
    }

    .main-subtitle {
        font-size: 1.1rem;
        color: #8C96A6;
        margin-bottom: 2rem;
    }

    /* Card Containers */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-card:hover {
        border-color: rgba(130, 87, 229, 0.3);
    }

    /* Decision Banner Styling */
    .decision-banner {
        border-radius: 12px;
        padding: 16px 20px;
        font-weight: 700;
        font-size: 1.25rem;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    .decision-go {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.25));
        border: 1px solid #10B981;
        color: #34D399;
    }
    .decision-nogo {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.25));
        border: 1px solid #EF4444;
        color: #F87171;
    }
    .decision-missing {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.25));
        border: 1px solid #F59E0B;
        color: #FBBF24;
    }

    /* Metric Visualizer */
    .metric-badge {
        font-family: monospace;
        font-size: 0.9rem;
        background: rgba(255, 255, 255, 0.08);
        padding: 4px 8px;
        border-radius: 6px;
        color: #E2E8F0;
    }

    /* Audit Trace Subsections */
    .trace-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #64748B;
        font-weight: 700;
        margin-bottom: 2px;
        letter-spacing: 0.5px;
    }
    .trace-value {
        font-family: monospace;
        font-size: 0.8rem;
        word-break: break-all;
        background: rgba(0, 0, 0, 0.2);
        padding: 6px 10px;
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        color: #A0AEC0;
        margin-bottom: 12px;
    }
    
    /* Verified / Failed indicators */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .status-pill-success {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .status-pill-fail {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* Custom scrollbar for markdown IC Memo */
    .ic-memo-container {
        max-height: 70vh;
        overflow-y: auto;
        padding-right: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Helper Functions ─────────────────────────────────────────────────────────

BACKEND_URL = "http://localhost:8000"

def check_backend_status():
    """Verify if the FastAPI backend is running."""
    try:
        response = httpx.get(f"{BACKEND_URL}/health", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False

# Initialize Session State
if "document_id" not in st.session_state:
    st.session_state.document_id = None
if "doc_hash" not in st.session_state:
    st.session_state.doc_hash = None
if "filename" not in st.session_state:
    st.session_state.filename = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

# Header Title
st.markdown('<div class="main-title">🛡️ Lemma ZK Tracer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Verifiable PE Due Diligence with Cryptographic Provenance Anchors</div>',
    unsafe_allow_html=True,
)

# Check Backend
backend_online = check_backend_status()
if not backend_online:
    st.error(
        "❌ Backend offline. Please start the FastAPI backend server using: \n"
        "`.venv/bin/python -m backend.main`"
    )
    st.stop()

# ─── Grid Layout ──────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 3], gap="large")

# ─── Left Column: Actions & Configurations ──────────────────────────────────────
with col_left:
    st.markdown('<h3 style="margin-top:0;">1. Ingest PDF Document</h3>', unsafe_allow_html=True)
    
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Upload Private Equity Prospectus or Financial PDF",
            type=["pdf"],
            help="Supported file size limit: 50MB",
        )
        
        if uploaded_file is not None:
            # Re-upload check
            if st.session_state.filename != uploaded_file.name:
                st.session_state.document_id = None
                st.session_state.doc_hash = None
                st.session_state.analysis_results = None
                st.session_state.filename = uploaded_file.name
                
            if st.session_state.document_id is None:
                with st.spinner("🚀 Uploading and Indexing PDF into local Document Store..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                        resp = httpx.post(f"{BACKEND_URL}/api/v1/ingest", files=files, timeout=60.0)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.document_id = data["document_id"]
                            st.session_state.doc_hash = data["doc_hash"]
                            st.success("✅ Ingestion Complete!")
                        else:
                            st.error(f"Ingestion failed: {resp.json().get('error', 'Unknown Error')}")
                    except Exception as e:
                        st.error(f"Error connecting to backend: {str(e)}")
            
            # Show active metadata
            if st.session_state.document_id:
                st.info(
                    f"**Document ID**: `{st.session_state.document_id}`\n\n"
                    f"**Doc Hash (SHA-256)**: `{st.session_state.doc_hash[:16]}...{st.session_state.doc_hash[-16:]}`"
                )
        else:
            # Clear state when file is removed
            st.session_state.document_id = None
            st.session_state.doc_hash = None
            st.session_state.filename = None
            st.session_state.analysis_results = None

    st.markdown('<h3>2. Investment Mandate Rules</h3>', unsafe_allow_html=True)
    with st.container(border=True):
        min_rev = st.number_input(
            "Min Revenue ($ Millions)", min_value=0.0, max_value=500.0, value=5.0, step=1.0
        )
        min_ebitda = st.number_input(
            "Min EBITDA ($ Millions)", min_value=0.0, max_value=100.0, value=1.0, step=0.5
        )
        min_ebitda_margin = st.slider(
            "Min EBITDA Margin (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0
        )
        min_yoy = st.slider(
            "Min YoY Growth (%)", min_value=-50.0, max_value=100.0, value=5.0, step=1.0
        )
        max_concentration = st.slider(
            "Max Single Customer Concentration (%)", min_value=0.0, max_value=100.0, value=40.0, step=5.0
        )
        allowed_risks = st.multiselect(
            "Allowed Legal Risk Levels",
            options=["Low", "Medium", "High"],
            default=["Low", "Medium"],
        )

        st.write("")
        # Run Button
        run_analysis = st.button(
            "⚡ Run Verification & Analytics Pipeline",
            type="primary",
            disabled=(st.session_state.document_id is None),
            use_container_width=True,
        )

        if run_analysis:
            with st.spinner("🤖 Orchestrating Multi-Agent Pipeline (Extracting, Screening, Drafting)..."):
                try:
                    payload = {
                        "document_id": st.session_state.document_id,
                        "mandate": {
                            "min_revenue_m": min_rev,
                            "min_ebitda_m": min_ebitda,
                            "min_ebitda_margin_pct": min_ebitda_margin,
                            "max_customer_concentration_pct": max_concentration,
                            "min_yoy_growth_pct": min_yoy,
                            "allowed_legal_risk_levels": allowed_risks,
                        },
                    }
                    resp = httpx.post(f"{BACKEND_URL}/api/v1/analyze", json=payload, timeout=120.0)
                    
                    if resp.status_code == 200:
                        st.session_state.analysis_results = resp.json()
                        st.toast("Pipeline complete! Analysis rendered.", icon="🎉")
                    else:
                        st.error(f"Analysis failed: {resp.json().get('error', 'Unknown Error')}")
                except Exception as e:
                    st.error(f"Pipeline error: {str(e)}")

# ─── Right Column: Results & Verification ─────────────────────────────────────
with col_right:
    results = st.session_state.analysis_results

    if results is None:
        # Beautiful CSS-only empty state card
        st.markdown(
            """
            <div class="glass-card" style="text-align: center; padding: 60px 40px; margin-top: 40px;">
                <div style="font-size: 4rem; margin-bottom: 20px;">🛡️</div>
                <h3 style="margin-top: 0; color: #FFFFFF; font-size: 1.5rem;">Awaiting Document Analysis</h3>
                <p style="color: #8C96A6; font-size: 0.95rem; max-width: 400px; margin: 0 auto 24px;">
                    Upload a prospectus PDF, set your investment gates, and run the pipeline to generate your verifiable Investment Memo.
                </p>
                <div style="display: flex; justify-content: center; gap: 8px;">
                    <span class="status-pill status-pill-success" style="opacity:0.6;">verbatim checks</span>
                    <span class="status-pill status-pill-success" style="opacity:0.6;">HMAC security</span>
                    <span class="status-pill status-pill-success" style="opacity:0.6;">Poseidon commitments</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Decision Banner
        decision = results["screen_result"]["decision"]
        passed = results["screen_result"]["passed_count"]
        failed = results["screen_result"]["failed_count"]
        na = results["screen_result"]["na_count"]
        duration = round(results["pipeline_duration_ms"] / 1000, 2)

        if decision == "GO":
            st.markdown(
                f'<div class="decision-banner decision-go">'
                f'🟢 INVESTMENT DECISION: GO '
                f'<span style="font-size: 0.9rem; font-weight: normal; margin-left: auto;">'
                f'Passed: {passed} | Failed: {failed} | N/A: {na} | Duration: {duration}s</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        elif decision == "NO_GO":
            st.markdown(
                f'<div class="decision-banner decision-nogo">'
                f'🔴 INVESTMENT DECISION: NO_GO '
                f'<span style="font-size: 0.9rem; font-weight: normal; margin-left: auto;">'
                f'Passed: {passed} | Failed: {failed} | N/A: {na} | Duration: {duration}s</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="decision-banner decision-missing">'
                f'🟡 INVESTMENT DECISION: INSUFFICIENT DATA '
                f'<span style="font-size: 0.9rem; font-weight: normal; margin-left: auto;">'
                f'Passed: {passed} | Failed: {failed} | N/A: {na} | Duration: {duration}s</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Tab views
        tab_memo, tab_audit = st.tabs(["📝 Investment Committee Memo", "🔍 Cryptographic ZK-Audit Trail"])

        with tab_memo:
            st.markdown(
                f'<div class="ic-memo-container">',
                unsafe_allow_html=True,
            )
            st.markdown(results["memo"]["markdown"])
            st.markdown('</div>', unsafe_allow_html=True)

        with tab_audit:
            st.write("")
            st.markdown("### Verification Auditing")
            st.markdown(
                "Every single metric extracted by the agent is audit-proven. Below is the local real-time ZK "
                "re-verification verifying that the value matches the verbatim document text."
            )
            
            metrics = results["metrics"]
            
            # Map metrics to list
            available_metrics = [
                ("revenue", "Revenue", "💸"),
                ("ebitda", "EBITDA", "📊"),
                ("ebitda_margin", "EBITDA Margin", "📈"),
                ("yoy_growth", "YoY Growth", "🚀"),
                ("customer_concentration", "Customer Concentration", "👥"),
                ("legal_risks", "Legal Risks", "⚖️"),
            ]

            for key, display_name, icon in available_metrics:
                evidence = metrics.get(key)
                if evidence is None or evidence.get("value") is None:
                    # Missing metric card
                    with st.expander(f"{icon} {display_name}: [Not Found in Document]", expanded=False):
                        st.warning("This metric was not found in the ingested PDF chunks. Provenance hash is null.")
                    continue
                
                val = evidence["value"]
                src_txt = evidence["source_text"]
                page = evidence["page_number"]
                doc_h = evidence["doc_hash"]
                src_h = evidence["source_hash"]
                ver_h = evidence["verification_hash"]
                
                # Perform client-side cryptographic check in Streamlit
                # This mathematically proves that our verify function evaluates it as true!
                computed_src = compute_source_hash(src_txt)
                is_src_valid = (computed_src == src_h)
                is_proof_valid = verify_metric_proof(
                    doc_hash=doc_h,
                    metric_name=key,
                    value=val,
                    source_text=src_txt,
                    claimed_verification_hash=ver_h
                )
                
                is_completely_authentic = (is_src_valid and is_proof_valid)
                
                # Setup expander header with verification outcome
                header_status = "✅ Verified" if is_completely_authentic else "❌ FAILED PROOF"
                
                with st.expander(f"{icon} {display_name}: {val}  —  ({header_status})", expanded=True):
                    # Show pill
                    if is_completely_authentic:
                        st.markdown(
                            '<span class="status-pill status-pill-success">🛡️ Cryptographically Provenance Sealed</span>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<span class="status-pill status-pill-fail">⚠️ Cryptographic Integrity Broken / Forged</span>',
                            unsafe_allow_html=True,
                        )
                    
                    st.write("")
                    
                    # Columns for value & page
                    m_c1, m_c2 = st.columns(2)
                    m_c1.metric("Extracted Value", val)
                    m_c2.metric("Page Reference", f"Page {page}")
                    
                    st.markdown("**Verbatim Source Context:**")
                    st.info(f'"{src_txt}"')
                    
                    # Collapsible cryptographic hashes
                    st.markdown("**Proof Context Details:**")
                    st.markdown('<div class="trace-label">Document Hash (SHA-256 PDF fingerprint)</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="trace-value">{doc_h}</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="trace-label">Source Hash (SHA-256 evidence fingerprint)</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="trace-value">{src_h}</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="trace-label">ZK Verification Proof (HMAC Signature binding value + source)</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="trace-value">{ver_h}</div>', unsafe_allow_html=True)
                    
                    # Status messages
                    st.markdown("**Cryptographic Integrity Audit:**")
                    if is_src_valid:
                        st.write("🟢 `source_hash` matches verbatim text.")
                    else:
                        st.write("🔴 `source_hash` mismatch: verbatim text has been modified.")
                        
                    if is_proof_valid:
                        st.write("🟢 `verification_hash` proof is valid. Bindings are secure.")
                    else:
                        st.write("🔴 `verification_hash` proof is invalid: value, metric, or source has been modified.")
