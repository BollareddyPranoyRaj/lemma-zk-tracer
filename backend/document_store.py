"""
backend/document_store.py
─────────────────────────
PDF ingestion pipeline → semantic chunking → persistent vector store.

The DocumentStore is the Lemma "data layer" equivalent for our system:
  • PDFs are chunked semantically (by page + token budget).
  • Each chunk is embedded and stored in ChromaDB (persistent, local).
  • The store is async-safe: all I/O is offloaded to a thread executor.
  • Only doc_hash and metadata are public; raw text stays in the local store.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import pdfplumber
import tiktoken

from backend.config import get_settings
from backend.crypto import hash_document
from backend.models import DocumentChunk

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Module-level thread pool for blocking I/O (PDF parsing, embeddings)
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="docstore")


class DocumentStore:
    """
    Manages document ingestion, chunking, embedding, and retrieval.

    Lifecycle:
        store = await DocumentStore.create()
        result = await store.ingest(pdf_bytes, filename)
        chunks = await store.retrieve(document_id, query="EBITDA")
    """

    def __init__(self, chroma_client, collection, embedding_fn):
        self._chroma = chroma_client
        self._collection = collection
        self._embed = embedding_fn
        self._settings = get_settings()
        self._tokenizer = tiktoken.get_encoding("cl100k_base")

    @classmethod
    async def create(cls) -> "DocumentStore":
        """
        Async factory: initialise ChromaDB and the embedding model.
        Runs heavy imports in a thread to avoid blocking the event loop.
        """
        settings = get_settings()
        loop = asyncio.get_event_loop()

        def _init_chroma():
            import chromadb
            from chromadb.utils import embedding_functions

            Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            collection = client.get_or_create_collection(
                name="document_chunks",
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"},
            )
            return client, collection, ef

        client, collection, ef = await loop.run_in_executor(_executor, _init_chroma)
        logger.info("DocumentStore initialised (chroma_dir=%s)", settings.chroma_persist_dir)
        return cls(client, collection, ef)

    # ─── Ingestion ────────────────────────────────────────────────────────────

    async def ingest(self, pdf_bytes: bytes, filename: str) -> dict:
        """
        Full ingestion pipeline for a PDF:
          1. Hash the raw bytes (doc_hash)
          2. Save to disk
          3. Extract text + page metadata via pdfplumber
          4. Chunk by page with token budget
          5. Embed and store in ChromaDB

        Returns:
            dict with document_id, doc_hash, total_pages, total_chunks
        """
        settings = self._settings
        document_id = str(uuid.uuid4())
        doc_hash = hash_document(pdf_bytes)

        # Save raw PDF
        upload_path = await self._save_pdf(pdf_bytes, document_id, filename)
        logger.info("PDF saved: doc_id=%s path=%s", document_id, upload_path)

        # Parse and chunk in thread (pdfplumber is sync)
        loop = asyncio.get_event_loop()
        chunks, total_pages = await loop.run_in_executor(
            _executor,
            self._parse_and_chunk,
            pdf_bytes,
            document_id,
            doc_hash,
        )

        # Store chunks in vector DB
        await loop.run_in_executor(
            _executor,
            self._store_chunks,
            chunks,
            doc_hash,
        )

        logger.info(
            "Ingestion complete: doc_id=%s pages=%d chunks=%d",
            document_id,
            total_pages,
            len(chunks),
        )
        return {
            "document_id": document_id,
            "doc_hash": doc_hash,
            "total_pages": total_pages,
            "total_chunks": len(chunks),
            "filename": filename,
        }

    async def _save_pdf(self, pdf_bytes: bytes, document_id: str, filename: str) -> Path:
        settings = self._settings
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{document_id}_{filename}"
        path = upload_dir / safe_name
        async with aiofiles.open(path, "wb") as f:
            await f.write(pdf_bytes)
        return path

    def _parse_and_chunk(
        self,
        pdf_bytes: bytes,
        document_id: str,
        doc_hash: str,
    ) -> tuple[list[DocumentChunk], int]:
        """
        Synchronous PDF parsing (runs in thread pool).
        Uses pdfplumber for accurate text extraction with layout awareness.
        """
        settings = self._settings
        chunks: list[DocumentChunk] = []
        total_pages = 0

        import io
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            total_pages = len(pdf.pages)
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                if not page_text.strip():
                    continue  # skip blank/image-only pages

                # Split page text into token-budget chunks
                page_chunks = self._chunk_text(
                    text=page_text,
                    document_id=document_id,
                    page_number=page_num,
                    doc_hash=doc_hash,
                )
                chunks.extend(page_chunks)

        return chunks, total_pages

    def _chunk_text(
        self,
        text: str,
        document_id: str,
        page_number: int,
        doc_hash: str,
    ) -> list[DocumentChunk]:
        """
        Split text into token-budget chunks with overlap.
        Preserves sentence boundaries where possible.
        """
        settings = self._settings
        tokens = self._tokenizer.encode(text)
        chunk_size = settings.chunk_size_tokens
        overlap = settings.chunk_overlap_tokens
        chunks: list[DocumentChunk] = []

        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self._tokenizer.decode(chunk_tokens)

            chunks.append(DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                page_number=page_number,
                text=chunk_text,
                token_count=len(chunk_tokens),
                embedding_model="all-MiniLM-L6-v2",
            ))

            if end == len(tokens):
                break
            start = end - overlap  # sliding window with overlap

        return chunks

    def _store_chunks(self, chunks: list[DocumentChunk], doc_hash: str) -> None:
        """Upsert all chunks into ChromaDB (sync — runs in thread pool)."""
        if not chunks:
            return

        self._collection.add(
            ids=[c.chunk_id for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "document_id": c.document_id,
                    "page_number": c.page_number,
                    "token_count": c.token_count,
                    "doc_hash": doc_hash,
                }
                for c in chunks
            ],
        )

    # ─── Retrieval ────────────────────────────────────────────────────────────

    async def retrieve(
        self,
        document_id: str,
        query: str,
        n_results: int = 5,
    ) -> list[dict]:
        """
        Semantic search within a specific document's chunks.
        Returns list of {text, page_number, chunk_id, doc_hash, distance}.
        """
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            _executor,
            self._query_collection,
            document_id,
            query,
            n_results,
        )
        return results

    def _query_collection(
        self,
        document_id: str,
        query: str,
        n_results: int,
    ) -> list[dict]:
        """Synchronous ChromaDB query (runs in thread pool)."""
        result = self._collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"document_id": {"$eq": document_id}},
        )

        output = []
        if not result["ids"] or not result["ids"][0]:
            return output

        for i, chunk_id in enumerate(result["ids"][0]):
            output.append({
                "chunk_id": chunk_id,
                "text": result["documents"][0][i],
                "page_number": result["metadatas"][0][i].get("page_number"),
                "doc_hash": result["metadatas"][0][i].get("doc_hash"),
                "distance": result["distances"][0][i] if result.get("distances") else None,
            })
        return output

    async def get_all_chunks(self, document_id: str) -> list[dict]:
        """
        Return ALL chunks for a document (used by the Extractor for broad sweep).
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self._get_all_chunks_sync, document_id
        )

    def _get_all_chunks_sync(self, document_id: str) -> list[dict]:
        result = self._collection.get(
            where={"document_id": {"$eq": document_id}},
            include=["documents", "metadatas"],
        )
        output = []
        for i, chunk_id in enumerate(result["ids"]):
            output.append({
                "chunk_id": chunk_id,
                "text": result["documents"][i],
                "page_number": result["metadatas"][i].get("page_number"),
                "doc_hash": result["metadatas"][i].get("doc_hash"),
            })
        return output

    async def document_exists(self, document_id: str) -> bool:
        """Check if a document has been ingested."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self._doc_exists_sync, document_id
        )

    def _doc_exists_sync(self, document_id: str) -> bool:
        result = self._collection.get(
            where={"document_id": {"$eq": document_id}},
            limit=1,
        )
        return bool(result["ids"])
