import pytest

from app.services.llm.fake_client import FakeLLMClient
from app.services.llm_service import LLMExtractionError, extract_fields

VALID = {
    "issuer_name": "Posto Avenida LTDA",
    "cnpj": "12345678000195",
    "issue_date": "2026-01-31",
    "invoice_number": "12345",
    "total_value": 245.90,
}


def test_clean_json():
    data, meta = extract_fields("texto ocr", client=FakeLLMClient(VALID))
    assert data.issuer_name == "Posto Avenida LTDA"
    assert data.total_value == 245.90
    assert meta["attempts"] == 1
    assert meta["provider"] == "fake"


def test_json_wrapped_in_markdown_fences():
    fenced = "```json\n" + '{"issuer_name": null, "cnpj": null, "issue_date": null, ' \
        '"invoice_number": null, "total_value": null}\n```'
    data, _ = extract_fields("t", client=FakeLLMClient(fenced))
    assert data.cnpj is None


def test_json_with_surrounding_text():
    noisy = 'Aqui esta: {"issuer_name": "ACME", "cnpj": null, "issue_date": null, ' \
        '"invoice_number": null, "total_value": null} fim'
    data, _ = extract_fields("t", client=FakeLLMClient(noisy))
    assert data.issuer_name == "ACME"


def test_extra_keys_rejected_then_retry_exhausts():
    bad = {**VALID, "extra_field": "x"}
    with pytest.raises(LLMExtractionError):
        extract_fields("t", client=FakeLLMClient(bad))


def test_ambiguous_total_value_string_rejected():
    bad = {**VALID, "total_value": "1.234"}
    with pytest.raises(LLMExtractionError):
        extract_fields("t", client=FakeLLMClient(bad))


def test_string_total_value_parsed():
    ok = {**VALID, "total_value": "1.234,56"}
    data, _ = extract_fields("t", client=FakeLLMClient(ok))
    assert data.total_value == 1234.56


def test_retry_then_success_counts_attempts():
    client = FakeLLMClient(VALID, fail_times=1)  # 1ª resposta inválida, 2ª ok
    data, meta = extract_fields("t", client=client)
    assert meta["attempts"] == 2
    assert client.calls == 2


def test_invalid_forever_raises_after_max_retries():
    client = FakeLLMClient(VALID, fail_times=99)
    with pytest.raises(LLMExtractionError):
        extract_fields("t", client=client)
    # LLM_MAX_RETRIES=2 → 3 tentativas
    assert client.calls == 3
