from __future__ import annotations

from typing import Any

from .rules import FAMILY_RULES, family_for_product, normalize_text
from .xlsx_reader import SheetSnapshot


def as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


def consolidated_records(sheet: SheetSnapshot) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source_row, row in enumerate(sheet.rows[1:], start=2):
        product = str(row.get("H") or "").strip()
        client = str(row.get("A") or "").strip()
        if not product or not client:
            continue
        family = family_for_product(product)
        records.append({
            "source_row": source_row,
            "client_raw": client,
            "client_key": normalize_text(client),
            "product_code": str(row.get("B") or "").strip(),
            "quantity": as_float(row.get("C")),
            "channel": str(row.get("D") or "").strip(),
            "profile": str(row.get("E") or "").strip(),
            "segment": str(row.get("F") or "").strip(),
            "market_base": str(row.get("G") or "").strip(),
            "product": product,
            "technical_family": str(row.get("I") or "").strip(),
            "market_canonical": str(row.get("J") or "").strip(),
            "equipment_candidate_1": str(row.get("K") or "").strip(),
            "equipment_candidate_2": str(row.get("L") or "").strip(),
            "equipment_candidate_3": str(row.get("M") or "").strip(),
            "equipment_candidate_4": str(row.get("N") or "").strip(),
            "equipment_candidate_5": str(row.get("O") or "").strip(),
            "family_id": family.family_id if family else "",
        })
    return records


def family_records(records: list[dict[str, Any]], family_id: str) -> list[dict[str, Any]]:
    return [row for row in records if row.get("family_id") == family_id]
