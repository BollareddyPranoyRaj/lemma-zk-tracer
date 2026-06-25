"""
backend/dependencies.py
───────────────────────
FastAPI dependency injection utilities.
"""
from __future__ import annotations

from fastapi import HTTPException, Request, status
from backend.document_store import DocumentStore


async def get_document_store(request: Request) -> DocumentStore:
    """
    FastAPI dependency that retrieves the singleton DocumentStore 
    from the application state.
    """
    store = getattr(request.app.state, "document_store", None)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document store not initialised",
        )
    return store
