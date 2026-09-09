"""Validação sistêmica dos dados extraídos (ESPECIFICACAO.md §8).

Produz um `FieldCheck` por campo. NÃO bloqueia o fluxo: o documento sempre
segue para revisão humana (`VALIDATION_PENDING`); quem decide é a pessoa.

`null` é um resultado VÁLIDO ("não identificado") — o sistema nunca preenche
valores presumidos.
"""

from __future__ import annotations

from app.models.schemas import ExtractedFields, FieldCheck
from app.utils.cnpj import is_valid_cnpj, normalize_cnpj
from app.utils.dates import is_valid_date, to_iso
from app.utils.money import parse_money

_ABSENT = "campo ausente (não identificado no texto OCR)"


def validate_extracted(data: ExtractedFields) -> dict[str, FieldCheck]:
    checks: dict[str, FieldCheck] = {}

    # issuer_name
    value = data.issuer_name
    if value is None:
        checks["issuer_name"] = FieldCheck(valid=True, reason=_ABSENT)
    elif len(value.strip()) >= 2 and any(c.isalpha() for c in value):
        checks["issuer_name"] = FieldCheck(valid=True)
    else:
        checks["issuer_name"] = FieldCheck(valid=False, reason="razão social inválida")

    # cnpj
    value = data.cnpj
    if value is None:
        checks["cnpj"] = FieldCheck(valid=True, reason=_ABSENT)
    elif is_valid_cnpj(value):
        checks["cnpj"] = FieldCheck(valid=True)
    else:
        checks["cnpj"] = FieldCheck(
            valid=False, reason="CNPJ inválido (formato ou dígitos verificadores)"
        )

    # issue_date
    value = data.issue_date
    if value is None:
        checks["issue_date"] = FieldCheck(valid=True, reason=_ABSENT)
    elif is_valid_date(value):
        checks["issue_date"] = FieldCheck(valid=True)
    else:
        checks["issue_date"] = FieldCheck(
            valid=False, reason="data inválida ou fora da faixa esperada"
        )

    # invoice_number
    value = data.invoice_number
    if value is None:
        checks["invoice_number"] = FieldCheck(valid=True, reason=_ABSENT)
    elif str(value).strip():
        checks["invoice_number"] = FieldCheck(valid=True)
    else:
        checks["invoice_number"] = FieldCheck(valid=False, reason="número da nota vazio")

    # total_value
    value = data.total_value
    if value is None:
        checks["total_value"] = FieldCheck(valid=True, reason=_ABSENT)
    elif parse_money(value) is not None:
        checks["total_value"] = FieldCheck(valid=True)
    else:
        checks["total_value"] = FieldCheck(
            valid=False, reason="valor monetário inválido ou ambíguo"
        )

    return checks


def normalize_extracted(data: ExtractedFields) -> ExtractedFields:
    """Normalização *best-effort* após a validação (não inventa dados)."""
    out = data.model_copy()

    if out.issuer_name is not None:
        out.issuer_name = out.issuer_name.strip() or None

    if out.cnpj is not None and is_valid_cnpj(out.cnpj):
        out.cnpj = normalize_cnpj(out.cnpj)

    if out.issue_date is not None and is_valid_date(out.issue_date):
        out.issue_date = to_iso(out.issue_date)

    if out.invoice_number is not None:
        out.invoice_number = str(out.invoice_number).strip() or None

    if out.total_value is not None:
        money = parse_money(out.total_value)
        out.total_value = float(money) if money is not None else None

    return out
