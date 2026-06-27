import streamlit as st

def show_landing():
    # 1. Hero Content
    st.markdown("""
        <div style="text-align: center; padding: 40px 0 20px 0;">
            <div style="display: inline-block; background: rgba(130, 81, 238, 0.12); border: 1px solid rgba(130, 81, 238, 0.25); border-radius: 99px; padding: 6px 16px; margin-bottom: 24px;">
                <span style="color: #A37EF5; font-size: 13px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">
                    ⚡ BINOCS HACKATHON BUILD
                </span>
            </div>
            <h1 style="font-size: 54px; margin-bottom: 16px; background: linear-gradient(135deg, #FFFFFF 0%, #A37EF5 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Verifiable Due Diligence Tracer
            </h1>
            <p style="font-size: 18px; max-width: 760px; margin: 0 auto 36px auto; color: #A1A1AA; line-height: 1.6;">
                Uncompromising precision for Private Equity. Automatically screen Confidential Information Memorandums (CIM) and prospectuses against investment mandates with cryptographically proven, zero-hallucination metrics.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. Main Call-to-Action Button (centered using columns)
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        if st.button("🚀 Launch Analyzer App", key="launch_app_landing"):
            st.session_state.current_page = "upload"
            st.rerun()

    # 3. Interactive UI Visual Sandbox (Mockup representation of ZK proof provenance)
    st.markdown("""
        <div style="margin: 50px 0;">
            <div class="glass-card" style="padding: 30px;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 16px; margin-bottom: 20px;">
                    <div>
                        <h4 style="margin: 0; color: #FFFFFF; font-size: 18px;">PROVABLE METRIC COMPLIANCE ENGINE</h4>
                        <p style="margin: 4px 0 0 0; font-size: 13px; color: #71717A;">Interactive Verification Pipeline</p>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <span style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.2); color: #10B981; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 6px;">Lemma Active</span>
                        <span style="background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.2); color: #3B82F6; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 6px;">HMAC Provable</span>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.05); padding: 16px; border-radius: 10px;">
                        <span style="color: #8251EE; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">STEP 01</span>
                        <h5 style="margin: 8px 0 4px 0; color: white; font-size: 15px;">Vector Search</h5>
                        <p style="margin: 0; font-size: 13px; color: #A1A1AA;">Semantic queries identify key pages and candidate sections dynamically from the Lemma Platform pod storage.</p>
                    </div>
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.05); padding: 16px; border-radius: 10px;">
                        <span style="color: #8251EE; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">STEP 02</span>
                        <h5 style="margin: 8px 0 4px 0; color: white; font-size: 15px;">ZK Verbatim Verification</h5>
                        <p style="margin: 0; font-size: 13px; color: #A1A1AA;">The extractor verifies that values exist exactly in the retrieved document text before computing cryptographic hashes.</p>
                    </div>
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.05); padding: 16px; border-radius: 10px;">
                        <span style="color: #8251EE; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">STEP 03</span>
                        <h5 style="margin: 8px 0 4px 0; color: white; font-size: 15px;">Mandate Screener</h5>
                        <p style="margin: 0; font-size: 13px; color: #A1A1AA;">Metrics are screened against active LP covenants. A provable GO/NO-GO memo report is generated.</p>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 4. Capabilities / Feature Grid (Pure SVG icons)
    st.markdown("""
        <div style="margin: 40px 0;">
            <h3 style="text-align: center; margin-bottom: 40px; font-size: 28px;">Core System Capabilities</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px;">
                
                <!-- Card 1 -->
                <div class="glass-card">
                    <div class="icon-box">
                        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        </svg>
                    </div>
                    <h4 style="margin: 0 0 10px 0; font-size: 18px; color: white;">Tamper-Proof Provenance</h4>
                    <p style="margin: 0; font-size: 14px; color: #A1A1AA;">
                        Every data extraction is sealed using HMAC-SHA256 signatures, binding the document signature directly to the LLM outputs.
                    </p>
                </div>
                
                <!-- Card 2 -->
                <div class="glass-card">
                    <div class="icon-box">
                        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <ellipse cx="12" cy="5" rx="9" ry="3"/>
                            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                            <path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/>
                        </svg>
                    </div>
                    <h4 style="margin: 0 0 10px 0; font-size: 18px; color: white;">Lemma Datastore Mode</h4>
                    <p style="margin: 0; font-size: 14px; color: #A1A1AA;">
                        Native integration with Gappy AI's Lemma platform, utilizing pod file-search, status polling, and structured schema record writes.
                    </p>
                </div>
                
                <!-- Card 3 -->
                <div class="glass-card">
                    <div class="icon-box">
                        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="20" x2="18" y2="10"/>
                            <line x1="12" y1="20" x2="12" y2="4"/>
                            <line x1="6" y1="20" x2="6" y2="14"/>
                        </svg>
                    </div>
                    <h4 style="margin: 0 0 10px 0; font-size: 18px; color: white;">Dynamic Screener Gates</h4>
                    <p style="margin: 0; font-size: 14px; color: #A1A1AA;">
                        Configure financial rules on the fly (revenue, growth, customer concentration). The pipeline dynamically checks thresholds and outputs visual decisions.
                    </p>
                </div>
                
            </div>
        </div>
    """, unsafe_allow_html=True)