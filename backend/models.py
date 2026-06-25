"""
backend/models.py
─────────────────
Pydantic v2 domain models for the entire system.
Every API input and output is typed here — no raw dicts escape the boundary.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ─── Enumerations ─────────────────────────────────────────────────────────────


class IngestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class ScreenDecision(str, Enum):
    GO = "GO"
    NO_GO = "NO_GO"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


# ─── Document Chunk ───────────────────────────────────────────────────────────


class DocumentChunk(BaseModel):
    """A single semantic chunk extracted from the PDF."""

    chunk_id: str = Field(..., description="UUID for this chunk")
    document_id: str = Field(..., description="Parent document UUID")
    page_number: int = Field(..., ge=1)
    text: str = Field(..., min_length=1)
    token_count: int = Field(..., ge=0)
    embedding_model: str | None = None


# ─── Ingestion Models ─────────────────────────────────────────────────────────


class IngestResponse(BaseModel):
    """Returned by POST /api/v1/ingest on success."""

    document_id: str = Field(..., description="UUID assigned to this document")
    filename: str
    total_pages: int
    total_chunks: int
    status: IngestStatus = IngestStatus.COMPLETE
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    doc_hash: str = Field(
        ...,
        description="SHA-256 hash of the raw PDF bytes — the cryptographic anchor",
    )


# ─── Financial Metrics ────────────────────────────────────────────────────────


class MetricEvidence(BaseModel):
    """
    A single extracted financial metric with full cryptographic provenance.
    This is the core output unit of the Extractor agent.
    """

    metric: str = Field(..., description="Metric name, e.g. 'revenue'")
    value: str | None = Field(
        None,
        description="Extracted value string; null if not found in document",
    )
    unit: str | None = Field(None, description="Currency, %, etc.")
    source_text: str | None = Field(
        None,
        description="The verbatim passage from the PDF that justifies this value",
    )
    page_number: int | None = Field(None, ge=1)
    chunk_id: str | None = Field(None)

    # Cryptographic provenance
    doc_hash: str | None = Field(
        None,
        description="SHA-256 of the raw PDF — links metric to a specific document",
    )
    source_hash: str | None = Field(
        None,
        description="SHA-256(source_text) — tamper-evident hash of the evidence",
    )
    verification_hash: str | None = Field(
        None,
        description=(
            "HMAC-SHA256(doc_hash || metric || value || source_text) "
            "— ZK-style proof binding this metric to this document"
        ),
    )

    @model_validator(mode="after")
    def null_value_clears_hashes(self) -> "MetricEvidence":
        """
        Zero-hallucination guard: if value is null, all provenance fields
        must also be null. We never attach hashes to fabricated data.
        """
        if self.value is None:
            self.source_text = None
            self.source_hash = None
            self.verification_hash = None
            self.page_number = None
            self.chunk_id = None
        return self


class FinancialMetrics(BaseModel):
    """Structured container for all extracted financial metrics."""

    revenue: MetricEvidence | None = None
    ebitda: MetricEvidence | None = None
    ebitda_margin: MetricEvidence | None = None
    yoy_growth: MetricEvidence | None = None
    customer_concentration: MetricEvidence | None = None
    legal_risks: MetricEvidence | None = None
    net_income: MetricEvidence | None = None
    total_debt: MetricEvidence | None = None
    free_cash_flow: MetricEvidence | None = None

    def metrics_found(self) -> list[str]:
        """Return list of metric names that were actually extracted (non-null value)."""
        found = []
        for name, field in self.model_fields.items():
            evidence: MetricEvidence | None = getattr(self, name)
            if evidence is not None and evidence.value is not None:
                found.append(name)
        return found

    def metrics_missing(self) -> list[str]:
        """Return metric names with null values."""
        missing = []
        for name in self.model_fields:
            evidence: MetricEvidence | None = getattr(self, name)
            if evidence is None or evidence.value is None:
                missing.append(name)
        return missing


# ─── Screener Models ──────────────────────────────────────────────────────────


class ScreenerMandate(BaseModel):
    """Investment mandate thresholds — all values are enforced strictly."""

    min_revenue_m: float = Field(default=5.0, ge=0, description="Minimum revenue in $M")
    min_ebitda_m: float = Field(default=1.0, ge=0, description="Minimum EBITDA in $M")
    min_ebitda_margin_pct: float = Field(
        default=10.0, ge=0, le=100, description="Minimum EBITDA margin %"
    )
    max_customer_concentration_pct: float = Field(
        default=40.0, ge=0, le=100, description="Max single customer concentration %"
    )
    min_yoy_growth_pct: float = Field(default=5.0, description="Minimum YoY revenue growth %")
    allowed_legal_risk_levels: list[str] = Field(
        default=["Low", "Medium"],
        description="Acceptable legal risk levels",
    )


class ScreenerFlag(BaseModel):
    """A single pass/fail gate from the screener."""

    gate: str
    passed: bool
    required: str
    actual: str | None
    reason: str


class ScreenerResult(BaseModel):
    """Full output of the Screener agent."""

    decision: ScreenDecision
    flags: list[ScreenerFlag]
    passed_count: int
    failed_count: int
    na_count: int  # gates where data was missing


# ─── Drafter / IC Memo ────────────────────────────────────────────────────────


class ICMemoSection(BaseModel):
    title: str
    content: str
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="metric keys referenced in this section",
    )


class ICMemo(BaseModel):
    """Structured Investment Committee Memo ready for Markdown rendering."""

    document_id: str
    filename: str
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    executive_summary: str
    sections: list[ICMemoSection]
    screen_result: ScreenerResult
    markdown: str = Field(..., description="Full Markdown rendering of the memo")


# ─── Pipeline Response ────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Request body for POST /api/v1/analyze."""

    document_id: str = Field(..., description="document_id returned by /ingest")
    mandate: ScreenerMandate = Field(
        default_factory=ScreenerMandate,
        description="Investment mandate thresholds; defaults apply if omitted",
    )
    include_raw_chunks: bool = Field(
        default=False,
        description="If true, include raw chunk text in response (debug mode)",
    )


class AnalyzeResponse(BaseModel):
    """Complete response from POST /api/v1/analyze."""

    document_id: str
    filename: str
    metrics: FinancialMetrics
    screen_result: ScreenerResult
    memo: ICMemo
    pipeline_duration_ms: float
    metrics_found: list[str]
    metrics_missing: list[str]


# ─── Error Models ─────────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    """Standard error envelope returned on 4xx / 5xx."""

    status: int
    error: str
    details: list[ErrorDetail] = Field(default_factory=list)
    request_id: str | None = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
