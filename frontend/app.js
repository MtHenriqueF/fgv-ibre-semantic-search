const DEFAULT_EXAMPLES = [
    "mudanças na taxa de juros",
    "mercado de trabalho e desemprego",
    "inflação e preços ao consumidor",
];

const CONTENT_QUALITY_LABELS = {
    empty: "Texto vazio",
    very_short: "Notícia curta",
    short: "Notícia curta",
    ok: "Notícia normal",
};

const state = {
    evaluationLoaded: false,
    dateMin: "",
    dateMax: "",
};

const elements = {
    queryInput: document.querySelector("#query-input"),
    searchForm: document.querySelector("#search-form"),
    sourceFilter: document.querySelector("#source-filter"),
    qualityFilter: document.querySelector("#quality-filter"),
    dateStartFilter: document.querySelector("#date-start-filter"),
    dateEndFilter: document.querySelector("#date-end-filter"),
    dateHelperText: document.querySelector("#date-helper-text"),
    dateErrorText: document.querySelector("#date-error-text"),
    topKFilter: document.querySelector("#top-k-filter"),
    similarityFilter: document.querySelector("#similarity-filter"),
    similarityValue: document.querySelector("#similarity-value"),
    technicalToggle: document.querySelector("#technical-toggle"),
    exampleChips: document.querySelector("#example-chips"),
    resultsCount: document.querySelector("#results-count"),
    resultsContext: document.querySelector("#results-context"),
    searchResults: document.querySelector("#search-results"),
    metricsSummary: document.querySelector("#metrics-summary"),
    evaluationTableBody: document.querySelector("#evaluation-table-body"),
    evaluationDetails: document.querySelector("#evaluation-details"),
    articleDialog: document.querySelector("#article-dialog"),
    dialogTitle: document.querySelector("#dialog-title"),
    dialogMeta: document.querySelector("#dialog-meta"),
    dialogContent: document.querySelector("#dialog-content"),
    closeDialogButton: document.querySelector("#close-dialog-button"),
};

document.addEventListener("DOMContentLoaded", async () => {
    bindTabs();
    bindEvents();
    renderExampleChips(DEFAULT_EXAMPLES);
    await Promise.all([loadMetadata(), loadExamples()]);
});

function bindTabs() {
    document.querySelectorAll("[data-tab-target]").forEach((button) => {
        button.addEventListener("click", async () => {
            const target = button.dataset.tabTarget;

            document.querySelectorAll("[data-tab-target]").forEach((item) => {
                item.classList.toggle("is-active", item === button);
            });
            document.querySelectorAll("[data-tab-panel]").forEach((panel) => {
                panel.classList.toggle("is-active", panel.dataset.tabPanel === target);
            });

            if (target === "evaluation" && !state.evaluationLoaded) {
                await loadEvaluation();
            }
        });
    });
}

function bindEvents() {
    elements.searchForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await runSearch();
    });

    elements.similarityFilter.addEventListener("input", () => {
        elements.similarityValue.textContent = Number(elements.similarityFilter.value).toFixed(2);
    });

    [elements.dateStartFilter, elements.dateEndFilter].forEach((input) => {
        input.addEventListener("change", () => {
            clearDateError();
        });
    });

    elements.closeDialogButton.addEventListener("click", () => elements.articleDialog.close());
}

async function loadMetadata() {
    try {
        const metadata = await fetchJson("/api/metadata");
        fillSelect(elements.sourceFilter, metadata.fontes);
        fillSelect(elements.qualityFilter, metadata.content_quality, formatContentQualityLabel);
        elements.dateStartFilter.min = metadata.date_min || "";
        elements.dateStartFilter.max = metadata.date_max || "";
        elements.dateEndFilter.min = metadata.date_min || "";
        elements.dateEndFilter.max = metadata.date_max || "";
        state.dateMin = metadata.date_min || "";
        state.dateMax = metadata.date_max || "";
        renderDateHelperText(state.dateMin, state.dateMax);
    } catch (error) {
        renderSearchMessage("Não foi possível carregar os filtros disponíveis.", "error-state");
    }
}

async function loadExamples() {
    try {
        const payload = await fetchJson("/api/search/examples");
        const examples = payload.examples.map((example) => example.query);
        if (examples.length) {
            renderExampleChips(examples);
        }
    } catch (error) {
        // Fallback local já renderizado.
    }
}

function fillSelect(select, values, formatLabel = (value) => value) {
    values.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = formatLabel(value);
        select.append(option);
    });
}

function renderExampleChips(examples) {
    elements.exampleChips.innerHTML = "";
    examples.forEach((query) => {
        const button = document.createElement("button");
        button.className = "chip";
        button.type = "button";
        button.textContent = query;
        button.addEventListener("click", () => {
            elements.queryInput.value = query;
            elements.queryInput.focus();
        });
        elements.exampleChips.append(button);
    });
}

