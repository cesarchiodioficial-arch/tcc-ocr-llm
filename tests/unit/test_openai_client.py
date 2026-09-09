"""Testes do OpenAIClient sem rede (httpx.post é substituído)."""

import httpx
import pytest

from app.services.llm.base import LLMAuthError, LLMError
from app.services.llm.openai_client import OpenAIClient


class _Resp:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def _client():
    return OpenAIClient(api_key="k", base_url="https://api.openai.com/v1", model="gpt-4o-mini")


def test_success(monkeypatch):
    payload = {"choices": [{"message": {"content": '{"issuer_name": null}'}}]}
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Resp(200, payload))
    result = _client().complete("sys", "user", timeout=5)
    assert result.provider == "openai"
    assert result.model == "gpt-4o-mini"
    assert result.text == '{"issuer_name": null}'


def test_auth_error_not_retryable(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Resp(401, text="unauthorized"))
    with pytest.raises(LLMAuthError):
        _client().complete("s", "u", timeout=5)


def test_http_500_is_llm_error(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Resp(500, text="boom"))
    with pytest.raises(LLMError):
        _client().complete("s", "u", timeout=5)


def test_timeout_is_llm_error(monkeypatch):
    def _raise(*a, **k):
        raise httpx.TimeoutException("slow")

    monkeypatch.setattr(httpx, "post", _raise)
    with pytest.raises(LLMError):
        _client().complete("s", "u", timeout=5)


def test_malformed_payload_is_llm_error(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Resp(200, {"unexpected": 1}))
    with pytest.raises(LLMError):
        _client().complete("s", "u", timeout=5)
