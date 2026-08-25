from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import time
from typing import Any, Iterable

from .abc import abc_table, top_terms
from .parquet_io import read_parquet
from .rules import client_type, eligible_client, normalize_text


PILOT_PRODUCTS = [
    "VENT. FF/2-146 P 220V",
    "VENT. FS/4-400 EMBT - 230 V",
    "CONECTO FF",
    "MICROVENTILADOR A17251VBHBL - 110/220V",
    "VENT.FB/2-190MCD- 230V. 50/60",
    "VENT. FS/2-300 EM -  230 V",
    "VENT. TGH-240 V2- 220V. 60 HZ",
    "VENT. FF/2-160 VS- 220V. 60 HZ",
    "VENT. ECM 30 - 50/60HZ",
    "PLUS UNIC",
]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row}) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _terms_from_row(row: dict[str, Any], columns: Iterable[str]) -> list[str]:
    result: list[str] = []
    for column in columns:
        value = str(row.get(column) or "").strip()
        if value and value not in result:
            result.append(value)
    return result


def _dimension_terms(rows: list[dict[str, Any]], dimension: str) -> list[str]:
    if dimension == "market":
        values = [str(row.get("market_canonical") or row.get("market_base") or "Revisar — mercado não comprovado") for row in rows]
    elif dimension == "application":
        values = [str(row.get("technical_family") or "Revisar — aplicação não comprovada") for row in rows]
    else:
        values = []
        for row in rows:
            values.extend(_terms_from_row(row, ["equipment_candidate_1", "equipment_candidate_2", "equipment_candidate_3", "equipment_candidate_4", "equipment_candidate_5"]))
        values = values or [str(row.get("technical_family") or "Revisar — equipamento não comprovado") for row in rows]
    return top_terms(values, 5)


