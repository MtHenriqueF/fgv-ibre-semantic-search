from __future__ import annotations

import pytest

from src.evaluate import (
    dedupe_article_ids,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_precision_at_k() -> None:
    assert precision_at_k([1, 2, 3], {1, 3, 5}, 3) == pytest.approx(2 / 3)


def test_recall_at_k() -> None:
    assert recall_at_k([1, 2, 3, 4, 5], {1, 3, 5, 8}, 5) == pytest.approx(3 / 4)


def test_mrr() -> None:
    assert mrr([4, 2, 3], {3}) == pytest.approx(1 / 3)
    assert mrr([4, 2, 3], {8}) == 0.0


def test_ndcg_at_k() -> None:
    relevance_scores = {1: 3, 2: 2, 3: 1}

    assert ndcg_at_k([1, 2, 3], relevance_scores, 3) == pytest.approx(1.0)
    assert ndcg_at_k([3, 2, 1], relevance_scores, 3) < 1.0


def test_dedupe_article_ids_preserves_order() -> None:
    assert dedupe_article_ids([1, 1, 2, 3, 2]) == [1, 2, 3]
