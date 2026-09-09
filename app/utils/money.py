"""Parsing de valor monetário.

Regra da ESPECIFICACAO.md §8: `total_value` deve ser numérico válido e
**não pode aceitar parsing ambíguo**. Casos ambíguos (ex.: `1.234` — sem
como saber se é milhar ou decimal) retornam `None` (rejeição).
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_ALLOWED = re.compile(r"[0-9.,]+")


def parse_money(raw: object) -> Decimal | None:
    if raw is None:
        return None

    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        value = Decimal(str(raw))
        return value if value >= 0 else None

    text = str(raw).strip()
    if not text:
        return None
    text = re.sub(r"(?i)r\$", "", text).strip()
    text = re.sub(r"\s", "", text)
    if not text or not _ALLOWED.fullmatch(text):
        return None

    has_comma = "," in text
    has_dot = "." in text

    if has_comma and has_dot:
        # o último separador é o decimal
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif has_comma:
        parts = text.split(",")
        if len(parts) == 2 and len(parts[1]) == 2:
            text = text.replace(",", ".")
        else:
            # "1,234" ou "1,2" ou múltiplas vírgulas: ambíguo
            return None
    elif has_dot:
        parts = text.split(".")
        if len(parts) > 2:
            # "1.234.567" → separador de milhar
            text = text.replace(".", "")
        elif len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) <= 3:
            # "1.234" → ambíguo (milhar vs decimal)
            return None
        # senão: decimal normal ("1234.56", "12.5")

    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    return value if value >= 0 else None
