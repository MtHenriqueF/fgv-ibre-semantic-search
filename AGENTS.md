# Contexto do Projeto

Este projeto é uma solução para o Desafio Técnico de Estágio em Ciência de Dados do FGV IBRE.

O objetivo é construir um mini motor de busca semântico aplicado a notícias econômicas fictícias. A solução deve demonstrar capacidade de limpar dados textuais, gerar embeddings, armazenar vetores em um banco vetorial local, recuperar documentos por similaridade semântica e avaliar qualitativa e quantitativamente os resultados.

O projeto deve ser simples de executar, bem documentado e reproduzível.

## Escopo principal

O projeto deve conter:

1. Pipeline de limpeza textual.
2. Geração de dados limpos.
3. Geração de chunks com metadados.
4. Geração de embeddings usando `sentence-transformers`.
5. Armazenamento local em ChromaDB.
6. Busca semântica por distância vetorial.
7. Busca léxica com BM25.
8. Busca híbrida combinando ranking semântico e léxico.
9. Reranking opcional.
10. Métricas de avaliação de ranking.
11. Backend FastAPI.
12. Frontend HTML/CSS/JS servido pelo próprio FastAPI.
13. README com instruções de execução e decisões técnicas.

## Decisões arquiteturais

- O banco vetorial será ChromaDB local.
- O frontend será estático: HTML, CSS e JavaScript.
- O backend será FastAPI.
- O frontend deve consumir o backend via endpoints HTTP/JSON.
- O projeto deve rodar localmente com comandos simples.
- Docker deve ser suportado como opção adicional, mas não deve ser a única forma de execução.
- Não construir SaaS, autenticação, login, billing ou multiusuário.
- O foco é reprodutibilidade, clareza técnica e qualidade da recuperação.
- O pipeline deve ser reproduzível a partir de `data/raw/noticias_brutas.json`.

---

# Estrutura de diretórios

Use a estrutura:

fgv-ibre-semantic-search/
├── data/
│   ├── raw/
│   ├── processed/
│   └── vector_store/
├── outputs/
├── src/
├── backend/
├── frontend/
├── evaluation/
├── tests/
├── docs/
├── AGENTS.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── run_pipeline.py

---

# Responsabilidade de cada pasta

## `data/`

A pasta `data/` contém os dados usados ou gerados pelo pipeline.

### `data/raw/`

Armazena os dados brutos originais do desafio.

Deve conter:

- `noticias_brutas.json`

Regras:

- Não alterar manualmente o conteúdo bruto.
- O pipeline deve sempre começar a partir desse arquivo.
- Essa pasta representa a entrada original do desafio.

Exemplo:

data/raw/noticias_brutas.json

### `data/processed/`

Armazena dados intermediários e finais processados pelo pipeline.

Deve conter arquivos como:

- `noticias_limpas.json`
- `chunks.jsonl`

Responsabilidade:

- Guardar textos limpos.
- Guardar documentos enriquecidos com metadados derivados.
- Guardar chunks usados para embeddings e busca.
- Servir como entrada para a etapa de embeddings e indexação.

Exemplo de notícia limpa:

{
  "article_id": 1,
  "titulo": "...",
  "texto_limpo": "...",
  "data": "2023-08-02",
  "fonte": "Banco Central do Brasil",
  "ano": 2023,
  "mes": 8,
  "tema_economico": "juros"
}

Exemplo de chunk:

{
  "chunk_id": "article_1_chunk_0",
  "article_id": 1,
  "titulo": "...",
  "texto": "...",
  "data": "2023-08-02",
  "fonte": "Banco Central do Brasil",
  "tema_economico": "juros",
  "chunk_index": 0
}

### `data/vector_store/`

Armazena o banco vetorial local.

Deve conter:

- diretório persistente do ChromaDB.

Exemplo:

data/vector_store/chroma_db/

Regras:

