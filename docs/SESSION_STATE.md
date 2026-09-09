# SESSION_STATE — checkpoint da POC

> Consolidação do estado para continuidade entre sessões (ver `CLAUDE.md` →
> "Gestão de contexto e continuidade"). Atualizar ao encerrar / trocar de sessão.
>
> **Última atualização:** checkpoint pós-merge da auditoria.

---

## 1. Resumo em uma linha

POC **completa, testada (128 passed / 5 skipped, cobertura ~91%) e mesclada em
`origin/main`**. Falta apenas **validação em ambiente real** (Docker, Tesseract,
MongoDB, OpenAI, Postman com app no ar, experimento com notas) — nada no
código/config/docs bloqueia essas validações.

---

## 2. Git — estado exato

| Ref | Commit | Conteúdo |
|---|---|---|
| `origin/main` | `bf9bff3` | Merge do PR #2 — **contém TODO o trabalho** |
| ← | `d388326` | fix: correções da auditoria (P-01..P-27) — PR #2 |
| ← | `3cb1c57` | Merge do PR #1 (rotina de continuidade) |
| ← | `ae6e41b` | docs: rotina de continuidade entre sessões |
| ← | `dfc5542` | POC: implementação inicial completa |

- **PR #1** (`chore/session-continuity-docs`) → **merged**.
- **PR #2** (`fix/auditoria-poc`) → **merged**.
- Remote: `https://github.com/cesarchiodioficial-arch/tcc-ocr-llm` (origin, HTTPS, credencial via Git Credential Manager — `git push` funciona; **não há `gh` CLI** neste ambiente — PRs foram criados via API do GitHub).
- Branches locais `fix/auditoria-poc` e `chore/session-continuity-docs` estão **obsoletos** (já mesclados). Nova sessão: `git checkout main && git pull`.
- **Alteração local NÃO commitada:** `docker-compose.yml` — serviço `mongo` ganhou `ports: ["27017:27017"]` (feito pelo usuário, para acessar o Mongo do host, ex.: rodar `scripts/corrections_report.py` fora do container). Correto — commitar junto com este checkpoint.

---

## 3. Fases concluídas

