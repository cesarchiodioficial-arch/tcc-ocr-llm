# CLAUDE.md — REGRAS PERMANENTES DO PROJETO

## 1. Contexto

Este repositório contém a POC do TCC:

**Sistema inteligente de extração automática de dados em notas fiscais utilizando OCR e Large Language Models**

O projeto é acadêmico e deve permanecer pequeno, reproduzível e tecnicamente justificável.

## 2. Documentos de referência

Antes de tomar decisões relevantes, consultar:

1. `ESPECIFICACAO.md` — requisitos operacionais.
2. `PLANO_IMPLEMENTACAO.md` — plano técnico aprovado após a fase de análise.
3. `Artigo - CesarChiodi - UNIARA 2026.pdf` — contexto acadêmico.
4. `Estratégia e planejamento.pdf` — visão/desenho inicial.

Quando houver divergência, registrar a divergência e preservar o escopo do TCC.

## 3. Regra de ouro

**Não overengineer.**

Esta é uma POC de TCC, não um produto de produção.

Preferir:
- monólito modular;
- código simples;
- poucas dependências;
- Docker Compose;
- API REST;
- testes diretos;
- configuração por ambiente.

Evitar sem justificativa:
- microserviços;
- filas;
- Kubernetes;
- Kafka;
- RabbitMQ;
- cloud obrigatória;
- infraestrutura distribuída;
- autenticação complexa;
- observabilidade empresarial;
- bancos adicionais.

## 4. Arquitetura

A arquitetura deve manter a separação lógica:

API → processamento → OCR → LLM → validação → revisão humana → persistência

Os módulos podem estar na mesma aplicação.

Não criar serviços separados apenas para representar conceitualmente módulos.

## 5. Stack-alvo

- Python;
- API REST;
- Tesseract OCR;
- MongoDB;
- Docker/Docker Compose;
- LLM via API;
- Postman.

A escolha do framework Python deve seguir a especificação e o plano. Não trocar tecnologias já definidas sem motivo concreto.

## 6. Campos essenciais

A POC deve trabalhar prioritariamente com:

- `issuer_name`;
- `cnpj`;
- `issue_date`;
- `invoice_number`;
- `total_value`.

Não ampliar para itens, impostos ou outros dados fiscais sem necessidade para o TCC.

## 7. LLM

O LLM nunca deve ser tratado como fonte de verdade.

As instruções devem exigir:
- somente evidência do OCR;
- nenhum dado inventado;
- `null` quando não houver evidência;
- JSON estruturado;
- schema validado pela aplicação.

O acesso ao LLM deve acontecer por uma camada isolada para facilitar testes e troca de provedor.

## 8. Segredos

Nunca colocar em código:
- API keys;
- tokens;
- senhas;
- credenciais.

Utilizar variáveis de ambiente.

Manter `.env.example`.

Antes de commit, revisar se algum segredo foi incluído.

## 9. Documentos fiscais

Não versionar notas fiscais reais.

Não registrar conteúdo fiscal completo em logs desnecessariamente.

Arquivos de teste devem ser sintéticos ou exemplos autorizados e não sensíveis.

## 10. Tratamento de erros

Falhas devem ser:
- explícitas;
- previsíveis;
- registradas em log;
- refletidas no status do documento.

Nunca retornar sucesso quando a persistência não ocorreu.

## 11. Testes

Toda alteração relevante deve ser acompanhada de testes.

Prioridade:
1. regras de domínio;
2. validações;
3. processamento;
4. integração;
5. API.

Testes do LLM devem ser mockados quando o objetivo for testar a lógica interna.

## 12. Docker

O ambiente precisa ser reproduzível via Docker Compose.

O comando principal deve ser documentado:

```bash
docker compose up --build
```

## 13. Git

Antes de commit:

```bash
git status
git diff
```

Nunca:
- force push;
- reset destrutivo;
- apagar histórico;
- trocar remote sem autorização.

Commitar somente após os testes relevantes passarem.

## 14. Modo agentic

Para tarefas complexas:

1. investigar;
2. planejar;
3. implementar em pequenas fases;
4. testar;
5. corrigir;
6. revisar;
7. documentar;
8. validar novamente;
9. só então commit/push.

Não implementar impulsivamente antes de compreender o contexto.

## 15. Autocorreção

Quando um teste, build, Docker ou integração falhar:

1. reproduza;
2. encontre a causa;
3. corrija a causa;
4. execute novamente;
5. confirme que não houve regressão.

Não esconda falhas alterando testes apenas para fazê-los passar.

## 16. Documentação

Toda decisão importante deve ser compreensível por um aluno e por uma banca de TCC.

Documentação deve explicar:
- o que existe;
- por que existe;
- como executar;
- como testar;
- limitações da POC.

## 17. Comunicação

Não afirmar que algo foi testado se não foi executado.

Não afirmar que algo está no GitHub se o push não foi confirmado.

Quando houver limitação externa, declarar claramente.

## 18. Critério de simplicidade

Em qualquer decisão não especificada:

> Escolha a menor solução que atenda ao TCC, seja testável, executável localmente e fácil de explicar academicamente.

## 19. Decisões técnicas aprovadas

As decisões abaixo estão aprovadas e não devem ser novamente questionadas durante a implementação:

- processamento síncrono;
- FastAPI + Uvicorn;
- limite máximo de arquivo de 10 MB;
- PDF processado com pdf2image + poppler-utils;
- Experimento A utilizando baseline OCR-only com heurísticas/regex;
- provedor inicial OpenAI;
- modelo LLM configurável por `LLM_MODEL`;
- API key exclusivamente por variável de ambiente.

O agente não deve voltar a propor Flask, processamento assíncrono, PyMuPDF ou outros modelos de arquitetura salvo quando surgir um erro técnico concreto que impeça a execução da solução aprovada.