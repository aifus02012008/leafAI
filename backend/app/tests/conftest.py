"""Shared pytest configuration."""
import pytest

from app.core.config import settings
from app.core.rate_limit import reset_rate_limits


@pytest.fixture(autouse=True)
def _disable_rate_limits(monkeypatch):
    """Most tests register many users from one client; rate-limit tests re-enable it explicitly."""
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    # Never call real LLM APIs from tests, even if keys exist in the local .env.
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", None)
    reset_rate_limits()
    yield
    reset_rate_limits()
