import pytest

@pytest.fixture(autouse=True)
def clear_env_lemma_keys(monkeypatch):
    """
    Ensure Lemma settings are cleared by default during tests so that
    standard integration tests execute in local ChromaDB fallback mode.
    """
    monkeypatch.delenv("LEMMA_API_KEY", raising=False)
    monkeypatch.delenv("LEMMA_POD_ID", raising=False)
    monkeypatch.delenv("LEMMA_TOKEN", raising=False)
