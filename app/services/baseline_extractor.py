"""Baseline OCR-only — Experimento A (ESPECIFICACAO.md §15, PLANO conflito C-11).

Extrai os 5 campos essenciais do texto OCR usando apenas heurísticas /
expressões regulares, SEM LLM. Serve de linha de base para comparar com o
fluxo completo OCR + LLM (Experimento B).

Não é um endpoint: é usado offline por `scripts/evaluate.py`.
"""

from __future__ import annotations

import re

from app.models.schemas import ExtractedFields
from app.utils.cnpj import is_valid_cnpj, normalize_cnpj
from app.utils.dates import to_iso
from app.utils.money import parse_money

_CNPJ_RE = re.compile(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}")
_DATE_RE = re.compile(r"\b(\d{2}[/\-.]\d{2}[/\-.]\d{4}|\d{4}-\d{2}-\d{2})\b")
_MONEY_RE = re.compile(r"(?:R\$\s*)?\d{1,3}(?:\.\d{3})*,\d{2}\b|\b\d+\.\d{2}\b")
_INVOICE_RE = re.compile(
    r"(?:nota\s+fiscal|nf-?e?|n[ºo°.]|numero|número)\s*[:.\-]?\s*(\d{1,15})",
    re.IGNORECASE,
)
_NOISE_TERMS = ("cnpj", "http", "www", "data", "valor", "total")


def _find_cnpj(text: str) -> str | None:
    fallback: str | None = None
    for match in _CNPJ_RE.finditer(text):
        digits = normalize_cnpj(match.group(0))
        if not digits or len(digits) != 14:
            continue
        if is_valid_cnpj(digits):
            return digits
        fallback = fallback or digits
    return fallback


def _find_date(text: str) -> str | None:
    match = _DATE_RE.search(text)
    return to_iso(match.group(1)) if match else None


def _find_total(text: str) -> float | None:
    values = [parse_money(token) for token in _MONEY_RE.findall(text)]
    values = [v for v in values if v is not None]
    if not values:
        return None
    # heurística: o valor total costuma ser o maior valor monetário do texto
    return float(max(values))


def _find_invoice(text: str) -> str | None:
    match = _INVOICE_RE.search(text)
    if not match:
        return None
    number = match.group(1)
    return number.lstrip("0") or number


def _find_issuer(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if len(stripped) < 5:
            continue
        if sum(c.isalpha() for c in stripped) < 5:
            continue
        if _CNPJ_RE.search(stripped):
            continue
        lowered = stripped.lower()
        if any(term in lowered for term in _NOISE_TERMS):
            continue
        return stripped
    return None


def baseline_extract(ocr_text: str) -> ExtractedFields:
    text = ocr_text or ""
    return ExtractedFields(
        issuer_name=_find_issuer(text),
        cnpj=_find_cnpj(text),
        issue_date=_find_date(text),
        invoice_number=_find_invoice(text),
        total_value=_find_total(text),
    )
