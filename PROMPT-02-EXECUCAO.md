# PROMPT 02 — EXECUÇÃO DA POC

Você está trabalhando em:

`F:\Doc Importante\TCC\TCC`

O TCC é:

**Sistema inteligente de extração automática de dados em notas fiscais utilizando OCR e Large Language Models**

A etapa anterior de análise já foi concluída e existe um:

`PLANO_IMPLEMENTACAO.md`

## REGRA PRINCIPAL

Agora você pode implementar.

Porém, **não altere a arquitetura definida no plano sem necessidade**.

Antes de começar:

1. Leia novamente:
   - `CLAUDE.md`
   - `ESPECIFICACAO.md`
   - `PLANO_IMPLEMENTACAO.md`
   - `Artigo - CesarChiodi - UNIARA 2026.pdf`
   - `Estratégia e planejamento.pdf`
2. Verifique o estado atual do Git.
3. Verifique se existem mudanças feitas depois do plano.
4. Compare o estado atual com o plano.
5. Se houver uma decisão crítica ainda não resolvida, pare e informe.
6. Para dúvidas pequenas, prefira a solução mais simples que preserve o escopo da POC e registre a decisão na documentação.

## OBJETIVO

Entregar uma POC executável localmente com Docker Compose que demonstre o fluxo:

**upload da nota → OCR → interpretação LLM → validação sistêmica → revisão/validação humana → MongoDB**

A solução deve trabalhar com:

- imagens;
- PDF quando suportado pelo fluxo definido na especificação;
- Tesseract OCR;
- LLM via API;
- MongoDB;
- API REST Python;
- Docker Compose.

## ESCOPO ACADÊMICO OBRIGATÓRIO

Os campos essenciais são:

- `issuer_name` — razão social/empresa emissora;
- `cnpj`;
- `issue_date`;
- `invoice_number`;
- `total_value`.

O resultado do LLM deve ser estruturado e validado.

Nunca permita que o modelo seja tratado como fonte de verdade. O texto OCR é a evidência disponível e o sistema deve registrar o resultado do processamento.

## RESTRIÇÕES

Não transforme a POC em um produto empresarial.

Não adicionar sem necessidade:
- microserviços;
- Kubernetes;
- filas;
- Kafka;
- RabbitMQ;
- Azure;
- autenticação complexa;
- frontend obrigatório;
- infraestrutura cloud;
- banco adicional;
- arquitetura distribuída.

A simplicidade é requisito do projeto.

## IMPLEMENTAÇÃO POR FASES

Execute o plano em pequenos ciclos.

Depois de cada fase:

1. implemente;
2. rode os testes relacionados;
3. inspecione o resultado;
4. corrija problemas;
5. só então avance.

Não acumule dezenas de mudanças sem validar.

## QUALIDADE DO CÓDIGO

A implementação deve ter:

- organização modular;
- tipagem quando útil;
- tratamento explícito de erros;
- configuração por variáveis de ambiente;
- logs úteis;
- validação dos dados;
- funções pequenas e testáveis;
- dependências justificadas;
- comentários apenas onde agregarem entendimento.

Não use valores secretos hard-coded.

## API

Implemente e documente os endpoints previstos no TCC:

`POST /api/v1/documents`

`GET /api/v1/documents/{id}`

`PUT /api/v1/documents/{id}`

`POST /api/v1/documents/{id}/reprocess`

Pode existir endpoint de health/readiness se for tecnicamente necessário.

Para cada endpoint, garanta:
- validação;
- códigos HTTP coerentes;
- mensagens de erro úteis;
- contrato documentado.

## PROCESSAMENTO

### Upload

Aceitar documento de acordo com os formatos definidos na especificação.

Validar:
- extensão;
- MIME type quando disponível;
- arquivo vazio;
- tamanho máximo definido.

### OCR

Usar Tesseract.

Garantir que o ambiente Docker tenha os componentes necessários.

Quando necessário, realizar conversão de PDF para imagem e/ou pré-processamento simples.

Não implemente pipeline sofisticado de visão computacional sem justificativa.

Persistir o texto OCR para rastreabilidade.

### LLM

Criar uma camada/adaptador que permita trocar o provedor por configuração.

O prompt do sistema/modelo deve instruir:
- responder somente com dados observáveis no OCR;
- não inventar valores;
- retornar null/ausente quando não houver evidência;
- seguir exatamente o schema.

Validar a resposta antes de aceitar o resultado.

### Validação sistêmica

Validar:
- schema;
- tipos;
- campos obrigatórios;
- CNPJ;
- data;
- valor;
- coerência mínima dos dados.

Uma resposta do LLM que não cumprir o contrato NÃO deve ser persistida como resultado válido.

### Validação humana

A POC deve permitir:
- consultar os dados extraídos;
- corrigir os campos;
- confirmar a validação;
- registrar as correções;
- manter rastreabilidade.

### Reprocessamento

Permitir processar novamente o documento quando necessário.

Evitar duplicações acidentais e manter o histórico mínimo necessário para o experimento.

## MONGODB

Persistir, no mínimo, informações equivalentes às previstas no TCC:

- identificador;
- nome do arquivo;
- status;
- OCR bruto;
- dados estruturados;
- validação;
- correções;
- timestamps;
- metadados de processamento.

Não armazene dados além do necessário para a POC.

## DOCKER

