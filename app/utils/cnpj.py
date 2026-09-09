"""Validação de CNPJ: formato (14 dígitos) + dígitos verificadores (módulo 11).

A validação de CNPJ é responsabilidade da APLICAÇÃO, nunca do LLM
(CLAUDE.md §7 / ESPECIFICACAO.md §8).
"""

from __future__ import annotations

import re

_W1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_W2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def normalize_cnpj(raw: object) -> str | None:
    if raw is None:
        return None
    digits = re.sub(r"\D", "", str(raw))
    return digits or None


def _check_digit(digits: str, weights: list[int]) -> str:
    total = sum(int(d) * w for d, w in zip(digits, weights))
    rest = total % 11
    return "0" if rest < 2 else str(11 - rest)


def is_valid_cnpj(raw: object) -> bool:
    digits = normalize_cnpj(raw)
    if not digits or len(digits) != 14:
        return False
    if digits == digits[0] * 14:
        return False
    d1 = _check_digit(digits[:12], _W1)
    d2 = _check_digit(digits[:12] + d1, _W2)
    return digits[12] == d1 and digits[13] == d2


def format_cnpj(raw: object) -> str | None:
    digits = normalize_cnpj(raw)
    if not digits or len(digits) != 14:
        return None
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
