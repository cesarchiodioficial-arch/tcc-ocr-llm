# POC — Extração automática de dados em notas fiscais com OCR + LLM

Prova de conceito do TCC **"Sistema inteligente de extração automática de dados
em notas fiscais utilizando OCR e Large Language Models"** (UNIARA, 2026).

Fluxo implementado:

```
documento (PDF/PNG/JPG) → Tesseract OCR → LLM → validação sistêmica → validação humana → MongoDB
```

Aplicação única (monólito modular) em **Python + FastAPI**, com processamento
**síncrono**, reproduzível localmente via **Docker Compose**.

---

## 1. O que existe

| Módulo | Pasta | Papel |
|---|---|---|
| API REST | `app/api/` | rotas, validação de entrada, códigos HTTP, envelope de erro |
| Orquestrador | `app/services/pipeline.py` | coordena OCR → LLM → validação, controla `status` e tempos |
| OCR | `app/services/ocr_service.py`, `preprocess.py` | PDF→imagem (`pdf2image`+Poppler), pré-processamento simples, Tesseract (`por`) |
| LLM (camada isolada) | `app/services/llm/`, `llm_service.py` | interface `LLMClient`, `OpenAIClient`, `FakeLLMClient`, prompt, parsing, retry |
| Validação sistêmica | `app/services/validation_service.py`, `app/utils/` | schema + CNPJ (dígitos verificadores) + data + valor monetário |
| Baseline OCR-only | `app/services/baseline_extractor.py` | Experimento A (heurísticas/regex, sem LLM) |
| Persistência | `app/repository/documents_repository.py` | MongoDB (`pymongo`), erros explícitos |
| Armazenamento | `app/storage/files.py` | guarda o arquivo original (permite reprocessar) |
| Avaliação | `scripts/evaluate.py` | Experimento A vs B, métricas e tabelas |

Campos essenciais: `issuer_name`, `cnpj`, `issue_date`, `invoice_number`, `total_value`.

---

## 2. Por que estas escolhas

- **FastAPI + Uvicorn**: multipart nativo, OpenAPI automático (`/openapi.json`,
  `/docs`), validação por Pydantic. (PLANO, decisão C-06)
- **Processamento síncrono**: o `POST` só responde após OCR+LLM+validação —
  menos código, testes diretos, fácil de explicar. (C-01)
- **`pdf2image` + `poppler-utils`**: conversão de PDF simples e bem documentada. (C-05)
- **LLM em camada isolada**: nunca é fonte de verdade; a aplicação valida tudo.
  Provedor inicial **OpenAI**, modelo em `LLM_MODEL`. `FakeLLMClient` nos testes. (C-06/LLM)
- **MongoDB**: base orientada a documentos, adequada a estruturas variáveis.
- **`mongomock`** nos testes: sem servidor real para a suíte automatizada.

Fora de escopo (POC): itens/impostos, NF-e/SEFAZ/ERP, autenticação, filas,
microserviços, Kubernetes, cloud, frontend completo.

---

## 3. Como executar (Docker — recomendado)

Pré-requisitos: Docker + Docker Compose.

```bash
cp .env.example .env
# edite .env e defina LLM_API_KEY (OpenAI) se quiser usar o LLM real.
# Para testar sem chave, use LLM_PROVIDER=fake

docker compose up --build
```

- API: <http://localhost:8000>
- Documentação interativa: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

O `Dockerfile` já instala `tesseract-ocr`, `tesseract-ocr-por` e `poppler-utils`.

### Teste rápido do fluxo

```bash
# 1. health
curl http://localhost:8000/health

# 2. upload (nota sintética que acompanha o repositório)
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@samples/nota-sintetica-001.png"

# 3. consulta (troque <id> pelo _id retornado)
curl http://localhost:8000/api/v1/documents/<id>

# 4. correção humana
curl -X PUT http://localhost:8000/api/v1/documents/<id> \
  -H "Content-Type: application/json" \
  -d '{"extracted_data": {"total_value": 245.90}, "validated": true}'

# 5. reprocessamento
curl -X POST http://localhost:8000/api/v1/documents/<id>/reprocess
```

---

## 4. Como executar (local, sem Docker)

Requer Python 3.14, e **Tesseract + Poppler instalados no sistema** para o OCR
real (no Windows, informe `POPPLER_PATH` no `.env` se necessário).

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt   # Windows
# source .venv/bin/activate && pip install -r requirements-dev.txt  # Linux/Mac

