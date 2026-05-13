# FGV IBRE Semantic Search

Projeto para o Desafio Técnico de Estágio em Ciência de Dados do FGV IBRE.

## Contexto

O desafio propõe a construção de um mini motor de busca semântico aplicado a notícias econômicas fictícias. A solução deve demonstrar um fluxo reproduzível para limpeza textual, geração de embeddings, indexação local, recuperação por similaridade e avaliação dos resultados.

## Objetivo

Construir uma aplicação local e simples de executar para:

- limpar notícias econômicas brutas;
- gerar dados processados e chunks com metadados;
- criar embeddings com `sentence-transformers`;
- indexar os vetores em ChromaDB local;
- comparar busca semântica, léxica e híbrida;
- avaliar resultados com métricas de ranking;
- expor uma API FastAPI e uma interface web estática em etapas futuras.

## Arquitetura Planejada

A arquitetura será organizada em camadas simples:

- `src/`: lógica principal do projeto, incluindo limpeza, chunking, embeddings, busca e avaliação;
- `backend/`: aplicação FastAPI e services que chamam a lógica de `src/`;
- `frontend/`: HTML, CSS e JavaScript estáticos servidos pelo backend;
- `data/`: entrada bruta, dados processados e banco vetorial local reconstruível;
- `evaluation/`: queries e julgamentos de relevância;
- `outputs/`: relatórios e resultados gerados para inspeção.

O banco vetorial planejado é o ChromaDB local. O projeto não terá autenticação, login, billing, SaaS ou dependência de banco remoto.

## Estrutura de Diretórios

```text
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
```

## Pipeline Vetorial

A etapa atual prepara os dados limpos para indexação vetorial local:

1. `src/chunking.py` lê `data/processed/noticias_limpas.json`.
2. Cada notícia é dividida em chunks com `RecursiveCharacterTextSplitter`, preservando metadados do artigo.
3. O campo `document` é criado como texto natural no formato `{titulo}. {texto_do_chunk}`.
4. `src/embeddings.py` gera embeddings com `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
5. `src/vector_store.py` recria a coleção `fgv_ibre_news_chunks` no ChromaDB local.

O JSON completo do chunk não é enviado para embedding. A separação é intencional:

- `id`: identificador único do chunk;
- `document`: texto puro usado para busca semântica;
- `embedding`: vetor numérico gerado a partir do `document`;
- `metadata`: campos estruturados usados para filtros e exibição.

Essa decisão evita que chaves JSON, nomes de campos e valores administrativos contaminem o vetor semântico. O ChromaDB armazena os metadados separadamente, incluindo `article_id`, `chunk_id`, `chunk_index`, `titulo`, `data`, `date_int`, `ano`, `mes`, `fonte` e `content_quality`. O campo `date_int` é derivado de `data` no formato `YYYYMMDD`, permitindo filtros futuros por intervalo de datas, além de filtros por fonte e qualidade.

O chunking usa `chunk_size=900`, `chunk_overlap=120` e separadores `["\n\n", ". ", "! ", "? ", "; ", ", ", ".", "!", "?", " ", ""]`. Como as notícias limpas atuais são curtas, cada notícia tende a gerar um único chunk, mantendo o contexto completo do artigo.

A coleção é configurada com distância cosseno e índice HNSW quando suportado pela versão instalada do ChromaDB. O banco vetorial persistente fica em `data/vector_store/chroma_db/` e pode ser reconstruído a partir dos dados processados.

## Como Rodar

Instale as dependências e execute o pipeline:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py
```

Também é possível executar as etapas separadamente:

```bash
python -m src.chunking
python -m src.vector_store
```

Saídas geradas:

- `data/processed/chunks.jsonl`
- `data/vector_store/chroma_db/`

## Roadmap Resumido

1. Setup inicial do repositório.
2. Limpeza dos dados brutos.
3. Enriquecimento de metadados.
4. Geração de chunks.
5. Embeddings e indexação em ChromaDB.
6. Busca semântica com filtros.
7. Busca léxica e busca híbrida.
8. Reranking opcional.
9. Métricas de avaliação.
10. Backend FastAPI.
11. Frontend estático.
12. Docker como opção de execução.
13. Documentação final.

## Status Atual

Implementada a preparação e indexação vetorial:

- limpeza textual disponível em `src/cleaning.py`;
- geração de chunks em `src/chunking.py`;
- geração de embeddings em `src/embeddings.py`;
- indexação local em ChromaDB em `src/vector_store.py`.

Ainda não foram implementados nesta branch:

- busca semântica para usuário final;
- busca léxica;
- busca híbrida;
- reranking;
- avaliação;
- backend;
- frontend.
