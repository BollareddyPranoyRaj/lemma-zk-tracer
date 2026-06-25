"""
backend/routes/analyze.py
─────────────────────────
POST /api/v1/analyze — runs the multi-agent due diligence pipeline.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.config import get_settings
from backend.dependencies import get_document_store
from backend.document_store import DocumentStore
from backend.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ErrorDetail,
    ErrorResponse
)
from backend.agents.extractor import ExtractorAgent
from backend.agents.screener import ScreenerAgent
from backend.agents.drafter import DrafterAgent

log = structlog.get_logger(__name__)
router = APIRouter()


def _get_filename_by_id(document_id: str) -> str:
    """Helper to extract original filename from data/uploads/ directory."""
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.exists():
        return "document.pdf"
    
    prefix = f"{document_id}_"
    for item in os.listdir(upload_dir):
        if item.startswith(prefix):
            return item[len(prefix):]
    return "document.pdf"


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze an ingested PDF using the multi-agent due diligence pipeline",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input mandate or parameters"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Pipeline execution failure"},
    },
)
async def analyze_document(
    request: Request,
    body: AnalyzeRequest,
    store: DocumentStore = Depends(get_document_store),
) -> AnalyzeResponse:
    request_id = getattr(request.state, "request_id", None)
    document_id = body.document_id
    t0 = time.perf_counter()

    from opentelemetry import trace
    tracer = trace.get_tracer("backend.routes.analyze")

    log.info("Analysis request received", document_id=document_id, request_id=request_id)

    # ── 1. Check Document Existence ──────────────────────────────────────────
    exists = await store.document_exists(document_id)
    if not exists:
        log.warning("Document not found in store", document_id=document_id, request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                status=404,
                error="Document not found",
                details=[ErrorDetail(
                    code="DOCUMENT_NOT_FOUND",
                    message=f"The document with ID '{document_id}' does not exist or has not been ingested.",
                    field="document_id",
                )],
                request_id=request_id,
            ).model_dump(mode="json"),
        )

    # ── 2. Retrieve doc_hash ──────────────────────────────────────────────────
    try:
        chunks = await store.get_all_chunks(document_id)
        if not chunks:
            raise ValueError("Document has no chunks associated with it.")
        doc_hash = chunks[0]["doc_hash"]
    except Exception as exc:
        log.error("Failed to retrieve document metadata", exc_info=exc, request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                status=500,
                error="Metadata retrieval failed",
                details=[ErrorDetail(
                    code="METADATA_ERROR",
                    message=str(exc),
                )],
                request_id=request_id,
            ).model_dump(mode="json"),
        )

    # Resolve filename
    filename = _get_filename_by_id(document_id)

    # ── 3. Run Pipeline ───────────────────────────────────────────────────────
    try:
        with tracer.start_as_current_span("analyze_pipeline") as pipeline_span:
            pipeline_span.set_attribute("document_id", document_id)
            pipeline_span.set_attribute("filename", filename)

            # A. Extractor Agent
            with tracer.start_as_current_span("extractor_agent"):
                log.info("Running Extractor Agent", document_id=document_id, request_id=request_id)
                extractor = ExtractorAgent(store)
                metrics = await extractor.extract(document_id, doc_hash)

            # B. Screener Agent
            with tracer.start_as_current_span("screener_agent") as screener_span:
                log.info("Running Screener Agent", document_id=document_id, request_id=request_id)
                screener = ScreenerAgent()
                screen_result = screener.screen(metrics, body.mandate)
                screener_span.set_attribute("decision", screen_result.decision.value)
                pipeline_span.set_attribute("decision", screen_result.decision.value)

            # C. Drafter Agent
            with tracer.start_as_current_span("drafter_agent"):
                log.info("Running Drafter Agent", document_id=document_id, request_id=request_id)
                drafter = DrafterAgent()
                memo = await drafter.draft(document_id, filename, metrics, screen_result)

    except Exception as exc:
        # Record error status on active span
        span = trace.get_current_span()
        if span.is_recording():
            span.set_status(trace.StatusCode.ERROR, str(exc))
            span.record_exception(exc)

        log.error("Pipeline agent execution failed", exc_info=exc, request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                status=500,
                error="Pipeline agent execution failed",
                details=[ErrorDetail(
                    code="PIPELINE_AGENT_ERROR",
                    message=str(exc),
                )],
                request_id=request_id,
            ).model_dump(mode="json"),
        )

    elapsed_ms = (time.perf_counter() - t0) * 1000
    log.info(
        "Analysis complete",
        document_id=document_id,
        decision=screen_result.decision.value,
        elapsed_ms=round(elapsed_ms, 1),
        request_id=request_id,
    )

    return AnalyzeResponse(
        document_id=document_id,
        filename=filename,
        metrics=metrics,
        screen_result=screen_result,
        memo=memo,
        pipeline_duration_ms=elapsed_ms,
        metrics_found=metrics.metrics_found(),
        metrics_missing=metrics.metrics_missing(),
    )
