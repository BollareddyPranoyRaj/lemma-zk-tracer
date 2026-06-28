import streamlit as st

def show_ingest_loader():
    st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 48px; margin: 60px auto; max-width: 620px; border-radius: 8px; background: var(--bg-dark-2); border: 1px solid var(--border-subtle);">
            <div style="margin-bottom: 24px; display: flex; justify-content: center;">
                <svg class="animate-spin" style="animation: spin 1.2s linear infinite; color: var(--color-brand);" xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" style="opacity: 0.15;"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" style="opacity: 0.85;"></path>
                </svg>
            </div>
            <h4 style="margin: 0 0 8px 0; color: var(--text-primary); font-size: 18px; letter-spacing: -0.01em;">INGESTING DOCUMENT</h4>
            <p style="margin: 0; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">Uploading and parsing PDF to Lemma Pod datastore... This parses the layout structure and generates semantic vector embeddings.</p>
        </div>
        <style>
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
        </style>
    """, unsafe_allow_html=True)

def show_analysis_loader():
    st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 48px; margin: 60px auto; max-width: 620px; border-radius: 8px; background: var(--bg-dark-2); border: 1px solid var(--border-subtle);">
            <div style="margin-bottom: 24px; display: flex; justify-content: center;">
                <svg class="animate-spin" style="animation: spin 1.2s linear infinite; color: var(--color-success);" xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" style="opacity: 0.15;"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" style="opacity: 0.85;"></path>
                </svg>
            </div>
            <h4 style="margin: 0 0 8px 0; color: var(--text-primary); font-size: 18px; letter-spacing: -0.01em;">RUNNING MULTI-AGENT COMPLIANCE</h4>
            <p style="margin: 0; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">Retrieving semantic contexts from vector search and orchestrating Extractor, Screener, and Drafter agents to check thresholds and construct memo.</p>
        </div>
        <style>
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
        </style>
    """, unsafe_allow_html=True)