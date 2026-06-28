import streamlit as st

from components.landing import show_landing
from components.dashboard import show_dashboard
from components.loader import show_ingest_loader, show_analysis_loader
from data.mock_data import mock_data
from services.api import upload_pdf as upload_pdf_api, analyze_document, map_backend_response_to_ui

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Verifiable Due Diligence Tracer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Load CSS ----------------
def load_css():
    try:
        with open("assets/style.css") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )
    except FileNotFoundError:
        pass

load_css()

# ---------------- Session State ----------------
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = False

if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "upload"

if "mandate" not in st.session_state:
    st.session_state.mandate = None

if "document_id" not in st.session_state:
    st.session_state.document_id = None

# ---------------- Sidebar ----------------
with st.sidebar:

    st.title("📊 Pipeline Control")
    
    if st.button("🏠 Upload Screen / Home", key="sidebar_home_btn"):
        st.session_state.uploaded_file = None
        st.session_state.show_dashboard = False
        st.session_state.analysis_data = None
        st.session_state.current_page = "upload"
        st.rerun()

    st.divider()

    # Step 1 status
    if st.session_state.current_page in ["loading_analyze", "dashboard"]:
        st.success("✅ PDF Uploaded")
    elif st.session_state.current_page == "loading_ingest":
        st.info("⏳ Uploading to Lemma...")
    else:
        st.info("⏳ Waiting for PDF")

    # Step 2 status
    if st.session_state.current_page == "dashboard":
        st.success("✅ Hash Generated")
        st.success("✅ Revenue Extracted")
        st.success("✅ EBITDA Extracted")
        st.success("✅ Investment Memo Generated")
    elif st.session_state.current_page == "loading_analyze":
        st.info("⏳ Analyzing metrics...")
    else:
        st.info("⏳ Waiting for Analysis")

    st.divider()
    st.subheader("⚙️ Mandate Thresholds")
    min_revenue = st.slider("Min Revenue ($M)", min_value=1.0, max_value=500.0, value=5.0, step=1.0)
    min_ebitda = st.slider("Min EBITDA ($M)", min_value=0.1, max_value=100.0, value=1.0, step=0.1)
    min_ebitda_margin = st.slider("Min EBITDA Margin (%)", min_value=1.0, max_value=100.0, value=10.0, step=1.0)
    max_cust_conc = st.slider("Max Customer Concentration (%)", min_value=5.0, max_value=100.0, value=40.0, step=1.0)
    min_growth = st.slider("Min YoY Growth (%)", min_value=1.0, max_value=100.0, value=5.0, step=1.0)

    if st.session_state.current_page == "dashboard":
        st.divider()
        if st.button("🔄 Reset / Analyze New PDF"):
            st.session_state.uploaded_file = None
            st.session_state.show_dashboard = False
            st.session_state.analysis_data = None
            st.session_state.current_page = "upload"
            st.rerun()

# ---------------- Page Router ----------------
if st.session_state.current_page == "upload":
    uploaded_file = show_landing()

    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        st.success(f"📄 Ready to Analyze: {uploaded_file.name}")

        if st.button("🚀 Generate Investment Memo"):
            st.session_state.mandate = {
                "min_revenue_m": float(min_revenue),
                "min_ebitda_m": float(min_ebitda),
                "min_ebitda_margin_pct": float(min_ebitda_margin),
                "max_customer_concentration_pct": float(max_cust_conc),
                "min_yoy_growth_pct": float(min_growth),
                "allowed_legal_risk_levels": ["Low", "Medium"]
            }
            st.session_state.current_page = "loading_ingest"
            st.rerun()

elif st.session_state.current_page == "loading_ingest":
    show_ingest_loader()
    
    # 1. Upload & Ingest
    ingest_res = upload_pdf_api(st.session_state.uploaded_file)
    if ingest_res:
        st.session_state.document_id = ingest_res["document_id"]
        st.session_state.current_page = "loading_analyze"
        st.rerun()
    else:
        st.error("❌ Failed to ingest the PDF. Check backend logs.")
        if st.button("↩ Go Back"):
            st.session_state.current_page = "upload"
            st.rerun()

elif st.session_state.current_page == "loading_analyze":
    show_analysis_loader()
    
    # 2. Analyze Document with Mandate
    analyze_res = analyze_document(st.session_state.document_id, st.session_state.mandate)
    if analyze_res:
        # 3. Map backend response to UI
        mapped_data = map_backend_response_to_ui(analyze_res, st.session_state.uploaded_file)
        st.session_state.analysis_data = mapped_data
        st.session_state.show_dashboard = True
        st.session_state.current_page = "dashboard"
        st.rerun()
    else:
        st.error("❌ Failed to analyze the document. Check backend logs.")
        if st.button("↩ Go Back"):
            st.session_state.current_page = "upload"
            st.rerun()

elif st.session_state.current_page == "dashboard":
    show_dashboard(
        st.session_state.uploaded_file,
        st.session_state.analysis_data
    )
'''changes'''