O comando principal para executar o sistema deve ser documentado.

Preferência:

```bash
docker compose up --build
```

O projeto deve funcionar a partir de uma máquina limpa que possua Docker Desktop, dentro das limitações normais de uma POC.

Use volume persistente para o MongoDB.

Crie `.env.example`.

Nunca commit `.env` contendo segredos.

## TESTES

Crie e execute testes suficientes para demonstrar:

1. health da aplicação;
2. upload válido;
3. rejeição de arquivo inválido;
4. OCR;
5. parsing/validação da resposta do LLM;
6. validação de CNPJ;
7. validação de data;
8. validação de valor;
9. persistência;
10. consulta;
11. atualização/validação humana;
12. reprocessamento;
13. tratamento de erro.

Para testes externos do LLM, não exponha API key no código.

Sempre que possível, use mock no teste automatizado e um teste manual/integrado separado para o provedor real.

## OPENAPI E POSTMAN

A API deve gerar/possuir documentação OpenAPI coerente.

Crie:

`postman/TCC-OCR-LLM.postman_collection.json`

A coleção deve conter, no mínimo:
- health;
- upload;
- consulta;
- atualização/validação humana;
- reprocessamento.

Se houver variável de ambiente/base URL, documente como configurar.

A coleção deve ser importável no Postman.

Faça uma validação real da coleção contra a API sempre que possível.

## DOCUMENTAÇÃO

Atualize/crie:

- `README.md`
- `.env.example`
- documentação dos endpoints;
- instruções de Docker;
- instruções de execução dos testes;
- instruções para configurar o provedor de LLM;
- instruções de uso do Postman;
- exemplo do fluxo completo.

O README deve explicar o que a POC faz e, principalmente, o que ela não pretende fazer.

## AVALIAÇÃO EXPERIMENTAL

A implementação deve facilitar o experimento descrito no TCC.

Preserve dados suficientes para comparar:
- OCR isolado;
- OCR + LLM.

Quando for adequado, registre:
- tempo de processamento;
- campos encontrados;
- campos ausentes/incorretos;
- necessidade de correção humana;
- status final.

Não invente resultados experimentais.

O código deve preparar a coleta, mas os resultados devem ser obtidos a partir de notas fiscais reais/selecionadas durante o experimento.

## SEGURANÇA

Nunca:
- commitar API keys;
- colocar credenciais no código;
- colocar documentos fiscais reais de teste no Git;
- registrar dados sensíveis desnecessariamente nos logs.

Verifique o `.gitignore`.

## AUTOVERIFICAÇÃO OBRIGATÓRIA

Ao terminar a implementação:

### 1. Testes

Execute toda a suíte.

Se falhar:
- investigue;
- corrija;
- execute novamente.

### 2. Docker

Execute:

```bash
docker compose config
docker compose up --build -d
```

Valide os containers.

Teste a API.

Depois, derrube o ambiente adequadamente quando não for mais necessário.

### 3. Postman

Valide se a coleção JSON está sintaticamente correta e corresponde à API.

### 4. Lint/format

Se ferramentas de lint/format estiverem configuradas, execute-as.

Não introduza ferramentas desnecessárias apenas para cumprir esta etapa.

### 5. Revisão final

Verifique:
- requisitos da especificação;
- plano;
- artigo;
- documentação;
- testes;
- Docker;
- Postman;
- `.gitignore`;
- segredos;
- arquivos temporários.

## GIT E GITHUB

Depois que tudo estiver validado:

1. `git status`
2. revise o diff;
3. confirme que não existem segredos ou arquivos indevidos;
4. faça commit organizado;
5. faça push para o remote atual se a autenticação estiver disponível.

Não:
- force push;
- reescreva histórico;
- apague branches;
- altere remote;
- faça reset destrutivo.

Use uma mensagem de commit clara, por exemplo:

`feat: implement OCR and LLM invoice extraction POC`

Caso o push não seja possível por falta de autenticação/permissão:
- não tente contornar credenciais;
- deixe o commit local feito;
- informe exatamente o que falta para o push.

## CRITÉRIO DE CONCLUSÃO

Considere a tarefa concluída somente quando:

- [ ] arquitetura conforme plano/especificação;
- [ ] API executável;
- [ ] Docker Compose funcional;
- [ ] MongoDB funcional;
- [ ] Tesseract funcional;
- [ ] integração LLM configurável;
- [ ] validação sistêmica;
- [ ] validação humana;
- [ ] persistência;
- [ ] reprocessamento;
- [ ] testes passando;
- [ ] OpenAPI/documentação coerente;
- [ ] Postman collection importável;
- [ ] README completo;
- [ ] `.env.example`;
- [ ] `.gitignore` revisado;
- [ ] sem segredos versionados;
- [ ] commit realizado;
- [ ] push realizado, quando tecnicamente possível.

## RELATÓRIO FINAL

Ao final, apresente:

1. o que foi implementado;
2. estrutura principal do projeto;
3. tecnologias utilizadas;
4. como executar;
5. como configurar o LLM;
6. endpoints;
7. testes executados e resultado;
8. Docker executado e resultado;
9. Postman validado;
10. commit criado;
11. push realizado ou motivo pelo qual não foi possível;
12. limitações conhecidas;
13. próximos passos somente se forem realmente necessários ao TCC.

Não declare que algo foi validado se não foi realmente executado.
