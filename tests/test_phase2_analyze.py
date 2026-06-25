"""
tests/test_phase2_analyze.py
────────────────────────────
Phase 2 Test Gate: POST /api/v1/analyze
"""
from __future__ import annotations

import io
import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.agents.extractor import ExtractedFinancialMetrics, ExtractedMetric
from backend.agents.drafter import DraftedMemo, DraftedSection
from tests.test_phase1_ingest import build_minimal_pdf


# ─── Mock Data Generators ─────────────────────────────────────────────────────

def get_mock_extracted_metrics(
    revenue_val: str | None = "$10.0M",
    chunk_id: str = "mock-chunk-id"
) -> ExtractedFinancialMetrics:
    """Helper to return a mock parsed Pydantic response from LLM."""
    return ExtractedFinancialMetrics(
        revenue=ExtractedMetric(
            value=revenue_val,
            unit="M",
            source_text="Revenue was $10.0M" if revenue_val else None,
            page_number=1,
            chunk_id=chunk_id
        ),
        ebitda=ExtractedMetric(
            value="$6.0M",
            unit="M",
            source_text="EBITDA was $6.0M",
            page_number=1,
            chunk_id=chunk_id
        ),
        ebitda_margin=ExtractedMetric(
            value="60%",
            unit="%",
            source_text="EBITDA margin was 60%",
            page_number=1,
            chunk_id=chunk_id
        ),
        yoy_growth=ExtractedMetric(
            value="10%",
            unit="%",
            source_text="YoY Growth was 10%",
            page_number=1,
            chunk_id=chunk_id
        ),
        customer_concentration=ExtractedMetric(
            value="15%",
            unit="%",
            source_text="Customer Concentration was 15%",
            page_number=1,
            chunk_id=chunk_id
        ),
        legal_risks=ExtractedMetric(
            value="Low",
            unit=None,
            source_text="Legal Risks were Low",
            page_number=1,
            chunk_id=chunk_id
        ),
        net_income=ExtractedMetric(
            value="$4.0M",
            unit="M",
            source_text="Net income was $4.0M",
            page_number=1,
            chunk_id=chunk_id
        ),
        total_debt=ExtractedMetric(
            value="$2.0M",
            unit="M",
            source_text="Total debt was $2.0M",
            page_number=1,
            chunk_id=chunk_id
        ),
        free_cash_flow=ExtractedMetric(
            value="$3.0M",
            unit="M",
            source_text="Free cash flow was $3.0M",
            page_number=1,
            chunk_id=chunk_id
        )
    )


def get_mock_drafted_memo() -> DraftedMemo:
    """Helper to return a mock drafted IC memo response from LLM."""
    return DraftedMemo(
        executive_summary="Target company shows robust financial performance.",
        sections=[
            DraftedSection(
                title="Financial Performance Analysis",
                content="The target has strong revenues and stable operating margins.",
                evidence_refs=["revenue", "ebitda", "ebitda_margin"]
            ),
            DraftedSection(
                title="Risk & Debt Assessment",
                content="Customer concentration and debt loads are minimal.",
                evidence_refs=["customer_concentration", "total_debt"]
            )
        ]
    )