| Fase | Estado |
|---|---|
| 1. Estrutura / base (FastAPI, config, `.env.example`, `.gitignore`) | ✅ |
| 2. Docker (Dockerfile, docker-compose) | ✅ arquivos (não executado — sem Docker no ambiente) |
| 3. Modelo de dados + repositório MongoDB (`pymongo`) | ✅ |
| 4. Upload + validação de arquivo + storage do original | ✅ |
| 5. OCR (Tesseract, pdf2image+Poppler, pré-processamento) | ✅ código (real não executado) |
| 6. LLM (camada isolada, OpenAIClient, FakeLLMClient, prompt, parsing, retry) | ✅ |
| 7. Validação sistêmica (CNPJ/data/valor/schema) | ✅ |
| 8. Persistência do fluxo + estados + tempos + tratamento de falhas | ✅ |
| 9. GET / PUT (correção+confirmação) / reprocess | ✅ |
| 10. Testes (unit + integração) | ✅ 128 passed / 5 skipped |
| 11. OpenAPI + coleção Postman | ✅ |
| 12. Documentação (README, evaluation/README, SESSION_STATE) | ✅ |
| 13. Avaliação experimental (baseline OCR-only + `evaluate.py` + `corrections_report.py`) | ✅ ferramentas prontas (experimento real não executado) |
| 14. Git / commit / PR | ✅ 2 PRs mesclados em `main` |
| 15. Auditoria independente + correção completa (P-01..P-27) | ✅ mesclada (PR #2) |

## 4. Fase atual

**Aguardando validação em ambiente real** (item 5 abaixo). Não há mais trabalho
de implementação pendente dentro do escopo do TCC.

---

## 5. O que foi implementado (visão funcional)

Fluxo: **documento (PDF/PNG/JPG) → Tesseract OCR → LLM → validação sistêmica →
validação humana (`PUT`) → MongoDB**. Monólito modular Python + FastAPI,
processamento **síncrono**.

- **API** (`app/api/`): `GET /health`, `POST /api/v1/documents`,
  `GET|PUT /api/v1/documents/{id}`, `POST /api/v1/documents/{id}/reprocess`.
  Envelope de erro único `{"error":{"code","message","stage"}}`; códigos
  400/404/409/413/415/422/503 (todos no OpenAPI).
- **Orquestrador** (`app/services/pipeline.py`): estados
  `RECEIVED→PROCESSING→OCR_COMPLETED→EXTRACTED→VALIDATION_PENDING→VALIDATED`;
  `FAILED` (com `error.stage`); `REPROCESSING`. Falha de MongoDB em qualquer
  ponto → **503**, nunca 500; reprocesso limpa resultados do run anterior.
- **OCR** (`app/services/ocr_service.py`, `preprocess.py`): PDF multipágina via
  `pdf2image`+Poppler; imagens via Pillow; `OCR_PREPROCESS` (cinza/upscale/
  contraste/ruído, padrão on) e `OCR_BINARIZE` (limiar, padrão off).
- **LLM** (`app/services/llm/`, `llm_service.py`): interface `LLMClient`;
  `OpenAIClient` (Chat Completions, `temperature=0`, `response_format=json_object`,
  429/`retry-after`); `FakeLLMClient` (testes; modo baseline opcional);
  prompt anti-alucinação; parsing de JSON em markdown; retry com **backoff
  exponencial** (`LLM_MAX_RETRIES`, `LLM_RETRY_BACKOFF_SECONDS`); `attempts`
  gravado no doc mesmo em falha; `LLM_EXCERPT_CHARS` (padrão 600).
- **Validação** (`app/services/validation_service.py`, `app/utils/`): CNPJ
  (dígitos verificadores), data (multi-formato → ISO), valor monetário
  (BR/EN, **rejeita ambíguo**); `null` é válido; nunca preenche presumido.
  Correção humana (`PUT`) normaliza igual ao pipeline.
- **Persistência** (`app/repository/documents_repository.py`): collection
  `documents`; erros explícitos (`RepositoryUnavailableError`).
- **Experimento A (baseline OCR-only)** (`app/services/baseline_extractor.py`):
  regex/heurística — CNPJ com DV válido, emissor na linha próxima ao 1º CNPJ,
  total rotulado ("VALOR TOTAL"/"VALOR A PAGAR") com fallback ao maior.
- **`scripts/evaluate.py`**: A×B offline sobre o mesmo `ocr_text`; métricas —
  taxa de acerto por campo, **taxa de documentos processados com sucesso**,
  **correções necessárias**, tempo; CSV+MD em `evaluation/results/`.
- **`scripts/corrections_report.py`**: lê o MongoDB e agrega as **correções
  humanas reais** (total, por campo, validados com/sem correção, por status).
- **`scripts/export_openapi.py`**, **`scripts/make_sample.py`**.

---

## 6. Arquivos (94 versionados)

```
app/
  main.py  config.py  logging_config.py
  api/       deps.py  errors.py  routes_documents.py  routes_health.py
  models/    enums.py (DocumentStatus, StrEnum)  schemas.py
  services/  pipeline.py  ocr_service.py  preprocess.py  file_validation.py
             llm_service.py  validation_service.py  baseline_extractor.py  document_factory.py
  services/llm/  base.py (LLMClient)  openai_client.py  fake_client.py
  repository/ documents_repository.py
  storage/   files.py
  utils/     cnpj.py  dates.py  money.py  time_utils.py
scripts/     evaluate.py  corrections_report.py  export_openapi.py  make_sample.py
tests/       conftest.py  support.py   unit/ (8)   integration/ (11)     -> 26 arquivos, 128 testes
evaluation/  README.md  reference_values.example.csv       (reference_values.csv e results/ são gitignored)
postman/     TCC-OCR-LLM.postman_collection.json  (Collection v2.1)
docs/        openapi.json  SESSION_STATE.md
samples/     nota-sintetica-001.png (sintética)  README.md
Dockerfile  docker-compose.yml  requirements.txt  requirements-dev.txt  pytest.ini
.env.example  .gitignore  .gitattributes  .dockerignore
CLAUDE.md  ESPECIFICACAO.md  PLANO_IMPLEMENTACAO.md  README.md  (+ PDFs do TCC, PROMPTs)
```

Arquivo espúrio: **`Especificação.md`** (0 byte, com acento) — duplicata vazia de
`ESPECIFICACAO.md`. Não foi removido (regra: não apagar arquivo do usuário).
Recomenda-se `git rm "Especificação.md"`.

---

## 7. Decisões técnicas aprovadas (permanentes)

Fonte: `CLAUDE.md` §19 / `ESPECIFICACAO.md` §22.

- Processamento **síncrono** no `POST`.
- **FastAPI + Uvicorn**; driver **`pymongo`** (síncrono).
- Limite de upload **10 MB** (`MAX_UPLOAD_MB`).
- PDF→imagem: **`pdf2image` + `poppler-utils`**.
- **Experimento A = baseline OCR-only** (heurística/regex).
- LLM: provedor inicial **OpenAI**, `LLM_MODEL` por variável de ambiente,
  camada `LLMClient` desacoplada, `FakeLLMClient` nos testes.
- API key **exclusivamente** por variável de ambiente; nunca versionada.
- Uso **mono-usuário** (sem controle de concorrência).
- 5 campos essenciais: `issuer_name`, `cnpj`, `issue_date`, `invoice_number`,
  `total_value`. Sem itens/impostos.
- Base do container: `python:3.14-slim` (paridade com o ambiente de testes;
  o PLANO original citava 3.12 — desvio registrado).

---

## 8. Testes — executados nesta máquina

- **Comando:** `.venv\Scripts\python -m pytest`
- **Resultado:** `128 passed, 5 skipped` — cobertura **~91%**
  (`app/utils/*`, `validation_service`, `schemas`, `preprocess` = **100%**;
  `pipeline` 99%; `baseline_extractor` 97%; `file_validation` 96%; `llm_service` 90%;
  `routes_documents` 88%; `ocr_service` 54% — resto são caminhos de Tesseract/Poppler reais).
- **Suíte hermética (P-01):** verificado — `pytest` dá o **mesmo resultado com e
  sem `.env`** na máquina (conftest fixa todo o ambiente e desliga leitura de dotenv).
- **5 skipped:**
  - `tests/integration/test_llm_real.py` (1) — só roda com `RUN_LLM_REAL=1` + `LLM_API_KEY` válida.
  - `tests/integration/test_ocr_real.py` (4) — PNG real, PDF 1 pág, PDF multipág,
    PDF corrompido — rodam quando Tesseract **e** Poppler estão instalados (dentro do container).
- Ambiente: Windows 11, **Python 3.14.7**, venv em `.venv/` (gitignored).
  `pip install -r requirements-dev.txt` funciona em 3.14.
- Aviso benigno: `starlette` 1.6 → `DeprecationWarning` sobre `TestClient` (não afeta).

---

## 9. Docker

- **Arquivos prontos e validados sinteticamente** (YAML parseia; `Dockerfile`
  padrão `python:3.14-slim` + `apt` `tesseract-ocr tesseract-ocr-por poppler-utils`).
- **NÃO executado** — não há Docker/Podman neste ambiente.
- `docker compose up --build` → serviços `app` (8000) + `mongo` (27017, agora
  exposto no host).
- Perfil `eval` (não sobe no `up` normal): `docker compose --profile eval run --rm eval …`
  com bind-mount de `evaluation/` e `samples/` — para rodar `scripts.evaluate`
  e `scripts.corrections_report` com Tesseract no container.
- Imagem NÃO contém `tests/` nem `requirements-dev` (é enxuta). Testes rodam no host.

---

## 10. OpenAPI / Postman

- **OpenAPI:** `docs/openapi.json` sincronizado com o código (teste
  `test_openapi_file_is_in_sync` compara o schema inteiro). Regenerar:
  `python -m scripts.export_openapi`. Documenta todos os erros + envelope;
  `/health` documenta 200 e 503.
- **Postman:** `postman/TCC-OCR-LLM.postman_collection.json` (v2.1), 6 requests
  (Health, Upload, Consultar, Correção PUT, Confirmação PUT, Reprocessar),
  variáveis `base_url` + `document_id` (auto no upload via test script).
  `test_postman_collection.py` valida que todo request bate com uma rota/método reais.
- **NÃO executado com a API no ar** (Newman/Postman) — validação só estrutural.

---

## 11. Problemas encontrados na auditoria — todos corrigidos (PR #2)

| ID | Problema | Correção | Sev. orig. |
|---|---|---|---|
| P-01 | Suíte lia o `.env` do dev; 2 testes quebravam | conftest hermético | ALTO |
| P-02 | Faltavam métricas "taxa de sucesso" e "correções humanas" | `evaluate.py` + `corrections_report.py` | ALTO |
| P-03 | Experimento não rodava pelo caminho documentado | perfil `eval` + bind-mount | ALTO |
| P-04 | `.env` local com modelo inexistente | `.env.example` + aviso no README; **usuário já corrigiu p/ `gpt-4o-mini`** | ALTO (config) |
| P-05 | Mongo caindo no meio → 500 cru | 503 com envelope + testes | MÉDIO |
| P-06 | `evaluate.py` divergia da metodologia do Artigo | metodologia documentada + `corrections_report` | MÉDIO |
| P-07 | Baseline "strawman" | heurísticas honestas + testes | MÉDIO |
| P-08 | Reprocesso que falha mostrava dados antigos | `_reset_results` + teste | MÉDIO |
| P-09 | `PUT` não normalizava data/CNPJ | `normalize_extracted` no PUT + testes | MÉDIO |
| P-10 | OpenAPI não documentava erros | `ERROR_RESPONSES` nas rotas + testes | MÉDIO |
| P-11 | PDF sem teste | testes `ocr_real` de PDF (1/N/corrompido) + `source_pages` | MÉDIO |
| P-12..P-27 | Binarização opt-in, backoff/429, `.gitignore .env.*`, excerpt 600, código morto, status padronizado, README/`.env.example`, doc de `float`/mono-usuário, PDF truncado→422, asserções semânticas, teste com JSON real do LLM | todos aplicados | BAIXO/INFO |

Detalhe por item: `PLANO_IMPLEMENTACAO.md` → "Apêndice — Ajustes pós-auditoria".

## 12. Problemas ainda pendentes

**Nenhum problema de código/metodologia/documentação em aberto.**

Pendências operacionais:

1. **Rotacionar a API key da OpenAI** (`sk-proj-…`) — ela transitou pelo
   working-tree de um arquivo rastreado (nunca entrou em commit — verificado com
   `git log -S` em todo o histórico). Prevenção.
2. Commitar a alteração local do `docker-compose.yml` (porta 27017 do Mongo).
3. `git rm "Especificação.md"` (arquivo vazio duplicado).
4. Branches locais obsoletos (`fix/auditoria-poc`, `chore/session-continuity-docs`)
   podem ser apagados após `git checkout main`.

---

## 13. Próximos passos exatos (validação real)

Numa máquina com Docker:

```bash
git checkout main && git pull
cp .env.example .env            # LLM_PROVIDER=fake p/ 1ª execução

docker compose up --build
# valida: GET /health -> {"mongo":"ok"} ; upload da nota sintética ;
#         GET ; PUT (correção + validated) ; POST /reprocess
# rodar os 6 requests do Postman contra localhost:8000
```

OCR real + LLM real:

```bash
# dentro do container (ou host com Tesseract+Poppler+MongoDB):
#   instalar requirements-dev e:  pytest -m ocr_real
# LLM real:  no .env -> LLM_PROVIDER=openai, LLM_API_KEY=<chave>, LLM_MODEL=gpt-4o-mini
#   RUN_LLM_REAL=1 pytest -m llm_real
```

Experimento A × B:

```bash
cp evaluation/reference_values.example.csv evaluation/reference_values.csv
# preencher com as notas do experimento (colocar os arquivos em samples/)
docker compose --profile eval run --rm eval \
  -m scripts.evaluate --reference evaluation/reference_values.csv --dir samples
# rodar também com OCR_BINARIZE=true e comparar

# depois de submeter as notas pela API e conferir via PUT:
docker compose --profile eval run --rm eval -m scripts.corrections_report
```

Registrar os resultados (logs/screenshots) para a defesa. **Não inserir
resultados fictícios no software.**

---

## 14. O que uma nova sessão PRECISA saber

- **Todo o trabalho está em `origin/main` (`bf9bff3`).** Começar por
  `git checkout main && git pull`. Ignorar os branches locais antigos.
- **Não há `gh` CLI.** Para PR: `git push` + criar via API do GitHub com o token
  do Git Credential Manager (`git credential fill`), ou orientar o usuário a abrir
  pelo link do `git push`.
- **A suíte é hermética** — não depende de `.env`. Rodar `pytest` direto.
  Se 2+ testes de LLM falharem por contagem de tentativas, o conftest foi quebrado.
- **`FakeLLMClient` + `mongomock`** cobrem tudo; `run_ocr` é stubado nos testes
  de fluxo. OCR/LLM/Mongo **reais nunca foram executados** neste ambiente.
- **Regras do projeto valem sempre:** `CLAUDE.md` (não overengineer, sem
  microserviços/filas/frontend, segredos só em env, não versionar NF real, não
  inventar resultados, não afirmar que testou sem ter testado).
- Ordem de prioridade para requisitos: `ESPECIFICACAO.md` > `CLAUDE.md` >
  Artigo > Estratégia > `PLANO_IMPLEMENTACAO.md` > código.
- Python 3.14 no host; container também 3.14-slim.
- `evaluate.py` compara A×B **offline sobre o mesmo texto OCR** (decisão
  deliberada — LLM é a única variável); as correções humanas reais vêm do
  `corrections_report.py` (lê o Mongo). Isso está documentado e é defensável.
