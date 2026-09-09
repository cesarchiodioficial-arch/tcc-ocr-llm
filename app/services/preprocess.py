"""Pré-processamento simples de imagem para OCR (ESPECIFICACAO.md §6).

Apenas técnicas justificadas e leves. O pré-processamento é dividido em dois
níveis para não prejudicar documentos que já estão em boa qualidade:

- `OCR_PREPROCESS=true`  (padrão): tons de cinza, upscale de imagens pequenas,
  autocontraste e remoção leve de ruído — operações de baixo risco.
- `OCR_BINARIZE=true`    (padrão: false): binarização por limiar. Pode ajudar
  em digitalizações ruins, mas destrói texto de imagens com iluminação
  irregular — por isso é opt-in e deve ser avaliada no experimento.

Sem visão computacional complexa.
"""

from __future__ import annotations

from PIL import Image, ImageFilter, ImageOps

_MIN_SIDE = 1000
_BIN_THRESHOLD = 160


def preprocess(image: Image.Image, *, binarize: bool = False) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")

    width, height = image.size
    smallest = min(width, height)
    if smallest and smallest < _MIN_SIDE:
        scale = _MIN_SIDE / smallest
        image = image.resize((int(width * scale), int(height * scale)))

    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.MedianFilter(size=3))

    if binarize:
        image = image.point(lambda p: 255 if p > _BIN_THRESHOLD else 0)

    return image
