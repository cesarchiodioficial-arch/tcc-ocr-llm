# Avaliação experimental (Experimento A × Experimento B)

Apoia a metodologia experimental do TCC
(ESPECIFICACAO.md §15 / Artigo §3.11–3.12).

> O software **não inventa** resultados. Os valores de referência de cada nota
> são definidos por você, pesquisador, antes do experimento.

## Como as duas partes se encaixam (metodologia)

O Artigo §3.12 descreve dois aspectos:

1. **Comparar OCR isolado × OCR + LLM.**
   Feito por `scripts/evaluate.py`, **offline**, usando o **mesmo texto OCR**
   para as duas abordagens — assim o LLM é a única variável, o que torna a
   comparação justa. Métricas: campos corretos, campos ausentes/incorretos,
   taxa de acerto, taxa de documentos processados com sucesso, correções
   necessárias (nº de campos divergentes da referência) e tempo.

2. **Registrar as correções humanas do fluxo real.**
   Você submete as notas pela API (`POST /api/v1/documents`), confere o
   resultado (`GET`) e corrige/confirma (`PUT /api/v1/documents/{id}`). Cada
   correção fica gravada em `validation.corrections` no MongoDB.
   `scripts/corrections_report.py` agrega esses dados reais (total de
   correções, por campo, documentos validados com/sem correção, distribuição
   por status).

## Passo a passo

1. Selecione o conjunto de notas fiscais (sintéticas ou exemplos autorizados e
   não sensíveis) e coloque os arquivos em `samples/`.

2. Copie o modelo e preencha os valores esperados de cada campo:

   ```bash
   cp evaluation/reference_values.example.csv evaluation/reference_values.csv
   ```

   Colunas: `file_name,issuer_name,cnpj,issue_date,invoice_number,total_value`.
   Deixe a célula **vazia** quando a nota realmente não contém o campo — campos
   sem referência não entram no cálculo da taxa de acerto.

3. Suba o ambiente (necessário para o `corrections_report` e para o Mongo):

   ```bash
   docker compose up --build     # em outro terminal, ou -d
   ```

4. **Experimento A × B** (Tesseract roda no container `eval`):

   ```bash
   docker compose --profile eval run --rm eval \
     -m scripts.evaluate --reference evaluation/reference_values.csv --dir samples
   ```

   Para o Experimento B com LLM real, defina `LLM_PROVIDER=openai` e
   `LLM_API_KEY` no `.env` antes. Sem chave, apenas o Experimento A
   (OCR isolado) produz números úteis.

   Rode também com `OCR_BINARIZE=true` no `.env` para comparar o efeito da
   binarização.

5. **Fluxo real + correções humanas**: submeta cada nota pela API/Postman,
   confira e corrija via `PUT`. Depois:

   ```bash
   docker compose --profile eval run --rm eval -m scripts.corrections_report
   ```

6. Resultados:
   - `evaluation/results/results_<timestamp>.csv` / `.md` — Experimento A × B;
   - saída do `corrections_report` — correções humanas reais.

`evaluation/reference_values.csv` e `evaluation/results/` estão no `.gitignore`
(podem conter dados reais).

## Fórmula da taxa de acerto

`taxa_de_acerto = (campos_corretos / campos_avaliados) * 100`