def _taxonomy_terms(data_dir: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for dimension, filename in [("market", "taxonomy_markets.csv"), ("application", "taxonomy_applications.csv"), ("equipment", "taxonomy_equipment.csv")]:
        terms: set[str] = set()
        for row in _load_csv(data_dir / "master" / filename):
            for key in ["controlled_name", "terms"]:
                for value in str(row.get(key) or "").split("|"):
                    normalized = normalize_text(value)
                    if normalized:
                        terms.add(normalized)
        result[dimension] = terms
    return result


def _load_cache(data_dir: Path) -> dict[str, dict[str, Any]]:
    from .parquet_io import read_parquet

    rows = read_parquet(data_dir / "master" / "client_master.parquet")
    cache: dict[str, dict[str, Any]] = {}
    for row in rows:
        cache.setdefault(str(row.get("client_key") or ""), row)
    return cache


def _product_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    positive = [row for row in rows if float(row.get("quantity") or 0) > 0]
    eligible = [row for row in positive if eligible_client(row.get("channel"), row.get("profile"), row.get("segment"))]
    return {
        "quantity_total": sum(float(row.get("quantity") or 0) for row in positive),
        "quantity_eligible": sum(float(row.get("quantity") or 0) for row in eligible),
        "quantity_excluded": sum(float(row.get("quantity") or 0) for row in positive if row not in eligible),
        "raw_rows": len(rows),
        "eligible_rows": len(eligible),
        "eligible_clients": len({normalize_text(row.get("client_raw")) for row in eligible}),
        "excluded_channels": dict(Counter(str(row.get("channel") or "") for row in positive if row not in eligible)),
    }


def _run_product(product: str, all_rows: list[dict[str, Any]], cache: dict[str, dict[str, Any]], taxonomy_terms: dict[str, set[str]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    rows = [row for row in all_rows if row.get("product") == product]
    positive = [row for row in rows if float(row.get("quantity") or 0) > 0]
    eligible = [row for row in positive if eligible_client(row.get("channel"), row.get("profile"), row.get("segment"))]
    family = str(eligible[0].get("technical_family") if eligible else positive[0].get("technical_family") if positive else "")
    clients_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        clients_by_key[normalize_text(row.get("client_raw"))].append(row)

    client_rows: list[dict[str, Any]] = []
    queue_by_key: dict[str, dict[str, Any]] = {}
    for abc_row in abc_table(eligible, "client_raw"):
        key = normalize_text(abc_row["label"])
        source = clients_by_key[key][0]
        cached = cache.get(key)
        customer_cache_reused = cached is not None
        market = str(cached.get("market") or source.get("market_canonical") or "Revisar — mercado não comprovado") if cached else str(source.get("market_canonical") or source.get("market_base") or "Revisar — mercado não comprovado")
        application = str(cached.get("application") or "Revisar — aplicação não comprovada") if cached else "Revisar — aplicação não comprovada"
        equipment = str(cached.get("equipment") or source.get("equipment_candidate_1") or "Revisar — equipamento não comprovado") if cached else str(source.get("equipment_candidate_1") or "Revisar — equipamento não comprovado")
        client_rows.append({
            "client": abc_row["label"],
            "quantity": abc_row["quantity"],
            "abc": abc_row["abc"],
            "type": str(cached.get("client_type") if cached else client_type(source.get("channel"))),
            "market": market,
            "application": application,
            "equipment": equipment,
            "confidence": str(cached.get("confidence") if cached else "Baixa"),
            "status": "Cliente reutilizado; família técnica nova" if customer_cache_reused else "Cliente sem cache",
            "cache_customer_reused": customer_cache_reused,
            "cache_family_reused": False,
        })
        if abc_row["abc"] in {"A", "B"}:
            queue_key = f"{key}|{family}"
            queue_by_key.setdefault(queue_key, {
                "unique_key": queue_key,
                "client_key": key,
                "client": abc_row["label"],
                "technical_family": family,
                "product_example": product,
                "priority": abc_row["abc"],
                "reason": "new_technical_family" if customer_cache_reused else "cache_miss",
                "customer_validation_reused": customer_cache_reused,
                "external_research_executed": False,
                "status": "pending_approval",
            })

    market_rows = [{**row, "market_group": row.get("market_canonical") or row.get("market_base") or "Revisar — mercado não comprovado"} for row in eligible]
    application_rows = [{**row, "application_group": (cache.get(normalize_text(row.get("client_raw"))) or {}).get("application") or "Revisar — aplicação não comprovada"} for row in eligible]
    equipment_rows = [{**row, "equipment_group": row.get("equipment_candidate_1") or "Revisar — equipamento não comprovado"} for row in eligible]
    market_abc = abc_table(market_rows, "market_group")
    application_abc = abc_table(application_rows, "application_group")
    equipment_abc = abc_table(equipment_rows, "equipment_group")
    new_terms: dict[str, list[str]] = {}
    for dimension, values in [("market", _dimension_terms(eligible, "market")), ("application", _dimension_terms(eligible, "application")), ("equipment", _dimension_terms(eligible, "equipment"))]:
        new_terms[dimension] = [value for value in values if normalize_text(value) not in taxonomy_terms[dimension]]

    customer_hits = sum(1 for row in client_rows if row["cache_customer_reused"])
    family_lookups = len(client_rows)
    result = {
        "product": product,
        "technical_family": family,
        "summary": _product_summary(rows),
        "clients": client_rows,
        "abc": {"markets": market_abc, "applications": application_abc, "equipment": equipment_abc},
        "cache": {
            "customer_hits": customer_hits,
            "customer_lookups": len(client_rows),
            "customer_hit_rate": customer_hits / len(client_rows) if client_rows else 1.0,
            "family_hits": 0,
            "family_lookups": family_lookups,
            "family_hit_rate": 0.0 if family_lookups else 1.0,
            "external_research_executed": False,
        },
        "differences": {
            "baseline": "No golden baseline exists for pilot products",
            "new_technical_family": family not in {"A12038", "AXIAL"},
            "unmapped_terms_by_dimension": {dimension: len(values) for dimension, values in new_terms.items()},
            "not_publicable_until_approval": True,
        },
        "new_terms_for_approval": new_terms,
        "research_queue": list(queue_by_key.values()),
    }
    return result, list(queue_by_key.values()), [{"product": product, "technical_family": family, "dimension": dimension, "term": term, "status": "pending_approval"} for dimension, terms in new_terms.items() for term in terms]


def run_pilot(input_parquet: str | Path, data_dir: str | Path, output_dir: str | Path, products: list[str] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    rows = read_parquet(input_parquet)
    load_seconds = time.perf_counter() - started
    root = Path(data_dir)
    cache = _load_cache(root)
    taxonomy_terms = _taxonomy_terms(root)
    cache_seconds = time.perf_counter() - started - load_seconds
    selected = products or PILOT_PRODUCTS
    available = {str(row.get("product")) for row in rows}
    missing = [product for product in selected if product not in available]
    if missing:
        raise ValueError(f"Pilot products absent from Parquet: {missing}")
    selection = []
    for product in selected:
        product_rows = [row for row in rows if row.get("product") == product and float(row.get("quantity") or 0) > 0]
        quantities = sum(float(row.get("quantity") or 0) for row in product_rows)
        selection.append({
            "product": product,
            "technical_family": str(product_rows[0].get("technical_family") if product_rows else ""),
            "quantity": quantities,
            "clients": len({normalize_text(row.get("client_raw")) for row in product_rows}),
            "volume_band": "high" if quantities >= 5000 else "medium" if quantities >= 500 else "low",
        })
    selection_seconds = time.perf_counter() - started - load_seconds - cache_seconds
    process_start = time.perf_counter()
    results = []
    queue: dict[str, dict[str, Any]] = {}
    terms: dict[str, dict[str, Any]] = {}
    for product in selected:
        result, product_queue, product_terms = _run_product(product, rows, cache, taxonomy_terms)
        results.append(result)
        for item in product_queue:
            queue[item["unique_key"]] = item
        for item in product_terms:
            terms[f"{item['dimension']}|{normalize_text(item['term'])}"] = item
    process_seconds = time.perf_counter() - process_start
    write_start = time.perf_counter()
    destination = Path(output_dir)
    _write_json(destination / "pilot_results.json", results)
    _write_json(destination / "research_queue.json", list(queue.values()))
    _write_json(destination / "new_terms_for_approval.json", list(terms.values()))
    _write_json(destination / "differences.json", [{"product": result["product"], **result["differences"]} for result in results])
    _write_csv(destination / "product_selection.csv", selection)
    manifest = {
        "pilot": "pilot_10",
        "products_requested": len(selected),
        "products_processed": len(results),
        "input": str(input_parquet),
        "source_read_count": 0,
        "external_research_executed": False,
        "cache_customer_hits": sum(result["cache"]["customer_hits"] for result in results),
        "cache_customer_lookups": sum(result["cache"]["customer_lookups"] for result in results),
        "cache_customer_hit_rate": sum(result["cache"]["customer_hits"] for result in results) / sum(result["cache"]["customer_lookups"] for result in results) if results else 1.0,
        "cache_family_hits": sum(result["cache"]["family_hits"] for result in results),
        "cache_family_lookups": sum(result["cache"]["family_lookups"] for result in results),
        "research_queue_count": len(queue),
        "new_terms_count": len(terms),
        "published": False,
        "steps_seconds": {
            "load_parquet": load_seconds,
            "load_cache_and_taxonomies": cache_seconds,
            "select_products": selection_seconds,
            "process_products": process_seconds,
            "write_review_outputs": time.perf_counter() - write_start,
        },
        "selection": selection,
    }
    _write_json(destination / "pilot_manifest.json", manifest)
    return {"manifest": manifest, "results": results, "research_queue": list(queue.values()), "new_terms": list(terms.values())}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the 10-product review pilot using only Parquet and cache")
    parser.add_argument("--input", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--products", nargs="+")
    args = parser.parse_args()
    result = run_pilot(args.input, args.data_dir, args.output_dir, args.products)
    print(json.dumps({"manifest": result["manifest"], "research_queue_count": len(result["research_queue"]), "new_terms_count": len(result["new_terms"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
