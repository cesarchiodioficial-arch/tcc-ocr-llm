# SESSION_STATE — estado da POC entre sessões

> Atualizar este arquivo ao final de cada sessão ou antes de trocar de sessão
> (ver `CLAUDE.md` → "Gestão de contexto e continuidade").

## Fase atual

**POC implementada + auditoria + correções da auditoria aplicadas.**

- `dfc5542` — POC completa (em `origin/main`).
- `ae6e41b` — rotina de continuidade entre sessões (branch `chore/session-continuity-docs`).
- Correções da auditoria (P-01 … P-27) — aplicadas neste branch, aguardando commit/merge.

## Correções da auditoria aplicadas

| Grupo | Itens | Estado |
|---|---|---|
| Reprodutibilidade | P-01 (suíte hermética, ignora `.env`), P-17 (asserções semânticas) | ✅ verificado (mesmo resultado com/sem `.env`) |
| Falhas | P-05 (Mongo mid-pipeline → 503, nunca 500), P-08 (reprocesso limpa dados antigos), P-15 (PDF truncado → 422) | ✅ com testes |
| Correção humana | P-09 (normaliza data→ISO / CNPJ→dígitos no `PUT`) | ✅ com testes |
| Experimento | P-02 (taxa de sucesso + correções necessárias no `evaluate.py`; novo `corrections_report.py`), P-03 (perfil `eval` no compose com bind-mount), P-06 (metodologia documentada), P-07 (baseline honesto) | ✅ com testes |
| Contrato/API | P-10 (OpenAPI documenta 400/404/409/413/415/422/503 + envelope; /health 503) | ✅ com testes |
| Testes | P-11 (PDF: 1 pág, multipág, corrompido; `source_pages`), P-18 (integração com JSON real do LLM) | ✅ |
| Qualidade | P-12 (`OCR_BINARIZE` opt-in), P-13 (backoff no retry + 429), P-19 (`.gitignore` `.env.*`), P-20 (`LLM_EXCERPT_CHARS`), P-21 (código morto removido), P-24 (status padronizado), P-25/P-26 (README, `.env.example` `LLM_PROVIDER=fake`) | ✅ |
| Config | P-04 (`.env` local do usuário com modelo inválido — corrigir manualmente + **rotacionar API key**) | ⚠️ ação do usuário |

Suíte: **128 passed, 5 skipped** (`ocr_real`/`llm_real` pulam sem Tesseract/chave).
Cobertura ~91% (utils, validation, schemas, preprocess = 100%).

## Próxima ação

1. `docker compose up --build` numa máquina com Docker; validar health/upload/PUT/reprocess reais.
2. `.env`: `LLM_PROVIDER=openai` + `LLM_API_KEY` + `LLM_MODEL` real → validar Experimento B.
3. Preencher `evaluation/reference_values.csv` e rodar `docker compose --profile eval run --rm eval ...`.
4. Merge do branch de correções.

## Validações ainda NÃO executadas (ambiente sem Docker/Tesseract/OpenAI)

Docker build/up · Tesseract real · MongoDB real · OpenAI real · Postman com app no ar ·
experimento real. Tudo o mais foi verificado com `mongomock` + `FakeLLMClient` + OCR stub.

## Decisões permanentes

Ver `CLAUDE.md` §19 / `ESPECIFICACAO.md` §22. Síncrono · FastAPI+Uvicorn · upload 10 MB ·
pdf2image+Poppler · Experimento A = baseline OCR-only · LLM OpenAI, `LLM_MODEL` por env ·
API key só em variável de ambiente · uso mono-usuário.
