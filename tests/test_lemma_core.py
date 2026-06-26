"""
tests/test_lemma_core.py
─────────────────────────
Integration/unit tests for Lemma-native mode of DocumentStore.
"""
from __future__ import annotations

import io
import pytest
from unittest.mock import MagicMock, patch

from backend.config import Settings
from backend.document_store import DocumentStore
from backend.models import DocumentChunk


@pytest.mark.asyncio
async def test_lemma_native_mode_initialization():
    """Verify that when Lemma settings are provided, DocumentStore resolves is_lemma_active=True."""
    mock_settings = Settings(
        openai_api_key="mock_openai",
        lemma_api_key="mock_lemma_key",
        lemma_pod_id="mock_pod_id"
    )

    with patch("backend.document_store.get_settings", return_value=mock_settings), \
         patch("lemma_sdk.Pod") as mock_pod_class:
        
        # Instantiate document store
        store = await DocumentStore.create()
        assert store.is_lemma_active is True
        mock_pod_class.assert_called_once_with(pod_id="mock_pod_id", token="mock_lemma_key")


@pytest.mark.asyncio
async def test_lemma_native_mode_ingest():
    """Verify that ingest uploads file to Lemma Pod and polls status correctly."""
    mock_settings = Settings(
        openai_api_key="mock_openai",
        lemma_api_key="mock_lemma_key",
        lemma_pod_id="mock_pod_id"
    )

    pdf_bytes = b"%PDF-1.4\ncontent"
    filename = "report.pdf"

    # Mock Lemma SDK Pod and its files resource
    mock_pod = MagicMock()
    mock_files = MagicMock()
    mock_pod.files = mock_files

    # File status mock flow: PENDING -> COMPLETED
    mock_file_detail_pending = MagicMock()
    mock_file_detail_pending.status = "PENDING"
    mock_file_detail_completed = MagicMock()
    mock_file_detail_completed.status = "COMPLETED"

    mock_files.get.side_effect = [mock_file_detail_pending, mock_file_detail_completed]

    with patch("backend.document_store.get_settings", return_value=mock_settings), \
         patch("lemma_sdk.Pod", return_value=mock_pod), \
         patch("backend.document_store.hash_document", return_value="dummyhash"), \
         patch("backend.document_store.open", return_value=io.BytesIO(pdf_bytes)), \
         patch("backend.document_store.DocumentStore._save_pdf", return_value="/tmp/report.pdf"):
        
        store = await DocumentStore.create()
        result = await store.ingest(pdf_bytes, filename)

        assert result["doc_hash"] == "dummyhash"
        assert result["filename"] == filename
        
        # Verify upload_file was called with expected arguments
        mock_files.upload_file.assert_called_once()
        args, kwargs = mock_files.upload_file.call_args
        assert kwargs["filename"] == filename
        assert kwargs["description"] == "doc_hash:dummyhash"
        assert kwargs["search_enabled"] is True

        # Verify polling happened twice (PENDING -> COMPLETED)
        assert mock_files.get.call_count == 2


@pytest.mark.asyncio
async def test_lemma_native_mode_retrieve():
    """Verify retrieve performs vector search and maps FileSearchResultSchema items."""
    mock_settings = Settings(
        openai_api_key="mock_openai",
        lemma_api_key="mock_lemma_key",
        lemma_pod_id="mock_pod_id"
    )

    mock_pod = MagicMock()
    mock_files = MagicMock()
    mock_pod.files = mock_files

    # Mock list (to extract doc_hash)
    mock_file_detail = MagicMock()
    mock_file_detail.description = "doc_hash:hash123"
    mock_file_list_response = MagicMock()
    mock_file_list_response.items = [mock_file_detail]
    mock_files.list.return_value = mock_file_list_response

    # Mock search
    mock_search_item = MagicMock()
    mock_search_item.file_id = "file-uuid"
    mock_search_item.chunk_index = 0
    mock_search_item.content = "EBITDA was $10M"
    mock_search_item.page_number = 4
    
    mock_search_response = MagicMock()
    mock_search_response.items = [mock_search_item]
    mock_files.search.return_value = mock_search_response

    with patch("backend.document_store.get_settings", return_value=mock_settings), \
         patch("lemma_sdk.Pod", return_value=mock_pod):
        
        store = await DocumentStore.create()
        results = await store.retrieve("doc_id", "EBITDA", n_results=5)

        assert len(results) == 1
        assert results[0]["chunk_id"] == "file-uuid-0"
        assert results[0]["text"] == "EBITDA was $10M"
        assert results[0]["page_number"] == 4
        assert results[0]["doc_hash"] == "hash123"

        # Verify search arguments
        mock_files.search.assert_called_once_with(
            query="EBITDA",
            search_method="VECTOR",
            scope_path="/uploads/doc_id"
        )
