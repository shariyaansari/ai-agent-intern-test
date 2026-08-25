import pytest

from app.llm import GroqClient


def test_groq_client_requires_api_key(monkeypatch):
    monkeypatch.delenv(
        "GROQ_API_KEY",
        raising=False,
    )

    with pytest.raises(ValueError):
        GroqClient()