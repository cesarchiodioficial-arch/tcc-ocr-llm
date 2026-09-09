"""Pré-processamento simples de imagem para OCR (ESPECIFICACAO.md §6).

Apenas técnicas justificadas e leves: tons de cinza, redimensionamento,
autocontraste, remoção de ruído e binarização. Sem visão computacional
complexa. Pode ser desligado por `OCR_PREPROCESS=false`.
"""

from __future__ import annotations

from PIL import Image, ImageFilter, ImageOps

_MIN_SIDE = 1000
_BIN_THRESHOLD = 140


def preprocess(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")

    width, height = image.size
    smallest = min(width, height)
    if smallest and smallest < _MIN_SIDE:
        scale = _MIN_SIDE / smallest
        image = image.resize((int(width * scale), int(height * scale)))

    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.MedianFilter(size=3))
    image = image.point(lambda p: 255 if p > _BIN_THRESHOLD else 0)
    return image
