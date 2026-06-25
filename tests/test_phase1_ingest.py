"""
tests/test_phase1_ingest.py
────────────────────────────
Phase 1 Test Gate: POST /api/v1/ingest

Tests:
  1. Happy path  — upload a minimal valid PDF → 200 OK with valid document_id + doc_hash
  2. Non-PDF     — upload a text file → 400 INVALID_CONTENT_TYPE
  3. Oversized   — upload a 51MB payload → 400 FILE_TOO_LARGE
  4. Fake PDF    — correct extension but not real PDF → 400 INVALID_PDF_MAGIC
  5. doc_hash    — verify SHA-256 of the raw bytes matches response
  6. Idempotency — upload the same PDF twice, get different document_ids (new UUID each time)
"""
from __future__ import annotations

import hashlib
import io
import struct
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# We need the app but NOT a running server
from backend.main import app


# ─── Minimal valid PDF builder ────────────────────────────────────────────────

def build_minimal_pdf(content: str = "Revenue was $10M\nEBITDA was $6M") -> bytes:
    """
    Build a standards-compliant minimal PDF with one page of text.
    No external libs needed — raw bytes construction.
    This is a REAL parseable PDF (pdfplumber can open it).
    """
    body = b"%PDF-1.4\n"

    # Object 1: Catalog
    obj1_offset = len(body)
    body += b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"

    # Object 2: Pages
    obj2_offset = len(body)
    body += b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"

    # Object 4: Font
    obj4_offset = len(body)
    body += (
        b"4 0 obj\n"
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"
        b"endobj\n"
    )

    # Object 5: Content stream
    stream_content = (
        f"BT /F1 12 Tf 50 750 Td ({content}) Tj ET"
    ).encode()
    obj5_offset = len(body)
    body += (
        f"5 0 obj\n<< /Length {len(stream_content)} >>\nstream\n".encode()
        + stream_content
        + b"\nendstream\nendobj\n"
    )

    # Object 3: Page
    obj3_offset = len(body)
    body += (
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> "
        b"/Contents 5 0 R >>\n"
        b"endobj\n"
    )

    # Cross-reference table
    xref_offset = len(body)
    offsets = [obj1_offset, obj2_offset, obj3_offset, obj4_offset, obj5_offset]
    body += b"xref\n"
    body += f"0 6\n".encode()
    body += b"0000000000 65535 f \n"
    for off in offsets:
        body += f"{off:010d} 00000 n \n".encode()

    # Trailer
    body += (
        f"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()

    return body


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """Async test client — spins up the full FastAPI app in-process."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_valid_pdf_returns_200(client):
    """Happy path: upload a valid PDF → 200 OK with document_id + doc_hash."""
    pdf_bytes = build_minimal_pdf()

    response = await client.post(
        "/api/v1/ingest",
        files={"file": ("test_report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()

    # Required fields
    assert "document_id" in body
    assert "doc_hash" in body
    assert "total_chunks" in body
    assert "status" in body

    # document_id must be a valid UUID
    parsed = uuid.UUID(body["document_id"])  # raises ValueError if invalid
    assert str(parsed) == body["document_id"]

    # doc_hash must be a 64-char hex string (SHA-256)
    assert len(body["doc_hash"]) == 64
    assert all(c in "0123456789abcdef" for c in body["doc_hash"])

    # Status must be 'complete'
    assert body["status"] == "complete"

    # At least one chunk must have been created
    assert body["total_chunks"] >= 1


@pytest.mark.asyncio
async def test_ingest_doc_hash_matches_sha256(client):
    """doc_hash in response must equal SHA-256 of the uploaded bytes."""
    pdf_bytes = build_minimal_pdf("Unique content for hash test")
    expected_hash = hashlib.sha256(pdf_bytes).hexdigest()

    response = await client.post(
        "/api/v1/ingest",
        files={"file": ("hash_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["doc_hash"] == expected_hash, (
        f"Hash mismatch: expected {expected_hash}, got {body['doc_hash']}"
    )


@pytest.mark.asyncio
async def test_ingest_non_pdf_returns_400(client):
    """Uploading a text file should return 400 with INVALID_CONTENT_TYPE."""
    text_content = b"This is not a PDF file at all."

    response = await client.post(
        "/api/v1/ingest",
        files={"file": ("report.txt", io.BytesIO(text_content), "text/plain")},
    )

    assert response.status_code == 400
    body = response.json()
    assert "error" in body or "detail" in body


@pytest.mark.asyncio
async def test_ingest_fake_pdf_magic_bytes_returns_400(client):
    """A file with .pdf extension but wrong magic bytes → 400 INVALID_PDF_MAGIC."""
    fake_pdf = b"NOT_A_PDF_JUST_GARBAGE_CONTENT" * 10

    response = await client.post(
        "/api/v1/ingest",
        files={"file": ("fake.pdf", io.BytesIO(fake_pdf), "application/pdf")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_ingest_oversized_file_returns_400(client):
    """File exceeding max_upload_mb (50MB) should return 400 FILE_TOO_LARGE."""
    # Build a valid PDF header but pad it to 51MB
    # (we need %PDF magic bytes to pass the magic check, so we pad AFTER the check point)
    # Actually: the size check happens BEFORE the magic check in our route.
    # So a 51MB file (any content) should hit the size limit first.
    fifty_one_mb = b"%PDF-1.4\n" + b"x" * (51 * 1024 * 1024)

    response = await client.post(
        "/api/v1/ingest",
        files={"file": ("huge.pdf", io.BytesIO(fifty_one_mb), "application/pdf")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_ingest_twice_returns_different_document_ids(client):
    """Same PDF uploaded twice → different document_ids (idempotency not enforced at this layer)."""
    pdf_bytes = build_minimal_pdf("Same content uploaded twice")

    r1 = await client.post(
        "/api/v1/ingest",
        files={"file": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    r2 = await client.post(
        "/api/v1/ingest",
        files={"file": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )

    assert r1.status_code == 200
    assert r2.status_code == 200

    id1 = r1.json()["document_id"]
    id2 = r2.json()["document_id"]
    assert id1 != id2, "Two uploads of the same PDF must get different document_ids"

    # But doc_hash MUST be the same (same bytes)
    assert r1.json()["doc_hash"] == r2.json()["doc_hash"]


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """GET /health → 200 with status=ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