def build_rich_mock_pdf() -> bytes:
    """Helper to build a PDF containing all the target verbatim metric strings."""
    pdf_text = (
        "Revenue was $10.0M\n"
        "EBITDA was $6.0M\n"
        "EBITDA margin was 60%\n"
        "YoY Growth was 10%\n"
        "Customer Concentration was 15%\n"
        "Legal Risks were Low\n"
        "Net income was $4.0M\n"
        "Total debt was $2.0M\n"
        "Free cash flow was $3.0M"
    )
    return build_minimal_pdf(pdf_text)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """Async test client running with app lifespan context."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_garbage_document_id_returns_404(client):
    """Passing a non-existent document_id must return 404 clean JSON error."""
    garbage_id = str(uuid.uuid4())

    response = await client.post(
        "/api/v1/analyze",
        json={
            "document_id": garbage_id,
            "mandate": {}
        }
    )

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
    body = response.json()
    
    assert body["status"] == 404
    assert body["error"] == "Document not found"
    assert len(body["details"]) == 1
    assert body["details"][0]["code"] == "DOCUMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_analyze_happy_path(client):
    """Happy path: ingest PDF, mock LLM extraction & drafting → 200 OK with full response."""
    # 1. Ingest valid PDF with all verbatim target strings
    pdf_bytes = build_rich_mock_pdf()
    ingest_resp = await client.post(
        "/api/v1/ingest",
        files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert ingest_resp.status_code == 200
    doc_id = ingest_resp.json()["document_id"]
    doc_hash = ingest_resp.json()["doc_hash"]

    # Retrieve the actual chunk_id from store
    chunks = await app.state.document_store.get_all_chunks(doc_id)
    assert len(chunks) > 0
    real_chunk_id = chunks[0]["chunk_id"]

    # 2. Setup mock objects for OpenAI calls
    mock_extractor_response = AsyncMock()
    mock_extractor_response.choices = [AsyncMock()]
    mock_extractor_response.choices[0].message.parsed = get_mock_extracted_metrics(chunk_id=real_chunk_id)

    mock_drafter_response = AsyncMock()
    mock_drafter_response.choices = [AsyncMock()]
    mock_drafter_response.choices[0].message.parsed = get_mock_drafted_memo()

    # Patch AsyncOpenAI parse calls in both agents
    with patch("backend.agents.extractor.AsyncOpenAI") as mock_openai_extractor, \
         patch("backend.agents.drafter.AsyncOpenAI") as mock_openai_drafter:
        
        # Extractor client setup
        extractor_client = mock_openai_extractor.return_value
        extractor_client.beta.chat.completions.parse = AsyncMock(return_value=mock_extractor_response)
        
        # Drafter client setup
        drafter_client = mock_openai_drafter.return_value
        drafter_client.beta.chat.completions.parse = AsyncMock(return_value=mock_drafter_response)

        # 3. Request Analysis
        response = await client.post(
            "/api/v1/analyze",
            json={
                "document_id": doc_id,
                "mandate": {
                    "min_revenue_m": 5.0,
                    "min_ebitda_m": 1.0,
                    "min_ebitda_margin_pct": 10.0,
                    "max_customer_concentration_pct": 40.0,
                    "min_yoy_growth_pct": 5.0,
                    "allowed_legal_risk_levels": ["Low", "Medium"]
                }
            }
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        body = response.json()

        # Schema Verification
        assert body["document_id"] == doc_id
        assert body["filename"] == "report.pdf"
        assert "metrics" in body
        assert "screen_result" in body
        assert "memo" in body
        assert body["pipeline_duration_ms"] > 0
        assert "revenue" in body["metrics_found"]
        
        # Provenance Hashes Verification
        rev = body["metrics"]["revenue"]
        assert rev["value"] == "$10.0M"
        assert rev["doc_hash"] == doc_hash
        assert rev["source_hash"] is not None
        assert rev["verification_hash"] is not None
        
        # Screen Result Validation (Should be GO)
        assert body["screen_result"]["decision"] == "GO"
        assert body["screen_result"]["passed_count"] == 6
        assert body["screen_result"]["failed_count"] == 0
        
        # Memo Validation
        assert body["memo"]["executive_summary"] == "Target company shows robust financial performance."
        assert len(body["memo"]["sections"]) == 2
        assert "INVESTMENT COMMITTEE MEMO" in body["memo"]["markdown"]


@pytest.mark.asyncio
async def test_analyze_mandate_rejection_no_go(client):
    """Mandate violation: minimum revenue required is higher than actual → NO_GO decision."""
    # 1. Ingest
    pdf_bytes = build_rich_mock_pdf()
    ingest_resp = await client.post(
        "/api/v1/ingest",
        files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = ingest_resp.json()["document_id"]

    # Retrieve the actual chunk_id from store
    chunks = await app.state.document_store.get_all_chunks(doc_id)
    real_chunk_id = chunks[0]["chunk_id"]

    # 2. Setup mock
    mock_extractor_response = AsyncMock()
    mock_extractor_response.choices = [AsyncMock()]
    mock_extractor_response.choices[0].message.parsed = get_mock_extracted_metrics(
        revenue_val="$10.0M",
        chunk_id=real_chunk_id
    )

    mock_drafter_response = AsyncMock()
    mock_drafter_response.choices = [AsyncMock()]
    mock_drafter_response.choices[0].message.parsed = get_mock_drafted_memo()

    with patch("backend.agents.extractor.AsyncOpenAI") as mock_openai_extractor, \
         patch("backend.agents.drafter.AsyncOpenAI") as mock_openai_drafter:
        
        mock_openai_extractor.return_value.beta.chat.completions.parse = AsyncMock(return_value=mock_extractor_response)
        mock_openai_drafter.return_value.beta.chat.completions.parse = AsyncMock(return_value=mock_drafter_response)

        # 3. Analyze with high revenue requirement ($50M min vs actual $10M)
        response = await client.post(
            "/api/v1/analyze",
            json={
                "document_id": doc_id,
                "mandate": {
                    "min_revenue_m": 50.0  # actual is 10.0
                }
            }
        )

        assert response.status_code == 200
        body = response.json()

        # Must be NO_GO
        assert body["screen_result"]["decision"] == "NO_GO"
        
        # Verify specific gate failure
        revenue_flag = next(f for f in body["screen_result"]["flags"] if f["gate"] == "Revenue")
        assert revenue_flag["passed"] is False
        assert "fails to meet" in revenue_flag["reason"]


@pytest.mark.asyncio
async def test_analyze_mandate_insufficient_data(client):
    """Mandate evaluation with missing required data (value is null) → INSUFFICIENT_DATA decision."""
    # 1. Ingest
    pdf_bytes = build_rich_mock_pdf()
    ingest_resp = await client.post(
        "/api/v1/ingest",
        files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = ingest_resp.json()["document_id"]

    # Retrieve the actual chunk_id from store
    chunks = await app.state.document_store.get_all_chunks(doc_id)
    real_chunk_id = chunks[0]["chunk_id"]

    # 2. Setup mock with revenue missing (null)
    mock_extractor_response = AsyncMock()
    mock_extractor_response.choices = [AsyncMock()]
    mock_extractor_response.choices[0].message.parsed = get_mock_extracted_metrics(
        revenue_val=None,
        chunk_id=real_chunk_id
    )

    mock_drafter_response = AsyncMock()
    mock_drafter_response.choices = [AsyncMock()]
    mock_drafter_response.choices[0].message.parsed = get_mock_drafted_memo()

    with patch("backend.agents.extractor.AsyncOpenAI") as mock_openai_extractor, \
         patch("backend.agents.drafter.AsyncOpenAI") as mock_openai_drafter:
        
        mock_openai_extractor.return_value.beta.chat.completions.parse = AsyncMock(return_value=mock_extractor_response)
        mock_openai_drafter.return_value.beta.chat.completions.parse = AsyncMock(return_value=mock_drafter_response)

        # 3. Analyze
        response = await client.post(
            "/api/v1/analyze",
            json={
                "document_id": doc_id,
                "mandate": {}
            }
        )

        assert response.status_code == 200
        body = response.json()

        # Must be INSUFFICIENT_DATA
        assert body["screen_result"]["decision"] == "INSUFFICIENT_DATA"
        
        # Verify specific gate status
        revenue_flag = next(f for f in body["screen_result"]["flags"] if f["gate"] == "Revenue")
        assert revenue_flag["passed"] is False
        assert revenue_flag["actual"] is None
        assert "missing" in revenue_flag["reason"].lower()
