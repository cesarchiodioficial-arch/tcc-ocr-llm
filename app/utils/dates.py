"""Parsing e validação de data de emissão.

Formatos aceitos são explícitos para evitar interpretação ambígua. Datas em
formato brasileiro (dia/mês/ano) têm prioridade sobre mês/dia/ano.
Saída interna: ISO `YYYY-MM-DD` (ESPECIFICACAO.md §8).
"""

from __future__ import annotations

from datetime import date, datetime

_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%Y/%m/%d",
)

_MIN_YEAR = 2000
_MAX_YEAR = 2100


def parse_date(raw: object) -> date | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    for fmt in _FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def to_iso(raw: object) -> str | None:
    parsed = parse_date(raw)
    return parsed.isoformat() if parsed else None


def is_valid_date(raw: object, *, min_year: int = _MIN_YEAR, max_year: int = _MAX_YEAR) -> bool:
    parsed = parse_date(raw)
    return bool(parsed and min_year <= parsed.year <= max_year)
