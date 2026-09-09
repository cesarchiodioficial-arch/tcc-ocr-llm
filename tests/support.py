"""Utilidades de teste: gera nota fiscal sintética e o texto OCR de referência.

Nada aqui usa notas fiscais reais (CLAUDE.md §9).
"""

from __future__ import annotations

import io

from PIL import Image, ImageDraw

# Valores de referência da nota sintética usada nos testes.
SAMPLE_REFERENCE = {
    "issuer_name": "POSTO AVENIDA LTDA",
    "cnpj": "12345678000195",
    "issue_date": "2026-01-31",
    "invoice_number": "12345",
    "total_value": 245.90,
}

SAMPLE_OCR_TEXT = (
    "POSTO AVENIDA LTDA\n"
    "CNPJ: 12.345.678/0001-95\n"
    "NOTA FISCAL No 12345\n"
    "Data de emissao: 31/01/2026\n"
    "Combustivel .......... 200,00\n"
    "Servicos ............. 45,90\n"
    "VALOR TOTAL R$ 245,90\n"
)


def make_invoice_png() -> bytes:
    """Renderiza uma nota fiscal sintética simples em PNG (fonte bitmap padrão)."""
    width, height = 900, 500
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    lines = [
        "POSTO AVENIDA LTDA",
        "CNPJ: 12.345.678/0001-95",
        "NOTA FISCAL No 12345",
        "Data de emissao: 31/01/2026",
        "",
        "Combustivel .......... 200,00",
        "Servicos ............. 45,90",
        "",
        "VALOR TOTAL R$ 245,90",
    ]
    y = 30
    for line in lines:
        draw.text((40, y), line, fill="black")
        y += 45
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def make_blank_png() -> bytes:
    image = Image.new("RGB", (300, 200), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
