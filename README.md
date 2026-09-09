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
| LLM (camada isolada) | `app/services/llm/`, `llm_service.py` | interface `LLMClient`, `OpenAIClient`, `FakeLLMClient`, prompt, parsing, retry com backoff |
| Validação sistêmica | `app/services/validation_service.py`, `app/utils/` | schema + CNPJ (dígitos verificadores) + data (ISO) + valor monetário |
| Baseline OCR-only | `app/services/baseline_extractor.py` | Experimento A (heurísticas/regex, sem LLM) |
| Persistência | `app/repository/documents_repository.py` | MongoDB (`pymongo`), erros explícitos |
| Armazenamento | `app/storage/files.py` | guarda o arquivo original (permite reprocessar) |
| Avaliação | `scripts/evaluate.py`, `scripts/corrections_report.py` | Experimento A × B; correções humanas reais |

Campos essenciais: `issuer_name`, `cnpj`, `issue_date`, `invoice_number`, `total_value`.

---

## 2. Por que estas escolhas

- **FastAPI + Uvicorn**: multipart nativo, OpenAPI automático, validação por Pydantic. (PLANO C-06)
- **Processamento síncrono**: o `POST` só responde após OCR+LLM+validação. (C-01)
- **`pdf2image` + `poppler-utils`**: conversão de PDF simples e bem documentada. (C-05)
- **LLM em camada isolada**: nunca é fonte de verdade; a aplicação valida tudo.
  Provedor inicial **OpenAI**, modelo em `LLM_MODEL`. `FakeLLMClient` nos testes. (C-06)
- **MongoDB**: base orientada a documentos, adequada a estruturas variáveis.
- **`mongomock`** nos testes: sem servidor real na suíte automatizada.

Fora de escopo (POC): itens/impostos, NF-e/SEFAZ/ERP, autenticação, filas,
microserviços, Kubernetes, cloud, frontend completo.

**Premissa da POC:** uso **mono-usuário**, sem concorrência. Não há controle de
escrita concorrente sobre o mesmo documento (última escrita vence).

---

## 3. Como executar (Docker — recomendado)

Pré-requisitos: Docker + Docker Compose.

```bash
cp .env.example .env
# 1ª execução: deixe LLM_PROVIDER=fake (não precisa de chave).
# Para usar o LLM real: LLM_PROVIDER=openai, LLM_API_KEY=<sua chave>,
#   LLM_MODEL=<modelo OpenAI REAL, ex.: gpt-4o-mini>

docker compose up --build
```

- API: <http://localhost:8000>
- Documentação interativa (Swagger): <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

O `Dockerfile` já instala `tesseract-ocr`, `tesseract-ocr-por` e `poppler-utils`.

### Teste rápido do fluxo

```bash
curl http://localhost:8000/health

# upload (nota sintética que acompanha o repositório)
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@samples/nota-sintetica-001.png"

# consulta (troque <id> pelo _id retornado)
curl http://localhost:8000/api/v1/documents/<id>

# correção + confirmação humana
curl -X PUT http://localhost:8000/api/v1/documents/<id> \
  -H "Content-Type: application/json" \
  -d '{"extracted_data": {"total_value": 245.90}, "validated": true}'

# reprocessamento
curl -X POST http://localhost:8000/api/v1/documents/<id>/reprocess
```

---

## 4. Como executar (local, sem Docker)

Requer Python 3.14 e **Tesseract + Poppler instalados no sistema** para o OCR
real (no Windows, informe `POPPLER_PATH` no `.env` se necessário).

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt   # Windows
# source .venv/bin/activate && python -m pip install -r requirements-dev.txt  # Linux/Mac

# MongoDB local em mongodb://localhost:27017 (ou ajuste MONGO_URI)
.venv\Scripts\python -m uvicorn app.main:app --reload
```

---

## 5. Como testar

```bash
.venv\Scripts\python -m pytest              # suíte completa
.venv\Scripts\python -m pytest tests/unit   # só regras de domínio e validação
```

- A suíte é **hermética**: fixa todas as variáveis de ambiente que usa e
  **ignora qualquer `.env`** presente — o resultado é o mesmo com ou sem `.env`.
- Testes usam **`FakeLLMClient`** e **`mongomock`** (sem rede, chave ou servidor).
- `tests/integration/test_ocr_real.py` (marca `ocr_real`): roda Tesseract/Poppler
  **de verdade** se instalados (PNG, PDF 1 página, PDF multipágina, PDF corrompido);
  senão, `skip`.
- `tests/integration/test_llm_real.py` (marca `llm_real`): só roda com
  `RUN_LLM_REAL=1` e `LLM_API_KEY` válida.

---

## 6. API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | disponibilidade (app + MongoDB + config do LLM) |
| `POST` | `/api/v1/documents` | upload `multipart/form-data` (`file`) + processamento síncrono |
| `GET` | `/api/v1/documents/{id}` | status, texto OCR, dados, validação, metadados |
| `PUT` | `/api/v1/documents/{id}` | correção e/ou confirmação humana (`validated: true`) |
| `POST` | `/api/v1/documents/{id}/reprocess` | reprocessa a partir do arquivo original |

- Correção humana **normaliza** os valores (data→ISO, CNPJ→dígitos) igual ao pipeline.
- Falha do MongoDB (inclusive no meio do pipeline) → **HTTP 503** com envelope,
  nunca 500; nada é reportado como persistido sem gravação.
- Envelope de erro: `{"error": {"code": "...", "message": "...", "stage": "...|null"}}`.
  Todos os códigos (400/404/409/413/415/422/503) estão no [`docs/openapi.json`](docs/openapi.json)
  (regenerar: `python -m scripts.export_openapi`).

Estados: `RECEIVED → PROCESSING → OCR_COMPLETED → EXTRACTED → VALIDATION_PENDING →
VALIDATED`; `FAILED` (causa em `error.stage`); `REPROCESSING`.

---

## 7. Postman

`postman/TCC-OCR-LLM.postman_collection.json` (Collection v2.1). Importe no
Postman/Insomnia.

- Variáveis: `base_url` (default `http://localhost:8000`), `document_id`
  (preenchida automaticamente pelo request de upload).
