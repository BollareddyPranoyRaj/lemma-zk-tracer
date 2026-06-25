"""
backend/routes/health.py
────────────────────────
Liveness / readiness probes.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health_check() -> HealthResponse:
    """Returns 200 OK if the service is alive."""
    return HealthResponse(
        status="ok",
        version=get_settings().app_version,
        timestamp=datetime.now(timezone.utc),
    )
