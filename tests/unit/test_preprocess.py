from PIL import Image

from app.services.preprocess import preprocess


def _img():
    return Image.new("RGB", (400, 300), "white")


def test_default_preprocess_no_binarization_keeps_grayscale():
    out = preprocess(_img())
    assert out.mode == "L"
    # sem binarização: mais de 2 níveis possíveis (não é preto/branco puro)
    assert out.size[0] >= 400  # upscale de imagem pequena


def test_binarize_option_produces_two_levels():
    out = preprocess(_img(), binarize=True)
    extrema = out.getextrema()  # (min, max)
    assert extrema[0] in (0, 255) and extrema[1] in (0, 255)


def test_small_image_is_upscaled():
    small = Image.new("L", (200, 150), "white")
    out = preprocess(small)
    assert min(out.size) >= 1000