- Requests: Health, Upload, Consultar, Correção (PUT), Confirmação (PUT
  `validated=true`), Reprocessar.
- No **upload**, selecione o arquivo (`samples/nota-sintetica-001.png`) no campo
  `file` — o Postman não versiona o caminho do arquivo.

---

## 8. Avaliação experimental (Experimento A × Experimento B)

Ver [`evaluation/README.md`](evaluation/README.md). Resumo:

1. coloque as notas do experimento em `samples/`;
2. `cp evaluation/reference_values.example.csv evaluation/reference_values.csv`
   e preencha os valores esperados;
3. rode a comparação (usa o **mesmo texto OCR** para A e B):

   ```bash
   docker compose --profile eval run --rm eval \
     -m scripts.evaluate --reference evaluation/reference_values.csv --dir samples
   ```

   Saída em `evaluation/results/`: **taxa de acerto por campo**, **taxa de
   documentos processados com sucesso**, **correções necessárias** e **tempo**,
   para A e B.

4. as **correções humanas reais** (feitas via `PUT` ao submeter as notas pela
   API/Postman) são agregadas do MongoDB:

   ```bash
   docker compose --profile eval run --rm eval -m scripts.corrections_report
   ```

O software **não inventa** valores de referência nem resultados.

---

## 9. Configuração (variáveis de ambiente)

Todas em [`.env.example`](.env.example). Destaques:

| Variável | Default | Observação |
|---|---|---|
| `MAX_UPLOAD_MB` | `10` | limite de upload |
| `MONGO_URI` | `mongodb://mongo:27017` | no compose aponta para o serviço `mongo` |
| `OCR_LANG` | `por` | idioma do Tesseract (fallback `eng`) |
| `OCR_PREPROCESS` | `true` | cinza + upscale + autocontraste + ruído (baixo risco) |
| `OCR_BINARIZE` | `false` | binarização por limiar — opt-in (pode piorar imagens boas) |
| `LLM_PROVIDER` | `fake` | `fake` (1ª execução) ou `openai` |
| `LLM_API_KEY` | `changeme` | **somente no `.env`, nunca versionar** |
| `LLM_MODEL` | `gpt-4o-mini` | **use um modelo OpenAI real** |
| `LLM_MAX_RETRIES` | `2` | tentativas extras em resposta inválida |
| `LLM_RETRY_BACKOFF_SECONDS` | `0.5` | backoff exponencial entre tentativas |

Segredos **nunca** ficam no código. `.env` e `.env.*` estão no `.gitignore`.

---

## 10. Limitações conhecidas da POC

- **OCR** depende da qualidade da imagem; layouts muito diferentes podem exigir
  ajuste de pré-processamento (`OCR_BINARIZE`) ou do prompt. Recomenda-se rodar o
  experimento **com e sem** `OCR_BINARIZE` e comparar.
- O **LLM** pode errar ou omitir campos — por isso a validação sistêmica e a
  conferência humana são obrigatórias no fluxo.
- **`total_value` é armazenado como número de ponto flutuante** (`float`). É
  suficiente para a POC (não há aritmética sobre valores); `Decimal` seria mais
  rigoroso e fica como evolução futura.
- **Experimento A** usa um baseline por heurística/regex — é deliberadamente
  simples (é o ponto do experimento), mas faz um esforço honesto (CNPJ com
  dígitos verificadores, emissor próximo ao CNPJ, total rotulado). Deve ser
  descrito como "baseline OCR-only" no TCC.
- A comparação A × B é **offline sobre o mesmo texto OCR**; a persistência e a
  conferência humana descritas no Artigo §3.12 são exercidas pela API e agregadas
  por `scripts/corrections_report.py`.
- Sem **frontend**: validação humana via `PUT` (curl/Postman).
- Processamento **síncrono**: uploads de PDFs grandes deixam a requisição lenta.
- Uso **mono-usuário** (sem controle de concorrência — ver §2).
- Escopo restrito aos **5 campos essenciais**.
- A suíte automatizada usa `mongomock` e `FakeLLMClient`; a validação com
  **MongoDB real, Tesseract real e OpenAI real** é feita ao subir o
  `docker compose` e ao rodar os testes marcados `ocr_real` / `llm_real`.
- `starlette` 1.6 emite um `DeprecationWarning` sobre o `TestClient` — não
  afeta a execução.

---

## 11. Estrutura do repositório

```text
app/            aplicação (API + serviços + repositório)
scripts/        evaluate.py, corrections_report.py, export_openapi.py, make_sample.py
evaluation/     modelo de referência + instruções do experimento
postman/        coleção Postman v2.1
docs/           openapi.json, SESSION_STATE.md
samples/        nota sintética de exemplo (sem dados reais)
tests/          unit/ e integration/
Dockerfile, docker-compose.yml, requirements*.txt, .env.example
```
