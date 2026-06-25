"""
backend/main.py
────────────────
FastAPI application entrypoint.

Phase 1 scope:
  • POST /api/v1/ingest  — PDF upload → document_store → returns document_id + doc_hash
  • GET  /api/v1/health  — liveness probe

Async lifecycle:
  • DocumentStore is initialised once at startup via lifespan context.
  • Injected into endpoints via FastAPI dependency injection.
"""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

import structlog
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.document_store import DocumentStore
from backend.models import ErrorResponse, IngestResponse, IngestStatus

# ─── Logging ──────────────────────────────────────────────────────────────────

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
log = structlog.get_logger(__name__)
logging.basicConfig(level=get_settings().log_level)

# ─── Application State ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise shared resources on startup; teardown on shutdown."""
    settings = get_settings()
    log.info("Starting up", app=settings.app_name, version=settings.app_version)

    # Setup OpenTelemetry tracing
    if not getattr(app.state, "otel_initialized", False):
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            resource = Resource.create(attributes={
                "service.name": settings.app_name,
                "service.version": settings.app_version,
            })
            provider = TracerProvider(resource=resource)
            
            endpoint_url = settings.otlp_endpoint
            if not endpoint_url.endswith("/v1/traces"):
                endpoint_url = f"{endpoint_url.rstrip('/')}/v1/traces"
                
            exporter = OTLPSpanExporter(endpoint=endpoint_url)
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            
            FastAPIInstrumentor().instrument_app(app)
            app.state.otel_initialized = True
            log.info("OpenTelemetry instrumentation successfully initialized", endpoint=endpoint_url)
        except Exception as e:
            log.warning("Failed to initialize OpenTelemetry", error=str(e))

    app.state.document_store = await DocumentStore.create()
    log.info("DocumentStore ready")

    yield  # Application is running

    log.info("Shutting down")
    
    # Shutdown OpenTelemetry tracing
    try:
        from opentelemetry import trace
        provider = trace.get_tracer_provider()
        if hasattr(provider, "shutdown"):
            provider.shutdown()
            log.info("OpenTelemetry provider shut down successfully")
    except Exception as e:
        log.warning("Failed to shut down OpenTelemetry provider", error=str(e))

    app.state.document_store = None


# ─── App Factory ──────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Verifiable Due Diligence Tracer: AI-extracted financial metrics "
            "with cryptographic provenance on every data point."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten in production
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request ID middleware ──────────────────────────────────────────────────
    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Custom HTTPException handler ──────────────────────────────────────────
    from fastapi.exceptions import HTTPException as FastAPIHTTPException

    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
        if isinstance(exc.detail, dict):
            # Already formatted as ErrorResponse
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        
        request_id = getattr(request.state, "request_id", None)
        body = ErrorResponse(
            status=exc.status_code,
            error=str(exc.detail),
            request_id=request_id,
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))

    # ── Global exception handler ───────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        log.error(
            "Unhandled exception",
            exc_info=exc,
            request_id=request_id,
            path=str(request.url),
        )
        body = ErrorResponse(
            status=500,
            error="Internal server error",
            request_id=request_id,
        )
        return JSONResponse(status_code=500, content=body.model_dump(mode="json"))

    # ── Register routers ──────────────────────────────────────────────────────
    from backend.routes.ingest import router as ingest_router
    from backend.routes.health import router as health_router
    from backend.routes.analyze import router as analyze_router

    app.include_router(health_router, tags=["Health"])
    app.include_router(ingest_router, prefix="/api/v1", tags=["Ingestion"])
    app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])

    return app


app = create_app()


# ─── Dependency Injection ─────────────────────────────────────────────────────
# (Dependencies are imported from backend.dependencies)


# ─── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=get_settings().log_level.lower(),
    )
