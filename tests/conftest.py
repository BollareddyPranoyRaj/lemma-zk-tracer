import pytest
import backend.config

@pytest.fixture(autouse=True)
def clear_env_lemma_keys(monkeypatch):
    """
    Ensure Lemma settings are cleared by default during tests so that
    standard integration tests execute in local ChromaDB fallback mode.
    """
    settings = backend.config.get_settings()
    monkeypatch.setattr(settings, "lemma_api_key", "")
    monkeypatch.setattr(settings, "lemma_pod_id", "")

