# ESPECIFICAÇÃO DA POC
## Sistema inteligente de extração automática de dados em notas fiscais utilizando OCR e Large Language Models

> Este documento funciona como especificação operacional da POC.  
> Quando houver conflito, o requisito mais específico deste arquivo prevalece sobre inferências do agente, sem contrariar o escopo acadêmico do TCC.

## 1. Objetivo

Construir uma prova de conceito local capaz de receber notas fiscais em imagem/PDF, extrair texto utilizando OCR, interpretar o texto utilizando um Large Language Model, validar os dados e permitir revisão humana antes da persistência definitiva.

Fluxo principal:

**Documento → OCR → LLM → Validação sistêmica → Validação humana → MongoDB**

A POC deve ser simples, executável localmente e adequada ao desenvolvimento de um TCC de Sistemas de Informação.

## 2. Escopo

### Obrigatório

Extrair os seguintes campos:

- razão social / empresa emissora;
- CNPJ;
- data de emissão;
- número da nota fiscal;
- valor total.

A solução também deve preservar o texto OCR e metadados suficientes para rastreabilidade.

### Fora do escopo inicial

Não é necessário implementar:

- itens de produtos;
- impostos detalhados;
- ERP;
- emissão de NF-e;
- integração com SEFAZ;
- autenticação empresarial;
- autorização complexa;
- processamento distribuído;
- filas;
- microserviços;
- Kubernetes;
- cloud obrigatória;
- frontend completo.

Esses itens podem ser considerados evolução futura, não requisitos da POC.

## 3. Arquitetura

Uma única aplicação Python organizada em módulos internos.

Componentes:

1. API REST;
2. recebimento/gestão de documentos;
3. OCR Tesseract;
4. interpretação LLM;
5. validação sistêmica;
6. validação humana;
7. persistência MongoDB.

O processamento deve permanecer dentro da própria aplicação, sem necessidade de arquitetura distribuída.

## 4. Tecnologias

Stack-base:

- Python;
- API REST Python;
- Tesseract OCR;
- MongoDB;
- Docker;
- Docker Compose;
- API de LLM configurável por variável de ambiente;
- Postman para testes manuais da API.

O framework Python pode ser escolhido pelo agente somente se não houver definição mais específica no repositório. A preferência é por uma solução simples, amplamente usada e adequada a uma POC.

As decisões técnicas já definidas para a POC (framework, limite de upload, conversão de PDF, provedor de LLM etc.) estão consolidadas na seção **22. Decisões técnicas aprovadas**.

## 5. Entrada de documentos

Formatos esperados:

- PDF;
- PNG;
- JPG/JPEG.

O sistema deve rejeitar arquivos vazios, corrompidos ou não suportados.

A implementação deve definir limite razoável de tamanho por arquivo e documentá-lo.

## 6. OCR

Usar Tesseract OCR.

O ambiente Docker deve incluir os pacotes necessários para sua execução.

Dar preferência ao idioma português quando disponível.

Quando o arquivo for PDF, o sistema deve utilizar uma estratégia simples e confiável para transformar páginas em imagens para OCR.

Pré-processamento pode incluir apenas técnicas simples e justificadas, como:
- redimensionamento;
- contraste;
- remoção de ruído;
- binarização.

Não implementar visão computacional complexa.

O texto OCR deve ser preservado para rastreabilidade.

## 7. LLM

A camada de LLM deve ser isolada por um serviço/adaptador interno.

O provedor e modelo devem ser configuráveis sem alterar o código, por exemplo por variáveis de ambiente.

A aplicação deve enviar ao modelo:
- instruções do schema;
- texto OCR.

O modelo deve ser instruído explicitamente:

1. utilizar somente informações evidenciadas no texto OCR;
2. não inventar dados;
3. retornar `null` quando não houver informação suficiente;
4. retornar JSON compatível com o schema;
5. evitar explicações fora do JSON esperado.

### Estrutura lógica esperada

