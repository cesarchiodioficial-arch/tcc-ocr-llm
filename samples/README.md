# samples/

Arquivos de exemplo para testar a API.

- `nota-sintetica-001.png` — nota fiscal **sintética** gerada por
  `python -m scripts.make_sample`. Não contém dados reais.

## Regras (CLAUDE.md §9 / ESPECIFICACAO.md §14)

- **Não** versionar notas fiscais reais aqui.
- Apenas arquivos sintéticos ou exemplos autorizados e não sensíveis.
- O `.gitignore` ignora tudo em `samples/` por padrão, exceto este README e
  `nota-sintetica-001.png`.
