import os
import pytest


@pytest.fixture(autouse=True)
def enable_test_mode(monkeypatch):
    """Force CASP_TEST_MODE=1 for all tests so no real API calls are made."""
    monkeypatch.setenv("CASP_TEST_MODE", "1")
    # Also patch the settings object
    from casp import config
    monkeypatch.setattr(config.settings, "test_mode", True)