```json
{
  "issuer_name": "Empresa Exemplo LTDA",
  "cnpj": "12345678000199",
  "issue_date": "2026-01-31",
  "invoice_number": "12345",
  "total_value": 1500.50
}
```

Os nomes dos campos podem ser ajustados se já houver definição no repositório, mas a semântica deve permanecer.

## 8. Validação sistêmica

Antes da persistência definitiva:

### `issuer_name`
Deve ser string não vazia quando identificado.

### `cnpj`
Validar formato e dígitos verificadores.

### `issue_date`
Validar formato de data.

Preferência para formato interno ISO `YYYY-MM-DD`.

### `invoice_number`
Validar como identificador textual/número não vazio quando identificado.

### `total_value`
Deve ser valor monetário numérico válido e não pode aceitar parsing ambíguo.

### Campos ausentes

Campo que não puder ser identificado com segurança deve permanecer `null`/ausente conforme o schema.

O sistema não deve preencher automaticamente informações presumidas.

## 9. Estados do processamento

Usar estados simples e documentados, por exemplo:

- `RECEIVED`
- `PROCESSING`
- `OCR_COMPLETED`
- `EXTRACTED`
- `VALIDATION_PENDING`
- `VALIDATED`
- `FAILED`
- `REPROCESSING`

Os nomes podem ser ajustados à implementação, desde que exista semântica equivalente e documentação.

## 10. Persistência

Coleção MongoDB para documentos processados.

Estrutura mínima:

```json
{
  "_id": "uuid",
  "file_name": "nota-001.pdf",
  "status": "VALIDATION_PENDING",
  "ocr_text": "...",
  "extracted_data": {
    "issuer_name": "...",
    "cnpj": "...",
    "issue_date": "...",
    "invoice_number": "...",
    "total_value": 0
  },
  "validation": {
    "validated": false,
    "corrections": []
  },
  "processing": {
    "ocr_duration_ms": 0,
    "llm_duration_ms": 0,
    "total_duration_ms": 0
  },
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

A estrutura pode ser adaptada sem perder os dados necessários para avaliação.

## 11. API

### POST `/api/v1/documents`

Recebe documento via `multipart/form-data`.

Responsabilidade:
- validar arquivo;
- criar identificação;
- iniciar processamento;
- retornar identificação e status.

### GET `/api/v1/documents/{id}`

Retorna:
- status;
- texto OCR;
- dados extraídos;
- validação;
- metadados disponíveis.

### PUT `/api/v1/documents/{id}`

Permite revisão/correção humana dos dados extraídos.

Deve registrar:
- valor anterior, quando aplicável;
- novo valor;
- data/hora;
- indicação de que houve correção;
- estado de validação.

### POST `/api/v1/documents/{id}/reprocess`

Solicita novo processamento do documento.

O reprocessamento deve reutilizar o documento original sem exigir novo upload, desde que isso seja possível com a implementação adotada.

### Health

Pode existir:

`GET /health`

ou equivalente, para permitir testes de disponibilidade e Docker.

## 12. Fluxo detalhado

1. Cliente envia documento.
2. API valida o arquivo.
3. Documento recebe ID único.
4. Sistema inicia processamento.
5. OCR é executado.
6. Texto OCR é registrado.
7. Se não houver texto útil, documento pode ser marcado como falha/revisão.
8. Texto é enviado ao LLM.
9. LLM retorna JSON.
10. Sistema valida schema e campos.
11. Se inválido, deve rejeitar o resultado e tentar novamente conforme política limitada.
12. Se continuar inválido, marcar falha/revisão.
13. Dados válidos ficam disponíveis para revisão humana.
14. Usuário confirma ou corrige.
15. Resultado validado é persistido como definitivo.
16. Metadados do processamento permanecem disponíveis para avaliação.

## 13. Tratamento de falhas

### Arquivo
- formato não suportado → HTTP 4xx;
- arquivo vazio → HTTP 4xx;
- arquivo corrompido → erro controlado e status de falha.

### OCR
- ausência de texto → estado de falha/revisão;
- erro do mecanismo → log + estado de falha.

### LLM
- timeout → tentativa limitada;
- erro de comunicação → retry limitado;
- resposta inválida → rejeitar;
- JSON incompatível → não persistir como resultado válido.

### MongoDB
- erro de conexão → registrar log;
- não considerar operação concluída quando a persistência não ocorreu.

## 14. Segurança e privacidade

- usar `.env` para chaves;
- manter `.env.example`;
- não versionar secrets;
- evitar logs com dados fiscais completos;
- não versionar notas fiscais reais;
- não persistir dados desnecessários.

## 15. Avaliação experimental

A implementação deve permitir medir:

- campos identificados corretamente;
- campos ausentes/incorretos;
- correções humanas;
- documentos processados com sucesso;
- tempo de processamento.

Também deve permitir comparar:

### Experimento A
OCR isolado.

### Experimento B
OCR + LLM.

Para cada nota, deverão existir valores de referência definidos previamente pelo pesquisador.

Taxa de acerto:

`taxa_de_acerto = (campos_corretos / campos_avaliados) * 100`

Os resultados do experimento não devem ser inventados pelo software.

## 16. Testes mínimos

Implementar testes para:

- health;
- upload válido;
- upload inválido;
- validação do CNPJ;
- validação da data;
- validação do valor;
- resposta válida do LLM;
- resposta inválida do LLM;
- persistência;
- consulta;
- correção humana;
- reprocessamento;
- tratamento de falhas.

O LLM real pode ser coberto por teste de integração separado; testes unitários devem utilizar mock quando adequado.

## 17. Docker

O projeto deve funcionar com:

```bash
docker compose up --build
```

Deve existir:
- serviço da aplicação;
- serviço MongoDB;
- volume do MongoDB;
- variáveis de ambiente documentadas.

O Dockerfile deve incluir as dependências do Tesseract.

## 18. Postman

Criar uma coleção importável contendo:

- health;
- upload;
- consulta;
- update/validação humana;
- reprocessamento.

Variáveis úteis podem incluir:

- `base_url`;
- `document_id`.

## 19. Git

Antes de commit:

- revisar `git diff`;
- verificar `git status`;
- verificar ausência de secrets;
- verificar ausência de documentos reais;
- verificar que testes passam.

Commit esperado após implementação funcional.

Nunca fazer force push ou operações destrutivas.

## 20. Critérios de aceite

A POC está funcional quando:

- Docker Compose sobe;
- API responde;
- MongoDB conecta;
- Tesseract executa;
- documento é recebido;
- OCR produz texto;
- LLM produz estrutura;
- schema é validado;
- usuário consegue revisar/corrigir;
- resultado é persistido;
- reprocessamento funciona;
- testes passam;
- Postman funciona;
- README permite reproduzir o ambiente;
- nenhuma credencial está versionada.

## 21. Princípio de implementação

Sempre escolher a solução:

**mais simples + suficiente para a POC + fácil de explicar academicamente + reproduzível localmente.**

Quando duas opções forem tecnicamente válidas, preferir a que:
- tenha menos código;
- tenha menos dependências;
- seja mais fácil de testar;
- seja mais fácil de justificar no TCC.

## 22. Decisões técnicas aprovadas

As seguintes decisões foram definidas para a implementação da POC:

- O processamento do `POST /api/v1/documents` será síncrono.
- O framework da API será FastAPI, servido por Uvicorn.
- O acesso ao MongoDB será feito com o driver `pymongo` (síncrono).
- O limite máximo de upload será de 10 MB (configurável por variável de ambiente).
- Arquivos PDF serão convertidos para imagem utilizando `pdf2image` e `poppler-utils`.
- O Experimento A será realizado por meio de um baseline OCR-only baseado em heurísticas/expressões regulares sobre o texto produzido pelo Tesseract.
- O provedor inicial do LLM será OpenAI, utilizando uma camada `LLMClient` desacoplada do restante da aplicação.
- O modelo do LLM será definido por variável de ambiente e registrado nos metadados de cada processamento.
- A API key será fornecida exclusivamente por variável de ambiente e nunca será versionada.