async function runSearch() {
    const query = elements.queryInput.value.trim();
    if (!query) {
        return;
    }

    const dateValidation = validateDateFilters(
        elements.dateStartFilter.value,
        elements.dateEndFilter.value,
        state.dateMin,
        state.dateMax,
    );
    if (!dateValidation.valid) {
        renderDateError(dateValidation.message);
        return;
    }
    clearDateError();

    const payload = {
        query,
        top_k: Number(elements.topKFilter.value),
        min_similarity: Number(elements.similarityFilter.value),
        filters: compactObject({
            fonte: elements.sourceFilter.value,
            content_quality: elements.qualityFilter.value,
            date_start: elements.dateStartFilter.value,
            date_end: elements.dateEndFilter.value,
        }),
    };

    if (!Object.keys(payload.filters).length) {
        payload.filters = null;
    }

    elements.resultsCount.textContent = "Buscando...";
    elements.resultsContext.textContent = "";
    elements.searchResults.innerHTML = "";

    try {
        const response = await fetchJson("/api/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        renderSearchResults(response);
    } catch (error) {
        renderSearchMessage(error.message || "Não foi possível executar a busca.", "error-state");
    }
}

function renderSearchResults(response) {
    const results = response.results || [];
    elements.resultsCount.textContent = `${results.length} resultado${results.length === 1 ? "" : "s"}`;
    elements.resultsContext.textContent = `similaridade mínima ${formatMetric(response.min_similarity ?? 0)}`;

    if (!results.length) {
        renderSearchMessage("Nenhum resultado passou pelo limiar configurado.", "empty-state");
        return;
    }

    elements.searchResults.innerHTML = "";
    results.forEach((result) => {
        const card = document.createElement("article");
        card.className = "result-card";
        card.innerHTML = `
            <div class="result-card__head">
                <span class="result-rank">#${result.rank}</span>
                <span class="meta-pill">${escapeHtml(result.fonte)}</span>
                <span class="meta-pill">${escapeHtml(result.data)}</span>
                <span class="meta-pill score-pill">Similaridade ${formatMetric(result.similarity)}</span>
            </div>
            <h3>${escapeHtml(result.titulo)}</h3>
            <p class="result-card__document">${escapeHtml(result.document)}</p>
            <div class="result-card__footer">
                <div class="result-card__meta">
                    <span>Article ID: ${result.article_id}</span>
                    <span>Chunk: ${result.chunk_index ?? "-"}</span>
                </div>
                <button class="button button--secondary" type="button" data-article-id="${result.article_id}">
                    Ver notícia completa
                </button>
            </div>
            ${elements.technicalToggle.checked ? renderTechnicalBlock(result) : ""}
        `;
        card.querySelector("[data-article-id]").addEventListener("click", () => {
            openDocument(result.article_id);
        });
        elements.searchResults.append(card);
    });
}

function renderTechnicalBlock(result) {
    return `
        <div class="technical-block">
            <span>Distância cosseno: ${formatMetric(result.distance)}</span>
            <span>Similaridade cosseno: ${formatMetric(result.similarity)}</span>
            <span>Chunk ID: ${escapeHtml(result.chunk_id)}</span>
            <span>Tipo de busca: ${escapeHtml(result.search_type || "semantic")}</span>
        </div>
    `;
}

function renderSearchMessage(message, className) {
    elements.resultsCount.textContent = "";
    elements.resultsContext.textContent = "";
    elements.searchResults.innerHTML = `<div class="${className}">${escapeHtml(message)}</div>`;
}

async function openDocument(articleId) {
    try {
        const documentPayload = await fetchJson(`/api/documents/${articleId}`);
        elements.dialogTitle.textContent = documentPayload.titulo;
        elements.dialogMeta.textContent = `${documentPayload.fonte} | ${documentPayload.data} | Article ID ${documentPayload.article_id}`;
        elements.dialogContent.textContent = documentPayload.texto_limpo;
        elements.articleDialog.showModal();
    } catch (error) {
        renderSearchMessage(error.message || "Não foi possível carregar a notícia completa.", "error-state");
    }
}

async function loadEvaluation() {
    renderEvaluationMessage("Carregando avaliação...", "empty-state");

    try {
        const payload = await fetchJson("/api/evaluation");
        renderEvaluation(payload);
        state.evaluationLoaded = true;
    } catch (error) {
        renderEvaluationMessage(
            error.message || "Não foi possível carregar a avaliação. Tente novamente em alguns instantes.",
            "error-state",
        );
    }
}

function renderEvaluationMessage(message, className) {
    elements.metricsSummary.innerHTML = `<div class="${className}">${escapeHtml(message)}</div>`;
    elements.evaluationTableBody.innerHTML = "";
    elements.evaluationDetails.innerHTML = "";
}

function renderEvaluation(payload) {
    const summary = payload.metrics_summary;
    const metrics = [
        ["Precision@3 médio", summary.mean_precision_at_3],
        ["Recall@5 médio", summary.mean_recall_at_5],
        ["MRR médio", summary.mean_mrr],
        ["nDCG@5 médio", summary.mean_ndcg_at_5],
    ];

    elements.metricsSummary.innerHTML = metrics
        .map(([label, value]) => `
            <article class="metric-card">
                <span>${label}</span>
                <strong>${formatMetric(value)}</strong>
            </article>
        `)
        .join("");

    elements.evaluationTableBody.innerHTML = payload.queries
        .map((query) => `
            <tr>
                <td>${escapeHtml(query.query)}</td>
                <td>${formatMetric(query.metrics.precision_at_3)}</td>
                <td>${formatMetric(query.metrics.recall_at_5)}</td>
                <td>${formatMetric(query.metrics.mrr)}</td>
                <td>${formatMetric(query.metrics.ndcg_at_5)}</td>
            </tr>
        `)
        .join("");

    elements.evaluationDetails.innerHTML = payload.queries
        .map((query, index) => renderEvaluationDetail(query, index === 0))
        .join("");
}

function renderEvaluationDetail(query, openByDefault) {
    return `
        <details class="evaluation-detail" ${openByDefault ? "open" : ""}>
            <summary>
                <span>${escapeHtml(query.query)}</span>
                <span>nDCG@5 ${formatMetric(query.metrics.ndcg_at_5)}</span>
            </summary>
            <div class="evaluation-detail__body">
                <div class="evaluation-detail__metrics">
                    <span class="meta-pill">Precision@3 ${formatMetric(query.metrics.precision_at_3)}</span>
                    <span class="meta-pill">Recall@5 ${formatMetric(query.metrics.recall_at_5)}</span>
                    <span class="meta-pill">MRR ${formatMetric(query.metrics.mrr)}</span>
                    <span class="meta-pill">nDCG@5 ${formatMetric(query.metrics.ndcg_at_5)}</span>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Article ID</th>
                                <th>Chunk</th>
                                <th>Título</th>
                                <th>Fonte</th>
                                <th>Data</th>
                                <th>Distância</th>
                                <th>Similaridade</th>
                                <th>Relevância</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${query.results.map(renderEvaluationRow).join("")}
                        </tbody>
                    </table>
                </div>
            </div>
        </details>
    `;
}

function renderEvaluationRow(result) {
    return `
        <tr>
            <td>${result.rank}</td>
            <td>${result.article_id}</td>
            <td>${result.chunk_index ?? "-"}</td>
            <td>${escapeHtml(result.titulo)}</td>
            <td>${escapeHtml(result.fonte)}</td>
            <td>${escapeHtml(result.data)}</td>
            <td>${formatMetric(result.distance)}</td>
            <td>${formatMetric(result.similarity)}</td>
            <td><span class="relevance-pill" data-grade="${result.relevance_grade}">${result.relevance_grade}</span></td>
        </tr>
    `;
}

function compactObject(object) {
    return Object.fromEntries(
        Object.entries(object).filter(([, value]) => value !== "" && value !== null && value !== undefined),
    );
}

function formatContentQualityLabel(value) {
    return CONTENT_QUALITY_LABELS[value] || value;
}

function formatDateBR(isoDate) {
    if (!isoDate) {
        return "";
    }

    const [year, month, day] = isoDate.split("-");
    return `${day}/${month}/${year}`;
}

function validateDateFilters(dateStart, dateEnd, minDate, maxDate) {
    const formattedRange = `${formatDateBR(minDate)} e ${formatDateBR(maxDate)}`;

    if (dateStart && minDate && dateStart < minDate) {
        return {
            valid: false,
            message: `A data inicial deve estar entre ${formattedRange}.`,
        };
    }
    if (dateStart && maxDate && dateStart > maxDate) {
        return {
            valid: false,
            message: `A data inicial deve estar entre ${formattedRange}.`,
        };
    }
    if (dateEnd && minDate && dateEnd < minDate) {
        return {
            valid: false,
            message: `A data final deve estar entre ${formattedRange}.`,
        };
    }
    if (dateEnd && maxDate && dateEnd > maxDate) {
        return {
            valid: false,
            message: `A data final deve estar entre ${formattedRange}.`,
        };
    }
    if (dateStart && dateEnd && dateStart > dateEnd) {
        return {
            valid: false,
            message: "A data inicial não pode ser maior que a data final.",
        };
    }

    return { valid: true, message: "" };
}

function renderDateHelperText(minDate, maxDate) {
    if (!minDate || !maxDate) {
        elements.dateHelperText.textContent = "";
        return;
    }

    elements.dateHelperText.textContent = `Período disponível: ${formatDateBR(minDate)} até ${formatDateBR(maxDate)}`;
}

function renderDateError(message) {
    elements.dateErrorText.textContent = message;
}

function clearDateError() {
    elements.dateErrorText.textContent = "";
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        let detail = "";
        try {
            const payload = await response.json();
            detail = payload.detail || "";
        } catch (error) {
            detail = "";
        }
        throw new Error(detail || `Erro HTTP ${response.status}`);
    }
    return response.json();
}

function formatMetric(value) {
    return Number(value).toFixed(2);
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
