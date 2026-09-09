"""Baseline OCR-only — Experimento A (ESPECIFICACAO.md §15, PLANO conflito C-11).

Extrai os 5 campos essenciais do texto OCR usando apenas heurísticas /
expressões regulares, SEM LLM. Serve de linha de base para comparar com o
fluxo completo OCR + LLM (Experimento B).

As heurísticas são deliberadamente simples (é o objetivo do Experimento A:
mostrar o limite de uma abordagem sem interpretação semântica), porém fazem
um esforço honesto — não são um "strawman":
- CNPJ: primeiro CNPJ com dígitos verificadores válidos;
- emissor: linha não-ruído mais próxima do primeiro CNPJ (acima, senão a 1ª linha);
- data: primeira data reconhecível;
- número da NF: número após rótulo ("nota fiscal", "nº", "número"…);
- valor total: valor monetário após rótulo "total"/"valor a pagar"; senão o maior.

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
    r"(?:nota\s+fiscal(?:\s+eletr[oô]nica)?|nf-?e?|n[ºo°.]|n[uú]mero)\s*[:.\-]?\s*(\d{1,15})",
    re.IGNORECASE,
)
_TOTAL_LABEL_RE = re.compile(
    r"(?:valor\s+total|total\s+(?:da\s+)?nota|total\s+geral|valor\s+a\s+pagar|total)\s*"
    r"[:.\-]?\s*(?:R\$\s*)?((?:\d{1,3}(?:\.\d{3})*|\d+),\d{2})",
    re.IGNORECASE,
)
_NOISE_TERMS = (
    "cnpj", "cpf", "http", "www", "data", "valor", "total", "inscri", "danfe",
    "documento auxiliar", "chave de acesso", "protocolo", "sefaz", "secretaria",
)


def _cnpj_matches(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for match in _CNPJ_RE.finditer(text):
        digits = normalize_cnpj(match.group(0))
        if digits and len(digits) == 14:
            out.append((match.start(), digits))
    return out


def _find_cnpj(text: str) -> str | None:
    fallback: str | None = None
    for _, digits in _cnpj_matches(text):
        if is_valid_cnpj(digits):
            return digits
        fallback = fallback or digits
    return fallback


def _find_date(text: str) -> str | None:
    match = _DATE_RE.search(text)
    return to_iso(match.group(1)) if match else None


def _looks_like_noise(line: str) -> bool:
    lowered = line.lower()
    if _CNPJ_RE.search(line):
        return True
    if any(term in lowered for term in _NOISE_TERMS):
        return True
    return sum(c.isalpha() for c in line) < 5


def _find_issuer(text: str) -> str | None:
    lines = text.splitlines()
    cnpj_matches = _cnpj_matches(text)
    if cnpj_matches:
        # linha do 1º CNPJ
        offset = cnpj_matches[0][0]
        line_idx = text[:offset].count("\n")
        # procura para cima a 1ª linha não-ruído
        for i in range(line_idx, -1, -1):
            candidate = lines[i].strip()
            if candidate and not _looks_like_noise(candidate):
                return candidate
    for line in lines:
        candidate = line.strip()
        if len(candidate) >= 5 and not _looks_like_noise(candidate):
            return candidate
    return None


def _find_invoice(text: str) -> str | None:
    match = _INVOICE_RE.search(text)
    return match.group(1) if match else None


def _find_total(text: str) -> float | None:
    labelled = _TOTAL_LABEL_RE.search(text)
    if labelled:
        value = parse_money(labelled.group(1))
        if value is not None:
            return float(value)
    values = [parse_money(token) for token in _MONEY_RE.findall(text)]
    values = [v for v in values if v is not None]
    return float(max(values)) if values else None


def baseline_extract(ocr_text: str) -> ExtractedFields:
    text = ocr_text or ""
    return ExtractedFields(
        issuer_name=_find_issuer(text),
        cnpj=_find_cnpj(text),
        issue_date=_find_date(text),
        invoice_number=_find_invoice(text),
        total_value=_find_total(text),
    )