# MongoDB local em mongodb://localhost:27017 (ou ajuste MONGO_URI)
.venv\Scripts\uvicorn app.main:app --reload
```

---

## 5. Como testar

```bash
.venv\Scripts\pytest                 # suíte completa (LLM e OCR reais são pulados)
.venv\Scripts\pytest tests/unit      # só regras de domínio e validação
```

- Testes unitários e de integração usam **`FakeLLMClient`** e **`mongomock`** —
  não precisam de rede, chave nem servidor.
- `tests/integration/test_ocr_real.py` (marca `ocr_real`) roda o Tesseract de
  verdade **se ele estiver instalado**; senão é `skip`.
- `tests/integration/test_llm_real.py` (marca `llm_real`) só roda com
  `RUN_LLM_REAL=1` e `LLM_API_KEY` válida.

A suíte automatizada roda no host (venv). A imagem Docker é enxuta (só
dependências de runtime); para exercitar o OCR real e a avaliação use
`docker compose run --rm app python -m scripts.evaluate ...`.

---

## 6. API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | disponibilidade (app + MongoDB) |
| `POST` | `/api/v1/documents` | upload `multipart/form-data` (`file`) + processamento síncrono |
| `GET` | `/api/v1/documents/{id}` | status, texto OCR, dados, validação, metadados |
| `PUT` | `/api/v1/documents/{id}` | correção e/ou confirmação humana (`validated: true`) |
| `POST` | `/api/v1/documents/{id}/reprocess` | reprocessa a partir do arquivo original |

Envelope de erro: `{"error": {"code": "...", "message": "...", "stage": "...|null"}}`.

Schema completo: [`docs/openapi.json`](docs/openapi.json) (regenerar com
`python -m scripts.export_openapi`).

Estados do documento: `RECEIVED → PROCESSING → OCR_COMPLETED → EXTRACTED →
VALIDATION_PENDING → VALIDATED`; `FAILED` (causa em `error.stage`); `REPROCESSING`.

---

## 7. Postman

`postman/TCC-OCR-LLM.postman_collection.json` (Collection v2.1). Importe no
Postman/Insomnia.

- Variáveis: `base_url` (default `http://localhost:8000`), `document_id`
  (preenchida automaticamente pelo request de upload).
- Requests: Health, Upload, Consultar, Correção (PUT), Confirmação (PUT
  `validated=true`), Reprocessar.

---

## 8. Avaliação experimental (A vs B)

Ver [`evaluation/README.md`](evaluation/README.md). Resumo:

1. coloque as notas do experimento em `samples/`;
2. `cp evaluation/reference_values.example.csv evaluation/reference_values.csv`
   e preencha os valores esperados;
3. `docker compose run --rm app python -m scripts.evaluate --reference evaluation/reference_values.csv --dir samples`;
4. resultados em `evaluation/results/` (CSV + Markdown com taxa de acerto e tempo).

O software **não inventa** valores de referência nem resultados.

---

## 9. Configuração (variáveis de ambiente)

Todas em [`.env.example`](.env.example). Destaques:

| Variável | Default | Observação |
|---|---|---|
| `MAX_UPLOAD_MB` | `10` | limite de upload |
| `MONGO_URI` | `mongodb://mongo:27017` | no compose aponta para o serviço `mongo` |
| `OCR_LANG` | `por` | idioma do Tesseract (fallback `eng`) |
| `OCR_PREPROCESS` | `true` | liga/desliga o pré-processamento simples |
| `LLM_PROVIDER` | `openai` | `openai` ou `fake` |
| `LLM_API_KEY` | `changeme` | **somente no `.env`, nunca versionar** |
| `LLM_MODEL` | `gpt-4o-mini` | modelo configurável |
| `LLM_MAX_RETRIES` | `2` | tentativas extras em resposta inválida |

Segredos **nunca** ficam no código. `.env` está no `.gitignore`.

---

## 10. Limitações conhecidas da POC

- **OCR** depende da qualidade da imagem; layouts muito diferentes podem exigir
  ajuste de pré-processamento ou do prompt.
- O **LLM** pode errar ou omitir campos — por isso a validação sistêmica e a
  conferência humana são obrigatórias no fluxo.
- Sem **frontend**: a validação humana é feita via `PUT` (curl/Postman).
- Processamento **síncrono**: uploads de PDFs grandes deixam a requisição lenta.
- Escopo restrito aos **5 campos essenciais** (sem itens, impostos, etc.).
- A suíte automatizada usa `mongomock` e `FakeLLMClient`; a validação com
  **MongoDB real, Tesseract real e OpenAI real** é feita ao subir o
  `docker compose` e ao rodar os testes marcados `ocr_real` / `llm_real`.
- `starlette` 1.6 emite um `DeprecationWarning` sobre o `TestClient` — não
  afeta a execução.

---

## 11. Estrutura do repositório

```text
app/            aplicação (API + serviços + repositório)
scripts/        evaluate.py, export_openapi.py, make_sample.py
evaluation/     modelo de referência + instruções do experimento
postman/        coleção Postman v2.1
docs/           openapi.json
samples/        nota sintética de exemplo (sem dados reais)
tests/          unit/ e integration/
Dockerfile, docker-compose.yml, requirements*.txt, .env.example
```
