from app.models.schemas import ExtractedFields
from app.services.validation_service import normalize_extracted, validate_extracted


def test_all_fields_valid():
    data = ExtractedFields(
        issuer_name="Posto Avenida LTDA",
        cnpj="12.345.678/0001-95",
        issue_date="31/01/2026",
        invoice_number="12345",
        total_value=245.90,
    )
    checks = validate_extracted(data)
    assert all(c.valid for c in checks.values())


def test_null_fields_are_valid_but_flagged():
    data = ExtractedFields()
    checks = validate_extracted(data)
    assert all(c.valid for c in checks.values())
    assert all(c.reason and "ausente" in c.reason for c in checks.values())


def test_invalid_cnpj_and_date_and_value():
    data = ExtractedFields(
        issuer_name="X",  # curto demais
        cnpj="12345678000199",  # dígitos errados
        issue_date="31/02/2026",  # data impossível
        invoice_number="   ",  # vazio
        total_value=None,
    )
    checks = validate_extracted(data)
    assert checks["issuer_name"].valid is False
    assert checks["cnpj"].valid is False
    assert checks["issue_date"].valid is False
    assert checks["invoice_number"].valid is False
    assert checks["total_value"].valid is True  # null é permitido


def test_issuer_name_without_letters_is_invalid():
    checks = validate_extracted(ExtractedFields(issuer_name="12345"))
    assert checks["issuer_name"].valid is False


def test_negative_total_value_is_invalid():
    checks = validate_extracted(ExtractedFields(total_value=-5.0))
    assert checks["total_value"].valid is False


def test_normalize_drops_ambiguous_total_value():
    # valor que não passa no parse vira None (sinalizado como inválido no field_check)
    data = ExtractedFields(issuer_name="ACME")
    data.total_value = None
    out = normalize_extracted(data)
    assert out.total_value is None


def test_normalize_converts_to_internal_formats():
    data = ExtractedFields(
        issuer_name="  Posto Avenida LTDA  ",
        cnpj="12.345.678/0001-95",
        issue_date="31/01/2026",
        invoice_number="  12345 ",
        total_value=245.9,
    )
    out = normalize_extracted(data)
    assert out.issuer_name == "Posto Avenida LTDA"
    assert out.cnpj == "12345678000195"
    assert out.issue_date == "2026-01-31"
    assert out.invoice_number == "12345"
    assert out.total_value == 245.9
