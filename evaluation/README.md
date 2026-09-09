# Avaliação experimental (Experimento A vs Experimento B)

Este diretório apoia a metodologia experimental do TCC
(ESPECIFICACAO.md §15 / Artigo §3.11–3.12).

> O software **não inventa** resultados. Os valores de referência de cada nota
> são definidos por você, pesquisador, antes do experimento.

## Passo a passo

1. Selecione o conjunto de notas fiscais do experimento (podem ser sintéticas ou
   exemplos autorizados e não sensíveis) e coloque os arquivos em `samples/`
   (ou em outra pasta que você indicar com `--dir`).

2. Copie o modelo e preencha os valores esperados de cada campo:

   ```bash
   cp evaluation/reference_values.example.csv evaluation/reference_values.csv
   ```

   Colunas: `file_name,issuer_name,cnpj,issue_date,invoice_number,total_value`.
   Deixe uma célula **vazia** quando a nota realmente não contém aquele campo —
   campos sem referência não entram no cálculo da taxa de acerto.

3. Rode a avaliação (precisa do Tesseract — use o container):

   ```bash
   docker compose run --rm app python -m scripts.evaluate \
     --reference evaluation/reference_values.csv --dir samples
   ```

   Para o Experimento B (OCR + LLM) é necessário `LLM_API_KEY` válida no `.env`.
   Sem chave, apenas o Experimento A (OCR isolado) produz números úteis.

4. Os resultados são gravados em `evaluation/results/`:
   - `results_<timestamp>.csv` — uma linha por documento e abordagem;
   - `results_<timestamp>.md` — tabela consolidada com a taxa de acerto
     (`campos_corretos / campos_avaliados * 100`) e o tempo médio.

## Métricas coletadas

- campos identificados corretamente;
- campos ausentes / incorretos;
- taxa de acerto (%);
- tempo de processamento (ms) por documento;
- comparação direta **A (OCR isolado)** vs **B (OCR + LLM)**.

As correções feitas na validação humana (via `PUT /api/v1/documents/{id}`) ficam
registradas em `validation.corrections` de cada documento no MongoDB e podem ser
exportadas para complementar a análise.

`evaluation/reference_values.csv` e `evaluation/results/` estão no `.gitignore`
(podem conter dados reais).