- O banco vetorial deve ser gerado pelo pipeline.
- O projeto não deve depender de um banco externo.
- O ChromaDB local deve ser reconstruível a partir de `data/raw/` e `data/processed/`.
- Em geral, o banco vetorial pode ficar fora do Git se for grande ou se for facilmente reconstruído.

---

## `outputs/`

A pasta `outputs/` armazena relatórios, resultados de avaliação e artefatos de inspeção.

Deve conter arquivos como:

- `cleaning_report.csv`
- `evaluation_results.csv`
- `search_examples.json`
- `retrieval_comparison.csv`

Responsabilidade:

- Guardar evidências do funcionamento do pipeline.
- Guardar resultados das métricas de avaliação.
- Guardar exemplos de busca para documentação no README.
- Guardar relatórios que ajudam a avaliar qualidade.

Diferença entre `data/processed/` e `outputs/`:

- `data/processed/` contém dados usados como entrada por etapas posteriores do pipeline.
- `outputs/` contém relatórios e resultados para análise, inspeção e documentação.

Exemplo:

- `data/processed/noticias_limpas.json` é usado para gerar embeddings.
- `outputs/cleaning_report.csv` é usado para mostrar a qualidade da limpeza.

---

## `src/`

A pasta `src/` contém a lógica principal do projeto.

Ela não deve depender diretamente do frontend.

Ela também não deve conter código específico de rotas HTTP.

Responsabilidade:

- Limpeza textual.
- Chunking.
- Geração de embeddings.
- Indexação no ChromaDB.
- Busca semântica.
- Busca léxica.
- Busca híbrida.
- Reranking.
- Cálculo de métricas.
- Configurações e schemas internos.

Arquivos esperados:

- `config.py`
- `cleaning.py`
- `chunking.py`
- `embeddings.py`
- `vector_store.py`
- `lexical_search.py`
- `hybrid_search.py`
- `rerank.py`
- `search.py`
- `evaluate.py`
- `schemas.py`

Responsabilidade de cada arquivo:

### `src/config.py`

Centraliza caminhos e constantes do projeto.

Exemplos:

- caminho para `data/raw/noticias_brutas.json`;
- caminho para `data/processed/noticias_limpas.json`;
- caminho para `data/processed/chunks.jsonl`;
- caminho para `data/vector_store/chroma_db`;
- nome do modelo de embeddings;
- parâmetros de chunking;
- parâmetros de busca.

### `src/cleaning.py`

Responsável por:

- carregar dados brutos;
- remover HTML;
- decodificar entidades HTML;
- remover espaços duplicados;
- remover quebras excessivas;
- remover ou normalizar metadados embutidos no texto;
- gerar `texto_limpo`;
- gerar metadados derivados simples;
- salvar `data/processed/noticias_limpas.json`;
- gerar dados para `outputs/cleaning_report.csv`.

### `src/chunking.py`

Responsável por:

- dividir textos limpos em chunks;
- preservar metadados do artigo original;
- gerar `chunk_id`;
- salvar `data/processed/chunks.jsonl`.

### `src/embeddings.py`

Responsável por:

- carregar modelo `sentence-transformers`;
- gerar embeddings de artigos ou chunks;
- preparar textos no formato adequado para embedding.

### `src/vector_store.py`

Responsável por:

- criar ou carregar coleção local do ChromaDB;
- indexar documentos/chunks;
- salvar textos, embeddings e metadados;
- executar consultas vetoriais;
- aplicar filtros de metadados quando necessário.

### `src/lexical_search.py`

Responsável por:

- criar índice BM25;
- executar busca léxica;
- retornar ranking lexical com score BM25.

### `src/hybrid_search.py`

Responsável por:

- combinar resultados semânticos e léxicos;
- implementar Reciprocal Rank Fusion ou estratégia similar;
- retornar ranking híbrido.

### `src/rerank.py`

Responsável por:

