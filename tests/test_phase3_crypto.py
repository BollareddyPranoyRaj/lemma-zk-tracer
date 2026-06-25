"""
tests/test_phase3_crypto.py
────────────────────────────
Phase 3 Test Gate: Cryptographic Provenance and Proof Soundness
"""
from __future__ import annotations

import io
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.crypto import (
    compute_source_hash,
    compute_verification_hash,
    verify_metric_proof,
    poseidon_commitment,
    _BN254_PRIME
)
from backend.agents.extractor import ExtractedFinancialMetrics
from backend.agents.drafter import DraftedMemo
from tests.test_phase1_ingest import build_minimal_pdf
from tests.test_phase2_analyze import (
    build_rich_mock_pdf,
    get_mock_extracted_metrics,
    get_mock_drafted_memo
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """Async test client running with app lifespan context."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# ─── Tests ────────────────────────────────────────────────────────────────────

def test_source_hash_calculation():
    """Verifies that source hash is the correct SHA-256 of the text."""
    source_text = "Revenue was $10.0M in FY25"
    expected = "7b1184901ff5dddfcfb1da261f617d0e7131425aca10949d78eb680293188c50"
    assert compute_source_hash(source_text) == expected


def test_hmac_proof_soundness_and_anti_forgery():
    """
    Mathematical verification of proof soundness.
    Altering any single input must invalidate the verification_hash.
    """
    doc_hash = "a" * 64
    metric = "revenue"
    value = "$10.0M"
    source = "Revenue was $10.0M"

    # Compute a valid verification hash
    v_hash = compute_verification_hash(doc_hash, metric, value, source)
    assert len(v_hash) == 64

    # Verify happy path (valid inputs)
    assert verify_metric_proof(doc_hash, metric, value, source, v_hash) is True

    # Attack 1: Alter the value (e.g. attempting to inflate revenue from $10M to $11M)
    assert verify_metric_proof(doc_hash, metric, "$11.0M", source, v_hash) is False

    # Attack 2: Alter the source text (attempting to change evidence)
    assert verify_metric_proof(doc_hash, metric, value, "Revenue was $11.0M", v_hash) is False

    # Attack 3: Alter the metric name (attempting to map revenue to ebitda)
    assert verify_metric_proof(doc_hash, "ebitda", value, source, v_hash) is False

    # Attack 4: Alter the doc_hash (attempting to associate proof with another PDF)
    assert verify_metric_proof("b" * 64, metric, value, source, v_hash) is False

    # Attack 5: Alter the verification_hash itself (forged proof)
    assert verify_metric_proof(doc_hash, metric, value, source, "c" * 64) is False


def test_poseidon_reference_sponge():
    """
    Verifies that the BN254 Poseidon reference commitment sponge works:
      - Outputs are deterministic.
      - Outputs represent valid scalar field elements (less than the BN254 prime).
    """
    elements = [100, 200, 300]
    
    # 1. Determinism
    h1 = poseidon_commitment(elements)
    h2 = poseidon_commitment(elements)
    assert h1 == h2

    # 2. Modulo Prime Field constraint
    assert h1 < _BN254_PRIME
    assert h1 > 0

    # 3. Collision resistance for simple swap
    h3 = poseidon_commitment([200, 100, 300])
    assert h1 != h3


@pytest.mark.asyncio
async def test_end_to_end_api_provenance(client):
    """
    Verifies that the API returned responses contain valid, verifiable proofs
    for all extracted metrics.
    """
    # 1. Ingest PDF
    pdf_bytes = build_rich_mock_pdf()
    ingest_resp = await client.post(
        "/api/v1/ingest",
        files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert ingest_resp.status_code == 200
    doc_id = ingest_resp.json()["document_id"]
    doc_hash = ingest_resp.json()["doc_hash"]

    # Get real chunk ID
    chunks = await app.state.document_store.get_all_chunks(doc_id)
    real_chunk_id = chunks[0]["chunk_id"]

    # 2. Mock LLM
    mock_extractor_response = AsyncMock()
    mock_extractor_response.choices = [AsyncMock()]
    mock_extractor_response.choices[0].message.parsed = get_mock_extracted_metrics(chunk_id=real_chunk_id)

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
        metrics = body["metrics"]

        # 4. Mathematically audit every single extracted metric in the response
        for metric_name in ["revenue", "ebitda", "ebitda_margin", "yoy_growth"]:
            evidence = metrics[metric_name]
            
            assert evidence["doc_hash"] == doc_hash
            assert evidence["source_hash"] == compute_source_hash(evidence["source_text"])
            
            # Cryptographic verification check
            is_valid = verify_metric_proof(
                doc_hash=doc_hash,
                metric_name=metric_name,
                value=evidence["value"],
                source_text=evidence["source_text"],
                claimed_verification_hash=evidence["verification_hash"]
            )
            assert is_valid is True, f"Failed proof verification for metric: {metric_name}"
