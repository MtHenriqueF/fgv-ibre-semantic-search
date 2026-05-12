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

## Como Rodar Futuramente

Nesta etapa, o pipeline funcional ainda não foi implementado. O repositório contém apenas a estrutura inicial e as configurações base.

Para validar o setup atual:

```bash
python run_pipeline.py
```

Saída esperada:

```text
Projeto fgv-ibre-semantic-search inicializado. As etapas do pipeline ainda serao implementadas.
```

Quando as próximas etapas forem implementadas, o fluxo previsto será:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py
```

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

Setup inicial do projeto.

Ainda não foram implementados:

- pipeline de limpeza;
- geração de chunks;
- embeddings;
- ChromaDB;
- busca;
- avaliação;
- backend;
- frontend.