- aplicar reranking opcional sobre candidatos recuperados;
- receber query e documentos candidatos;
- devolver ranking reordenado.

### `src/search.py`

Responsável por:

- orquestrar os modos de busca:
  - semântica;
  - léxica;
  - híbrida;
- aplicar filtros;
- aplicar reranking opcional;
- montar resposta padronizada para backend e CLI.

### `src/evaluate.py`

Responsável por:

- carregar queries de avaliação;
- carregar julgamentos de relevância;
- executar buscas;
- calcular métricas:
  - Precision@3;
  - Recall@5;
  - MRR;
  - nDCG@5;
- salvar `outputs/evaluation_results.csv`.

### `src/schemas.py`

Responsável por:

- definir estruturas internas de dados;
- padronizar campos de documentos, chunks, resultados de busca e métricas.

---

## `backend/`

A pasta `backend/` contém a aplicação FastAPI.

Responsabilidade:

- Expor endpoints HTTP.
- Receber requisições do frontend.
- Chamar os serviços que usam a lógica de `src/`.
- Servir arquivos estáticos do frontend.
- Não duplicar lógica de busca, limpeza ou avaliação.

Arquivos esperados:

backend/
├── main.py
├── routes/
│   ├── search_routes.py
│   ├── evaluation_routes.py
│   ├── document_routes.py
│   └── pipeline_routes.py
└── services/
    ├── search_service.py
    ├── evaluation_service.py
    └── pipeline_service.py

### `backend/main.py`

Responsável por:

- criar aplicação FastAPI;
- registrar rotas;
- configurar CORS se necessário;
- servir frontend estático;
- expor `/health`.

### `backend/routes/`

Contém as rotas HTTP.

Rotas sugeridas:

- `GET /`
- `GET /health`
- `POST /search`
- `POST /evaluate`
- `GET /metrics`
- `GET /documents/{article_id}`
- `POST /pipeline/run`

### `backend/services/`

Contém serviços usados pelas rotas.

Regras:

- Services podem chamar `src/search.py`, `src/evaluate.py`, `src/cleaning.py`, etc.
- Services não devem conter lógica pesada duplicada.
- Services traduzem requisições HTTP para chamadas dos módulos do projeto.

---

## `frontend/`

A pasta `frontend/` contém a interface web estática.

Responsabilidade:

- Exibir campo de busca.
- Permitir seleção do tipo de busca.
- Permitir aplicação de filtros.
- Exibir resultados em cards.
- Exibir métricas técnicas quando ativado.
- Exibir resultados de avaliação quando solicitado.

Arquivos esperados:

frontend/
├── index.html
├── styles.css
├── app.js
└── assets/

### `frontend/index.html`

Estrutura da página.

Deve conter:

- campo de busca;
- seletor de tipo de busca;
- checkbox de reranking;
- checkbox de detalhes técnicos;
- filtros de fonte, período e tema econômico;
- área de resultados;
- área de avaliação.

### `frontend/styles.css`

Estilos da interface.

Pode ser gerado ou inspirado por Google Stitch, mas deve ser simples de manter.

### `frontend/app.js`

Responsável por:

- ler inputs da interface;
- chamar endpoints do backend com `fetch`;
- renderizar resultados;
- renderizar métricas;
- tratar erros simples.

### `frontend/assets/`

Armazena imagens, ícones ou arquivos estáticos auxiliares.

---

## `evaluation/`

A pasta `evaluation/` contém arquivos que definem a avaliação.

Ela não armazena resultados finais. Resultados finais ficam em `outputs/`.

Deve conter:

- `queries_obrigatorias.json`
- `relevance_judgments.json`

### `evaluation/queries_obrigatorias.json`

Contém as queries exigidas pelo desafio:

- "mudanças na taxa de juros"
- "mercado de trabalho e desemprego"
- "inflação e preços ao consumidor"

### `evaluation/relevance_judgments.json`

Contém julgamentos manuais de relevância para as queries avaliadas.

