# SESSION_STATE — estado da POC entre sessões

> Atualizar este arquivo ao final de cada sessão ou antes de trocar de sessão
> (ver `CLAUDE.md` → "Gestão de contexto e continuidade").

## Fase atual

**POC implementada e commitada.** O commit `dfc5542` ("POC: extração de dados de
notas fiscais com OCR + LLM") está em `origin/main` com a aplicação completa.

## Próxima ação

1. Rodar `docker compose up --build` em uma máquina com Docker e validar o fluxo
   real (MongoDB + Tesseract + Poppler).
2. Configurar `LLM_API_KEY` real em `.env` (nunca em `.env.example`) e validar a
   integração OpenAI (`RUN_LLM_REAL=1 pytest -m llm_real`).
3. Preencher `evaluation/reference_values.csv` e rodar `scripts/evaluate.py`
   (Experimento A vs B) dentro do container.

## Testes e resultados (última execução local — Python 3.14, venv)

- `pytest` → **106 passed, 2 skipped** (skips: `ocr_real`, `llm_real`), cobertura ~88%.
- `utils/` e `validation_service.py`: 100% de cobertura.
- App sobe via `uvicorn app.main:app`; `/health`, `/openapi.json`, `/docs` respondem.
- Fluxo ponta a ponta validado com `mongomock` + `FakeLLMClient`:
  upload → OCR (stub) → LLM (fake) → validação → `VALIDATION_PENDING` →
  correção humana (`corrections[]`, `VALIDATED`) → reprocessamento (`reprocess_count`).

## Pendências / limitações (ver README §10)

- Docker não executado no ambiente de desenvolvimento (sem Docker) — arquivos
  validados sinteticamente (`docker-compose.yml` parseia; `Dockerfile` padrão).
- OCR real do Tesseract e LLM real da OpenAI ainda não validados fim a fim.
- `evaluation`: baseline (Experimento A) coberto por teste unitário; execução com
  Tesseract real pendente.

## Decisões (permanentes — ver `CLAUDE.md` §19 / `ESPECIFICACAO.md` §22)

Processamento síncrono · FastAPI + Uvicorn · upload 10 MB · pdf2image + Poppler ·
Experimento A = baseline OCR-only (regex) · LLM: OpenAI, `LLM_MODEL` por env ·
API key só em variável de ambiente.

## Git

- Branch principal: `main` (contém a POC completa).
- `origin`: `github.com/cesarchiodioficial-arch/tcc-ocr-llm`.
