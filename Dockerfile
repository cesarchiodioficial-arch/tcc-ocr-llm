# Imagem única da aplicação Python (API + pipeline OCR/LLM/validação).
# Python 3.14-slim: mesma linha usada nos testes locais da POC.
FROM python:3.14-slim

# Dependências de sistema:
# - tesseract-ocr + tesseract-ocr-por: OCR com idioma português (ESPECIFICACAO.md §6)
# - poppler-utils: conversão de PDF em imagem para o pdf2image (PLANO conflito C-05)
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-por \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/

RUN mkdir -p /data/uploads

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
