import pytest
import backend.config

@pytest.fixture(autouse=True)
def clear_env_lemma_keys(monkeypatch):
    """
    Ensure Lemma settings are cleared by default during tests so that
    standard integration tests execute in local ChromaDB fallback mode.
    """
    # Clear the settings cache
    backend.config.get_settings.cache_clear()
    
    real_get_settings = backend.config.get_settings
    
    def mock_settings_fn():
        settings = real_get_settings()
        settings.lemma_api_key = ""
        settings.lemma_pod_id = ""
        return settings

    monkeypatch.setattr(backend.config, "get_settings", mock_settings_fn)