Exemplo:

[
  {
    "query": "mudanças na taxa de juros",
    "relevance": {
      "1": 3,
      "2": 2,
      "3": 0
    }
  }
]

Escala sugerida:

- 0: irrelevante
- 1: parcialmente relevante
- 2: relevante
- 3: altamente relevante

Regras:

- Precision, Recall, MRR e nDCG só devem ser calculados para queries presentes nesse arquivo.
- Não calcular essas métricas para queries livres sem julgamentos de relevância.

---

## `tests/`

A pasta `tests/` contém testes automatizados simples.

Responsabilidade:

- Testar funções críticas.
- Garantir que a limpeza não quebre.
- Garantir que chunking preserva metadados.
- Garantir que métricas são calculadas corretamente.

Arquivos sugeridos:

- `test_cleaning.py`
- `test_chunking.py`
- `test_search.py`
- `test_metrics.py`

---

## `docs/`

A pasta `docs/` contém documentação complementar.

Pode conter:

- `architecture.md`
- `evaluation.md`
- `decisions.md`

Responsabilidade:

- Explicar decisões técnicas que ficariam longas demais no README.
- Documentar trade-offs.
- Documentar limitações e próximos passos.

---

# Filtros da interface

Implementar somente estes filtros inicialmente:

1. Fonte.
2. Período/data inicial e final.
3. Tema econômico.

O tema econômico deve ser criado por heurística simples a partir de título e texto limpo.

Temas sugeridos:

- juros
- inflação
- mercado_trabalho
- atividade_economica
- confianca
- cambio
- fiscal
- outros

---

# Tipos de busca

A interface deve permitir selecionar:

1. Busca semântica.
2. Busca léxica.
3. Busca híbrida.

Também deve haver uma opção para aplicar reranking.

A busca híbrida deve combinar busca semântica e busca léxica, preferencialmente usando Reciprocal Rank Fusion.

---

# Métricas exibidas

Para cada resultado individual, exibir quando disponível:

- distância vetorial;
- similaridade vetorial aproximada;
- score BM25;
- score RRF;
- score de reranking.

Para avaliação das queries obrigatórias, calcular:

- Precision@3;
- Recall@5;
- MRR;
- nDCG@5.

Não calcular Precision, Recall, MRR ou nDCG para queries livres sem julgamentos de relevância.

---

# Fluxo de desenvolvimento

O desenvolvimento deve seguir a ordem abaixo.

## 1. Setup do projeto

Criar estrutura inicial de pastas e arquivos.

Branch:

`chore/project-setup`

Objetivo:

- criar diretórios;
- criar arquivos-base;
- criar `src/config.py`;
- criar `requirements.txt`;
- criar README inicial;
- garantir que o repositório está organizado.

Não implementar pipeline completo nessa etapa.

---

## 2. Limpeza de dados

Branch:

`feat/text-cleaning`

Objetivo:

- carregar `data/raw/noticias_brutas.json`;
- limpar textos;
- salvar `data/processed/noticias_limpas.json`;
- gerar `outputs/cleaning_report.csv`.

Essa é a primeira etapa funcional do pipeline.

---

## 3. Enriquecimento de metadados

Branch:

`feat/metadata-enrichment`

Objetivo:

- criar campos derivados:
  - `ano`;
  - `mes`;
  - `tema_economico`;
- preservar:
  - `article_id`;
  - `titulo`;
  - `data`;
  - `fonte`;
  - `texto_limpo`.

---

## 4. Chunking

Branch:

`feat/chunking`

Objetivo:

- gerar chunks a partir dos textos limpos;
- preservar metadados;
- salvar `data/processed/chunks.jsonl`.

---

## 5. Embeddings e ChromaDB

Branch:

`feat/vector-store`

Objetivo:

- gerar embeddings;
- criar coleção local no ChromaDB;
- indexar chunks com metadados;
- garantir que o banco pode ser reconstruído pelo pipeline.

