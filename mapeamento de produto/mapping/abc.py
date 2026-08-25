from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


def abc_class(cumulative: float) -> str:
    if cumulative <= 0.80 + 1e-12:
        return "A"
    if cumulative <= 0.95 + 1e-12:
        return "B"
    return "C"


def abc_table(rows: Iterable[dict[str, Any]], group_key: str, quantity_key: str = "quantity") -> list[dict[str, Any]]:
    totals: dict[str, float] = {}
    for row in rows:
        label = str(row.get(group_key) or "").strip()
        quantity = float(row.get(quantity_key) or 0)
        if label and quantity > 0:
            totals[label] = totals.get(label, 0.0) + quantity
    grand_total = sum(totals.values())
    result: list[dict[str, Any]] = []
    accumulated = 0.0
    for rank, (label, quantity) in enumerate(sorted(totals.items(), key=lambda item: (-item[1], item[0])), start=1):
        share = quantity / grand_total if grand_total else 0.0
        accumulated += share
        result.append({
            "rank": rank,
            "label": label,
            "quantity": quantity,
            "share": share,
            "accumulated": accumulated,
            "abc": abc_class(accumulated),
        })
    return result


def top_terms(values: Iterable[str], limit: int = 5) -> list[str]:
    counts = Counter(str(value).strip() for value in values if str(value).strip())
    return [term for term, _ in counts.most_common(limit)]
