# GUIA DE USO — CLAUDE CODE PARA A POC DO TCC

## 1. Preparação

Abra o terminal e entre no repositório:

```powershell
cd "F:\Doc Importante\TCC\TCC"
```

Confira se os arquivos estão lá:

```powershell
Get-ChildItem
```

Recomenda-se confirmar que o Git está configurado:

```powershell
git status
git remote -v
```

## 2. Coloque os arquivos de governança na raiz

Na raiz do repositório devem existir:

- `CLAUDE.md`
- `ESPECIFICACAO.md`
- `PLANO_IMPLEMENTACAO.md` depois da fase 1
- `README.md` durante/depois da implementação

O `CLAUDE.md` deve ser mantido como regra permanente.

## 3. Fase 1 — somente análise

Abra o Claude Code nessa pasta e envie o conteúdo do arquivo:

`PROMPT-01-ANALISE.md`

O agente deve:

- ler o TCC;
- ler a estratégia;
- ler a especificação;
- ler o CLAUDE;
- inspecionar o repositório;
- criar `PLANO_IMPLEMENTACAO.md`;
- não implementar.

### Regra

Não avance para a execução até o plano estar consistente.

## 4. Conferência humana do plano

Abra:

`PLANO_IMPLEMENTACAO.md`

Confira principalmente:

- stack;
- fluxo OCR → LLM;
- campos;
- endpoints;
- MongoDB;
- Docker;
- estratégia de PDF;
- estratégia do LLM;
- testes;
- Postman;
- Git.

O plano deve continuar simples e compatível com o artigo.

## 5. Fase 2 — implementação

Quando o plano estiver aprovado, envie:

`PROMPT-02-EXECUCAO.md`

O agente deve implementar em ciclos pequenos e testar cada etapa.

## 6. O que esperar ao final

O repositório deve conter, no mínimo:

```text
.
├── CLAUDE.md
├── ESPECIFICACAO.md
├── PLANO_IMPLEMENTACAO.md
├── README.md
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── postman/
│   └── TCC-OCR-LLM.postman_collection.json
├── tests/
└── código da aplicação
```

Os nomes exatos de pastas podem variar conforme o plano aprovado.

## 7. Execução local esperada

Depois da implementação, o fluxo principal deve ser documentado e executável com algo equivalente a:

```powershell
docker compose up --build
```

Depois usar Postman para:

1. health;
2. upload;
3. consulta;
4. validação/correção;
5. reprocessamento.

## 8. Configuração do LLM

A API key deve ficar em `.env`, nunca no Git.

O projeto deve fornecer `.env.example` contendo apenas nomes de variáveis e valores fictícios.

## 9. Validação experimental do TCC

A implementação deve preparar a coleta das métricas, mas o aluno deve realizar o experimento com um conjunto de notas fiscais selecionadas.

Para cada documento, manter os valores de referência necessários para comparar:

- OCR isolado;
- OCR + LLM.

Registrar:

- campos corretos;
- campos incorretos/ausentes;
- correções humanas;
- sucesso/falha;
- tempo.

Não inserir resultados fictícios no software.

## 10. Critério final

Antes de considerar concluído:

```text
[ ] TCC analisado
[ ] estratégia analisada
[ ] especificação analisada
[ ] plano criado
[ ] código implementado
[ ] testes passando
[ ] Docker funcionando
[ ] MongoDB funcionando
[ ] OCR funcionando
[ ] LLM funcionando com configuração válida
[ ] validação humana funcionando
[ ] Postman importável
[ ] README completo
[ ] sem secrets no Git
[ ] commit criado
[ ] push confirmado ou impedimento documentado
```