---

## 6. Busca semântica

Branch:

`feat/semantic-search`

Objetivo:

- implementar busca vetorial;
- retornar distância vetorial;
- retornar similaridade aproximada;
- aplicar filtros de fonte, período e tema econômico.

---

## 7. Busca léxica e híbrida

Branch:

`feat/hybrid-search`

Objetivo:

- implementar BM25;
- implementar busca léxica;
- implementar busca híbrida;
- combinar rankings com RRF ou estratégia equivalente.

---

## 8. Reranking

Branch:

`feat/reranking`

Objetivo:

- implementar reranking opcional;
- aplicar reranking sobre os candidatos recuperados;
- retornar score de reranking.

---

## 9. Métricas de avaliação

Branch:

`feat/evaluation-metrics`

Objetivo:

- criar arquivos em `evaluation/`;
- implementar Precision@3;
- implementar Recall@5;
- implementar MRR;
- implementar nDCG@5;
- salvar resultados em `outputs/evaluation_results.csv`.

---

## 10. Backend FastAPI

Branch:

`feat/backend-api`

Objetivo:

- criar API;
- expor `/search`;
- expor `/evaluate`;
- expor `/metrics`;
- expor `/documents/{article_id}`;
- servir frontend estático.

---

## 11. Frontend

Branch:

`feat/frontend-ui`

Objetivo:

- criar interface HTML/CSS/JS;
- permitir seleção do tipo de busca;
- permitir filtros;
- permitir reranking;
- exibir resultados;
- exibir detalhes técnicos.

---

## 12. Docker

Branch:

`chore/docker-setup`

Objetivo:

- criar `Dockerfile`;
- criar `docker-compose.yml`;
- documentar execução via Docker;
- garantir que Docker é uma opção, não a única forma de rodar.

---

## 13. Documentação final

Branch:

`docs/final-submission`

Objetivo:

- finalizar README;
- explicar arquitetura;
- explicar pipeline;
- explicar decisões técnicas;
- explicar métricas;
- mostrar exemplos das queries obrigatórias;
- documentar execução local e com Docker;
- documentar limitações e próximos passos.

---

# Padrões de código

- Código Python claro, modular e tipado quando possível.
- Evitar overengineering.
- Preferir funções pequenas e testáveis.
- Não duplicar lógica entre backend e src.
- Backend deve chamar services, e services devem usar os módulos de `src`.
- O pipeline deve ser reproduzível a partir de `data/raw/noticias_brutas.json`.
- Não adicionar dependências sem necessidade clara.
- Não misturar código de frontend dentro de `src`.
- Não misturar lógica de busca dentro de arquivos de rota do FastAPI.

---

# Padrão de commits

Usar Conventional Commits:

- feat:
- fix:
- docs:
- test:
- refactor:
- chore:

Exemplos:

feat(cleaning): implement html text normalization
feat(search): add semantic search with chromadb
feat(hybrid): add bm25 and rrf fusion
feat(frontend): add metadata filters
docs(readme): document architecture and setup
chore(docker): add docker compose setup

---

# Instruções para o agente

Antes de implementar:

1. Verifique a branch atual.
2. Leia este `AGENTS.md`.
3. Leia o `README.md`.
4. Caso exista, leia `instruction.md`.
5. Entenda o escopo da branch atual.

Ao criar uma funcionalidade:

1. Implemente somente o escopo da branch.
2. Adicione teste simples quando fizer sentido.
3. Atualize documentação mínima.
4. Garanta que o pipeline continue executando.
5. Não altere a arquitetura sem justificar.
6. Não crie dependências desnecessárias.
7. Não implemente funcionalidades futuras fora da etapa atual.

Sempre priorize uma solução funcional, reproduzível e bem documentada.

Caso ainda precise de instruções sobre funcionamento do projeto e entrega, consulte o arquivo `instruction.md`.