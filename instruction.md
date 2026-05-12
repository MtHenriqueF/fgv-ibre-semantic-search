# Desafio Técnico — Estágio em Ciência de Dados
**FGV IBRE — Instituto Brasileiro de Economia**

---

## Contexto

O FGV IBRE produz indicadores econômicos de referência para o Brasil — como o IGP-M, o IPC e o ICC — e publica dezenas de notas técnicas por mês. Nesse volume de produção textual, a capacidade de **buscar e recuperar informação relevante** de forma eficiente é cada vez mais valiosa.

Neste desafio, você vai construir um **mini motor de busca semântico** aplicado a notícias econômicas. O objetivo não é implementar um sistema de produção, mas demonstrar que você sabe limpar dados textuais, aplicar modelos de linguagem e raciocinar sobre similaridade semântica.

---

## Visão Geral

O desafio está dividido em **três etapas encadeadas**:

```
noticias_brutas.json  →  [Etapa 1: Limpeza]  →  dados_limpos
                                                         ↓
                                               [Etapa 2: Embeddings]
                                                         ↓
                                               [Etapa 3: Busca Semântica]
```

Você deve entregar uma solução em python, além de um `README` explicando suas decisões.

---

## Dados

O arquivo `dados/noticias_brutas.json` contém 20 notícias fictícias sobre a economia brasileira. Cada entrada tem a seguinte estrutura:

```json
{
  "id": 1,
  "titulo": "...",
  "texto": "texto com sujeiras diversas",
  "data": "YYYY-MM-DD",
  "fonte": "..."
}
```

O campo `texto` contém intencionalmente diversos tipos de "sujeira":
- Tags HTML (`<p>`, `<strong>`, `<br/>`, `<a href=...>`)
- Entidades HTML (`&amp;`, `&nbsp;`, `&eacute;`, `&ccedil;`, etc.)
- Múltiplas quebras de linha consecutivas
- Espaços em excesso entre palavras
- Timestamps e metadados embutidos no corpo do texto
- Alguns artigos com conteúdo mínimo (casos extremos)

---

## Etapa 1 — Limpeza e Tratamento de Texto

Transforme os textos brutos em texto limpo e estruturado, lidando com as imperfeições presentes no campo `texto`. Os dados tratados devem ser salvos localmente para uso nas etapas seguintes.

---

## Etapa 2 — Geração de Embeddings

Utilize a biblioteca `sentence-transformers` para representar cada texto como um vetor numérico. No seu `README`, justifique o modelo escolhido.

---

## Etapa 3 — Motor de Busca Semântico

Implemente uma busca que receba uma consulta em texto livre e retorne os artigos mais relevantes do corpus, com base em similaridade semântica. Valide seu motor com as queries abaixo:

```
"mudanças na taxa de juros"
"mercado de trabalho e desemprego"
"inflação e preços ao consumidor"
```

---

## Entregáveis

Crie um repositório público no GitHub com a sua solução contendo:

- Código Python cobrindo as três etapas (organizado da forma que preferir)
- O arquivo de dados limpos gerado na Etapa 1
- Um `README.md` explicando suas decisões, como rodar o projeto e uma avaliação qualitativa dos resultados

**A solução deve ser facilmente reproduzível:** qualquer pessoa deve conseguir clonar o repositório e executar o pipeline do zero sem dificuldades.

> **Não é necessário** incluir o arquivo de embeddings no repositório se ele for muito grande. Basta garantir que o script da Etapa 2 seja reproduzível.

---

## Instruções de Entrega

1. Crie um repositório **público** no GitHub com a sua solução
2. Certifique-se de que o repositório contém todos os entregáveis listados acima
3. Preencha o formulário de entrega com seu nome, e-mail e o link do repositório:

**👉 [Formulário de Entrega](https://forms.office.com/r/vuaGLA1qLy)**

**Prazo:** conforme comunicado no processo seletivo.

---

Boa sorte!