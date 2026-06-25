# Lemma ZK Tracer — Verifiable Due Diligence

> **Binocs Hackathon Build** | Every metric is cryptographically anchored to its source PDF.

## What It Does
Private Equity analysts upload 200-page deal documents. Standard AI hallucinates.
We don't. Every metric extracted (Revenue, EBITDA, etc.) carries:
- `source_text` — the exact verbatim passage from the PDF
- `source_hash` — SHA-256 of that passage (tamper-evident)
- `verification_hash` — HMAC-SHA256 binding (document ↔ metric ↔ value ↔ source)

If the document doesn't contain the data, we return `null`. Full stop.

## Architecture

```
┌─────────────┐    PDF     ┌─────────────────────────────────────────┐
│  Streamlit  │ ─────────► │  POST /api/v1/ingest                    │
│   (Phase 4) │            │  • PDF → pdfplumber → chunks            │
└─────────────┘            │  • chunks → ChromaDB (embeddings)       │
                           │  • returns document_id + doc_hash       │
                           └──────────────┬──────────────────────────┘
                                          │ document_id
                                          ▼
                           ┌─────────────────────────────────────────┐
                           │  POST /api/v1/analyze                   │
                           │  ① Extractor  — semantic retrieval      │
                           │               + GPT-4o extraction       │
                           │               + ZK provenance per metric│
                           │  ② Screener   — mandate gate evaluation  │
                           │  ③ Drafter    — IC Memo generation      │
                           └─────────────────────────────────────────┘
```

## Tech Stack
| Layer | Technology |
|-------|-----------|
| API | FastAPI (async) |
| Document Store | ChromaDB (persistent vector store) |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) |
| PDF Parsing | pdfplumber |
| LLM | GPT-4o via OpenAI |
| Cryptography | SHA-256 + HMAC-SHA256 (Poseidon-ready) |
| Observability | OpenTelemetry + structlog |
| Frontend | Streamlit |

## Project Structure
```
lemma-zk-tracer/
├── backend/
│   ├── config.py          # Pydantic settings (env-driven)
│   ├── models.py          # All Pydantic domain models
│   ├── crypto.py          # Cryptographic provenance layer
│   ├── document_store.py  # PDF ingestion + ChromaDB
│   ├── main.py            # FastAPI app factory
│   └── routes/
│       ├── health.py      # GET /health
│       └── ingest.py      # POST /api/v1/ingest
├── agents/                # Lemma Pod agent configs
├── documents/             # Sample 10-K PDF
├── tests/
│   └── test_phase1_ingest.py
├── .env.example
├── requirements.txt
└── pyproject.toml
```

## Setup & Run

```bash
# 1. Create virtualenv and install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Fill in OPENAI_API_KEY and PROOF_HMAC_SECRET

# 3. Start the server
python -m backend.main

# 4. Run Phase 1 tests
pytest tests/test_phase1_ingest.py -v
```

## Phase Roadmap
- [x] **Phase 1** — FastAPI scaffolding + PDF ingestion + ChromaDB
- [x] **Phase 2** — Multi-agent pipeline (Extractor → Screener → Drafter)
- [x] **Phase 3** — Cryptographic provenance (ZK-style verification hashes)
- [x] **Phase 4** — Streamlit UI + OpenTelemetry observability
