# Lemma ZK Tracer — Verifiable Due Diligence

> **Binocs Hackathon Build** | Every metric is cryptographically anchored to its source PDF.

## 🔗 Live Deployments
* **Live Web App**: [http://52.22.227.138:8501](http://52.22.227.138:8501)
* **Backend API Docs**: [http://52.22.227.138:8000/docs](http://52.22.227.138:8000/docs)

---

## What It Does
Private Equity analysts upload 200-page deal documents. Standard AI hallucinates.
We don't. Every metric extracted (Revenue, EBITDA, etc.) carries:
- `source_text` — the exact verbatim passage from the PDF.
- `source_hash` — SHA-256 of that passage (tamper-evident).
- `verification_hash` — HMAC-SHA256 binding (document ↔ metric ↔ value ↔ source).

If the document doesn't contain the data, we return `null`. Full stop.

---

## Architecture & Data Flow

```
                                      PDF File
                                         │
                                         ▼
                               ┌───────────────────┐
                               │     Streamlit     │
                               │   Web Dashboard   │
                               └─────────┬─────────┘
                                         │
                        POST /api/v1/ingest (File Upload)
                                         │
                                         ▼
                             ┌──────────────────────┐
                             │     FastAPI Host     │
                             └───────────┬──────────┘
                                         │
                          Is Lemma platform configured?
                                🔑       │       ❌
                       ┌─────────────────┴─────────────────┐
                       ▼                                   ▼
             [Core Datastore]                      [Local Fallback]
             Lemma Pod Client                      ChromaDB Vector Store
         - Uploads directly to Pod               - Local PDF Parsing (pdfplumber)
         - Polls for vector indexing             - Semantic chunking with overlap
         - Native Vector search                  - Sentence-transformers embeddings
                       │                                   │
                       └─────────────────┬─────────────────┘
                                         │
                                         ▼
                            POST /api/v1/analyze (RAG)
                                         │
                                         ▼
                             ┌──────────────────────┐
                             │  Multi-Agent Engine  │
                             │  ① Extractor (RAG)   │
                             │  ② Screener (Gates)  │
                             │  ③ Drafter (IC Memo) │
                             └──────────────────────┘
```

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| **Core Database & Search** | **Gappy AI's Lemma platform** (Pod Vector Search) |
| **Local Fallback DB** | **ChromaDB** (persistent local vector store) |
| **Local Embeddings** | `all-MiniLM-L6-v2` (sentence-transformers) |
| **API Framework** | FastAPI (async) |
| **PDF Parsing** | pdfplumber |
| **LLM Reasoning** | GPT-4o via OpenAI |
| **Cryptography** | SHA-256 + HMAC-SHA256 (Poseidon-ready) |
| **Observability** | OpenTelemetry + structlog |
| **Frontend** | Streamlit |

---

## Project Structure
```
lemma-zk-tracer/
├── backend/
│   ├── config.py          # Pydantic settings (env-driven)
│   ├── models.py          # Pydantic request/response domain models
│   ├── crypto.py          # Cryptographic provenance layer (HMAC-SHA256)
│   ├── document_store.py  # PDF ingestion & search (Lemma SDK ↔ ChromaDB)
│   ├── main.py            # FastAPI entrypoint
│   └── routes/
│       ├── health.py      # GET /health
│       ├── ingest.py      # POST /api/v1/ingest
│       └── analyze.py     # POST /api/v1/analyze
├── frontend/
│   ├── app.py             # Streamlit application
│   ├── assets/            # CSS styles
│   ├── components/        # Split UI components (Header, Dashboard, PDF, Memo)
│   └── services/
│       └── api.py         # HTTP connection client & RAG response mapper
├── agents/                # Lemma Pod agent configurations
├── documents/             # Sample 10-K and prospectus PDFs
└── tests/                 # Backend pytest suite (18 E2E and unit tests)
```

---

## Setup & Run

### 1. Create Virtualenv and Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
# OpenAI for Agent Reasoning
OPENAI_API_KEY=sk-proj-...

# Lemma Platform Credentials (for Core Datastore Mode)
LEMMA_API_KEY=eyJraW...
LEMMA_POD_ID=019effe6...

# Cryptographic Secret for Provable HMACs
PROOF_HMAC_SECRET=your-secret-key-at-least-32-chars
```
> **Resiliency Fallback**: If `LEMMA_API_KEY` or `LEMMA_POD_ID` is missing, or if the token has expired, the system dynamically switches to local ChromaDB mode.

### 3. Start the Backend Server
```bash
python -m backend.main
```

### 4. Run the Streamlit Dashboard
```bash
streamlit run frontend/app.py
```

### 5. Run Backend Tests
```bash
pytest -v
```
