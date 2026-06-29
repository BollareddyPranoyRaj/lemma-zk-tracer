import requests
import pypdf
import io

BASE_URL = "http://127.0.0.1:8000"

def upload_pdf(file):
    files = {
        "file": (
            file.name,
            file,
            "application/pdf"
        )
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/ingest",
        files=files
    )

    if response.status_code == 200:
        return response.json()

    return None

def analyze_document(document_id, mandate=None):
    payload = {
        "document_id": document_id
    }
    if mandate:
        payload["mandate"] = mandate

    response = requests.post(
        f"{BASE_URL}/api/v1/analyze",
        json=payload
    )

    if response.status_code == 200:
        return response.json()

    return None

def map_backend_response_to_ui(analyze_res, uploaded_file):
    company = "General Enterprise"
    sector = "General / Diversified"

    try:
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        uploaded_file.seek(0)  # reset pointer for other uses

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        if reader.pages:
            first_page_text = reader.pages[0].extract_text()
            lines = [line.strip() for line in first_page_text.split("\n") if line.strip()]
            if lines:
                company = lines[0]
                if len(company) > 100:
                    company = company[:100] + "..."

            full_text = "".join([page.extract_text() for page in reader.pages[:2]]).lower()
            if "saas" in full_text or "software" in full_text:
                sector = "Software / SaaS"
            elif "healthcare" in full_text or "medical" in full_text:
                sector = "Healthcare"
            elif "fintech" in full_text or "finance" in full_text:
                sector = "Fintech"
            elif "energy" in full_text or "solar" in full_text:
                sector = "Energy / CleanTech"
    except Exception as e:
        print(f"Error extracting metadata from PDF: {e}")

    metrics = analyze_res["metrics"]
    screen_result = analyze_res["screen_result"]
    memo = analyze_res["memo"]

    # Extract specific values
    rev_val = metrics.get("revenue", {}).get("value") or "N/A"
    eb_val = metrics.get("ebitda", {}).get("value") or "N/A"
    growth_val = metrics.get("yoy_growth", {}).get("value") or "N/A"
    risk_val = metrics.get("legal_risks", {}).get("value") or "Low"

    # Map verification
    verification = {}
    for ui_key, backend_key in [("Revenue", "revenue"), ("EBITDA", "ebitda"), ("Growth", "yoy_growth")]:
        m_ev = metrics.get(backend_key) or {}
        val = m_ev.get("value")
        v_hash = m_ev.get("verification_hash")

        verification[ui_key] = {
            "page": m_ev.get("page_number") or 1,
            "hash": v_hash or "",
            "source": m_ev.get("source_text") or "",
            "verified": bool(v_hash and val)
        }

    passed = screen_result.get("passed_count", 0)
    failed = screen_result.get("failed_count", 0)
    total = passed + failed
    ai_score = int((passed / total) * 100) if total > 0 else 0

    return {
        "company": company,
        "sector": sector,
        "decision": screen_result["decision"],
        "confidence": 95 if screen_result["decision"] == "GO" else 85,
        "ai_score": ai_score,
        "metrics": {
            "Revenue": rev_val,
            "EBITDA": eb_val,
            "Growth": growth_val,
            "Industry": sector,
            "Risk": risk_val
        },
        "verification": verification,
        "executive_summary": memo["executive_summary"]
    }