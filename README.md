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

## Busca Semântica

O motor de busca semântico está implementado em `src/search.py`. Ele recebe uma consulta em texto livre, gera o embedding da query com o mesmo modelo usado na indexação (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) e consulta a coleção ChromaDB `fgv_ibre_news_chunks`.

A resposta padronizada contém a query, o tipo de busca, os filtros aplicados e uma lista ranqueada de chunks com metadados, documento recuperado, distância vetorial e similaridade aproximada. Como a coleção usa distância cosseno, a similaridade exibida é calculada como:

```text
similarity = 1 - distance
```

Distância menor indica maior proximidade vetorial. Similaridade maior indica maior proximidade semântica aproximada. Esses valores explicam a proximidade entre query e chunk; já as métricas de ranking avaliam a qualidade da ordem dos documentos recuperados contra julgamentos manuais de relevância.

Filtros disponíveis nesta etapa:

- `fonte`
- `date_start`
- `date_end`
- `content_quality`

Os filtros de data são convertidos para `date_int` no formato `YYYYMMDD` antes da consulta ao ChromaDB.

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

Execute a busca semântica por CLI:

```bash
python -m src.search "mudanças na taxa de juros"
python -m src.search "mudanças na taxa de juros" --top-k 5
python -m src.search "mudanças na taxa de juros" --fonte "Banco Central do Brasil"
python -m src.search "mudanças na taxa de juros" --date-start 2023-08-01 --date-end 2023-08-31
python -m src.search "receita de bolo de chocolate" --min-similarity 0.35
```

Execute a avaliação das queries obrigatórias:

```bash
python -m src.evaluate --top-k 5
```

Saídas geradas:

- `data/processed/chunks.jsonl`
- `data/vector_store/chroma_db/`
- `outputs/search_examples.json`
- `outputs/evaluation_results.csv`

## Avaliação

A avaliação usa as três queries obrigatórias do desafio em `evaluation/queries_obrigatorias.json` e julgamentos manuais em `evaluation/relevance_judgments.json`. Os julgamentos usam `article_id`, não `chunk_id`, e seguem a escala:

- `0`: irrelevante
- `1`: parcialmente relevante
- `2`: relevante
- `3`: altamente relevante

Quando múltiplos chunks do mesmo artigo aparecem no ranking, a avaliação deduplica por `article_id` antes de calcular as métricas.

Métricas calculadas:

- `Precision@3`: fração dos 3 primeiros documentos que são relevantes.
- `Recall@5`: fração dos documentos relevantes recuperada nos 5 primeiros resultados.
- `MRR`: recíproco da posição do primeiro documento relevante.
- `nDCG@5`: qualidade do ranking nos 5 primeiros resultados usando relevância graduada de 0 a 3.

Resultados atuais em `outputs/evaluation_results.csv`:

| Query | Precision@3 | Recall@5 | MRR | nDCG@5 | Artigos recuperados |
| --- | ---: | ---: | ---: | ---: | --- |
| mudanças na taxa de juros | 1.000000 | 1.000000 | 1.000000 | 0.972898 | `[1, 11, 10, 6, 7]` |
| mercado de trabalho e desemprego | 1.000000 | 0.750000 | 1.000000 | 0.965119 | `[14, 4, 19, 3, 15]` |
| inflação e preços ao consumidor | 0.666667 | 0.375000 | 1.000000 | 0.512367 | `[9, 11, 15, 1, 20]` |

Exemplos top 5 gerados em `outputs/search_examples.json`:

| Query | Top 5 resultados |
| --- | --- |
| mudanças na taxa de juros | 1. Copom mantém Selic em 13,75% ao ano pela quarta reunião consecutiva; 2. Selic deve recuar a 9% até o fim de 2024, projetam economistas; 3. Crédito total no Brasil atinge R$ 5,6 trilhões com desaceleração no crescimento; 4. Copom inicia ciclo de corte e reduz Selic para 13,25%; 5. Inadimplência das famílias sobe para 6,3% em julho, aponta BC |
| mercado de trabalho e desemprego | 1. Desemprego juvenil no Brasil ainda preocupa apesar de melhora geral; 2. Taxa de desemprego cai para 7,9% no segundo trimestre, menor nível desde 2014; 3. Setor de serviços cresce 0,6% em junho e supera expectativas; 4. PIB do Brasil cresce 1,9% no segundo trimestre de 2023; 5. Câmbio: real se fortalece com melhora do ambiente externo e fiscal |
| inflação e preços ao consumidor | 1. Inflação ao produtor (IPA) desacelera e pressão sobre preços finais diminui; 2. Selic deve recuar a 9% até o fim de 2024, projetam economistas; 3. Câmbio: real se fortalece com melhora do ambiente externo e fiscal; 4. Copom mantém Selic em 13,75% ao ano pela quarta reunião consecutiva; 5. Expectativas para o PIB de 2023 sobem para 2,5% após resultado do segundo trimestre |

Para consultas fora do domínio econômico, use `--min-similarity` para descartar resultados fracos. Exemplo validado:

```bash
python -m src.search "receita de bolo de chocolate" --top-k 5 --min-similarity 0.35
```

Retorno: `results: []`.

Busca léxica, busca híbrida e reranking não foram implementados nesta branch. O requisito principal do desafio é o motor de busca semântico, então esta etapa prioriza ChromaDB, distância cosseno, filtros por metadados, limiar de similaridade e métricas de ranking. Essas funcionalidades ficam como features opcionais para branches futuras.

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

Implementada a preparação, indexação vetorial e busca semântica:

- limpeza textual disponível em `src/cleaning.py`;
- geração de chunks em `src/chunking.py`;
- geração de embeddings em `src/embeddings.py`;
- indexação local em ChromaDB em `src/vector_store.py`.
- busca semântica com filtros em `src/search.py`;
- métricas de ranking em `src/evaluate.py`;
- avaliação salva em `outputs/evaluation_results.csv`;
- exemplos de busca salvos em `outputs/search_examples.json`.

Ainda não foram implementados nesta branch:

- busca léxica;
- busca híbrida;
- reranking;
- backend;
- frontend.
