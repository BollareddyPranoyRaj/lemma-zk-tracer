"""
backend/routes/ingest.py
────────────────────────
POST /api/v1/ingest — PDF upload and document store ingestion.

Validation:
  • Rejects non-PDF content types
  • Enforces max file size (configurable)
  • Returns 422 on validation failure (Pydantic), 400 on bad input
  • Returns structured ErrorResponse on all failure paths
"""
from __future__ import annotations

import logging
import time

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from backend.config import get_settings
from backend.document_store import DocumentStore
from backend.dependencies import get_document_store
from backend.models import ErrorDetail, ErrorResponse, IngestResponse, IngestStatus

log = structlog.get_logger(__name__)
router = APIRouter()


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest a PDF into the document store",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file type or size"},
        500: {"model": ErrorResponse, "description": "Ingestion pipeline failure"},
    },
)
async def ingest_document(
    request: Request,
    file: UploadFile = File(..., description="PDF file to ingest"),
    store: DocumentStore = Depends(get_document_store),
) -> IngestResponse:
    """
    Upload a PDF file and store it in the semantic document store.

    Returns a `document_id` (UUID) and `doc_hash` (SHA-256 of raw bytes).
    Use the `document_id` in subsequent `/analyze` calls.
    """
    settings = get_settings()
    request_id = getattr(request.state, "request_id", None)
    t0 = time.perf_counter()

    # ── Validate content type ─────────────────────────────────────────────────
    content_type = file.content_type or ""
    is_pdf_mimetype = "pdf" in content_type.lower()
    is_pdf_extension = (file.filename or "").lower().endswith(".pdf")
    if not is_pdf_mimetype and not is_pdf_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                status=400,
                error="Invalid file type",
                details=[ErrorDetail(
                    code="INVALID_CONTENT_TYPE",
                    message=f"Expected PDF, got '{content_type}'. "
                            "Only PDF files are supported.",
                    field="file",
                )],
                request_id=request_id,
            ).model_dump(mode="json"),
        )

    # ── Read file bytes ───────────────────────────────────────────────────────
    pdf_bytes = await file.read()

    # ── Validate file size ────────────────────────────────────────────────────
    max_bytes = settings.max_upload_bytes
    if len(pdf_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                status=400,
                error="File too large",
                details=[ErrorDetail(
                    code="FILE_TOO_LARGE",
                    message=(
                        f"File size {len(pdf_bytes) / 1024 / 1024:.1f}MB exceeds "
                        f"maximum allowed {settings.max_upload_mb}MB."
                    ),
                    field="file",
                )],
                request_id=request_id,
            ).model_dump(mode="json"),
        )

    # ── Validate PDF magic bytes (anti-MIME spoofing) ─────────────────────────
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                status=400,
                error="Invalid PDF",
                details=[ErrorDetail(
                    code="INVALID_PDF_MAGIC",
                    message="File does not appear to be a valid PDF (missing %PDF header).",
                    field="file",
                )],
                request_id=request_id,
            ).model_dump(mode="json"),
        )

    filename = file.filename or "document.pdf"
    log.info(
        "Ingestion started",
        filename=filename,
        size_bytes=len(pdf_bytes),
        request_id=request_id,
    )

    # ── Run ingestion pipeline ────────────────────────────────────────────────
    try:
        result = await store.ingest(pdf_bytes=pdf_bytes, filename=filename)
    except Exception as exc:
        log.error("Ingestion pipeline failed", exc_info=exc, request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                status=500,
                error="Ingestion failed",
                details=[ErrorDetail(
                    code="PIPELINE_ERROR",
                    message=str(exc),
                )],
                request_id=request_id,
            ).model_dump(mode="json"),
        )

    elapsed_ms = (time.perf_counter() - t0) * 1000
    log.info(
        "Ingestion complete",
        document_id=result["document_id"],
        total_chunks=result["total_chunks"],
        elapsed_ms=round(elapsed_ms, 1),
        request_id=request_id,
    )

    return IngestResponse(
        document_id=result["document_id"],
        filename=result["filename"],
        total_pages=result["total_pages"],
        total_chunks=result["total_chunks"],
        doc_hash=result["doc_hash"],
        status=IngestStatus.COMPLETE,
    )
