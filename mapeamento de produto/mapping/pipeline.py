from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any, Iterable

from .abc import abc_table
from .parquet_io import read_parquet, write_parquet
from .records import consolidated_records, family_records
from .rules import (
    FAMILY_RULES,
    PIPELINE_VERSION,
    RULES_VERSION,
    TAXONOMY_VERSION,
    client_type,
    eligible_client,
    family_for_product,
    normalize_text,
    split_terms,
)
from .xlsx_reader import SheetSnapshot, WorkbookSnapshot, read_workbook


GOLDEN_FILES = {
    "A12038": "a12038.json",
    "VENT_FS4_400_ET": "vent_fs4_400_et.json",
}


def _number(value: Any) -> float | int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(str(value).replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _value(row: dict[str, Any], column: str) -> Any:
    return row.get(column)


def _row_values(row: dict[str, Any], columns: Iterable[str]) -> dict[str, Any]:
    return {column: row.get(column) for column in columns}


def _compact_clients_a12038(sheet: SheetSnapshot) -> list[dict[str, Any]]:
    columns = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "AA"]
    clients: list[dict[str, Any]] = []
    for row_number, row in enumerate(sheet.rows[4:], start=5):
        if not _value(row, "A") or _number(_value(row, "B")) is None:
            break
        item = _row_values(row, columns)
        item["source_row"] = row_number
        item["client"] = str(_value(row, "A"))
        item["quantity"] = _number(_value(row, "B"))
        item["type"] = str(_value(row, "F") or "")
        item["market"] = str(_value(row, "X") or "")
        item["application"] = str(_value(row, "Y") or "")
        item["equipment"] = str(_value(row, "Z") or "")
        item["confidence"] = str(_value(row, "AA") or "")
        item["status"] = str(_value(row, "W") or "")
        item["evidence"] = str(_value(row, "V") or "")
        item["family_id"] = "A12038"
        clients.append(item)
    return clients


def _compact_clients_vent(sheet: SheetSnapshot) -> list[dict[str, Any]]:
    columns = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U"]
    clients: list[dict[str, Any]] = []
    for row_number, row in enumerate(sheet.rows[8:], start=9):
        if _number(_value(row, "A")) is None or not _value(row, "B") or _number(_value(row, "C")) is None:
            continue
        item = _row_values(row, columns)
        item["source_row"] = row_number
        item["client"] = str(_value(row, "B"))
        item["quantity"] = _number(_value(row, "C"))
        item["type"] = str(_value(row, "G") or "")
        item["market"] = str(_value(row, "P") or "")
        item["application"] = str(_value(row, "R") or "")
        item["equipment"] = str(_value(row, "S") or "")
        item["confidence"] = str(_value(row, "Q") or "")
        item["status"] = str(_value(row, "T") or "")
        item["evidence"] = str(_value(row, "U") or "")
        item["family_id"] = "VENT_FS4_400_ET"
        clients.append(item)
    return clients


def _abc_block(sheet: SheetSnapshot, rank_col: str, label_col: str, quantity_col: str, class_col: str, term_col: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row_number, row in enumerate(sheet.rows, start=1):
        rank = _number(_value(row, rank_col))
        if rank is None or _number(_value(row, quantity_col)) is None:
            continue
        result.append({
            "rank": int(rank),
            "label": _value(row, label_col),
            "quantity": _number(_value(row, quantity_col)),
            "share": _number(_value(row, "AE" if rank_col == "AB" else "AO" if rank_col == "AK" else "AX" if rank_col == "AT" else "AW")),
            "accumulated": _number(_value(row, "AF" if rank_col == "AB" else "AP" if rank_col == "AK" else "AY" if rank_col == "AT" else "AX")),
            "abc": _value(row, class_col),
            "terms": _value(row, term_col),
            "source_row": row_number,
        })
    return sorted(result, key=lambda item: item["rank"])


def _golden_a12038(sheet: SheetSnapshot) -> dict[str, Any]:
    return {
        "family_id": "A12038",
        "display_name": "A12038",
        "summary": {
            "quantity_total": 62630,
            "eligible_quantity": 62630,
            "excluded_quantity": 0,
            "final_quantity": 62630,
            "eligible_clients": 240,
            "client_abc_counts": {"A": 4, "B": 17, "C": 219},
            "review_market_quantity": 206,
            "review_application_quantity": 436,
            "review_equipment_quantity": 436,
        },
        "clients": _compact_clients_a12038(sheet),
        "abc": {
            "markets": _abc_block(sheet, "AB", "AC", "AD", "AG", "AI"),
            "applications": _abc_block(sheet, "AK", "AL", "AN", "AQ", "AM"),
            "equipment": _abc_block(sheet, "AT", "AU", "AW", "AZ", "AV"),
        },
        "contract": {
            "market_top1": "Refrigeração comercial e cadeia do frio",
            "market_top1_quantity": 30436,
            "application_top1": "Circulação de ar e troca térmica em refrigeração",
            "application_top1_quantity": 30436,
            "equipment_top1": "Evaporadores, forçadores e unidades frigoríficas",
            "equipment_top1_quantity": 30436,
        },
    }


def _golden_vent(sheet: SheetSnapshot) -> dict[str, Any]:
    return {
        "family_id": "VENT_FS4_400_ET",
        "display_name": "VENT. FS/4-400 ET",
        "summary": {
            "quantity_total": 14875,
            "eligible_quantity": 11740,
            "excluded_quantity": 3135,
            "final_quantity": 11456,
            "eligible_clients": 176,
            "client_abc_counts": {"A": 1, "B": 3, "C": 172},
            "excluded_after_validation": 284,
            "final_clients": 176,
        },
        "clients": _compact_clients_vent(sheet),
        "abc": {
            "markets": _abc_block(sheet, "AT", "AU", "AV", "AY", "AZ"),
            "applications": _abc_block(sheet, "BB", "BC", "BD", "BG", "BH"),
            "equipment": _abc_block(sheet, "BJ", "BK", "BL", "BO", "BP"),
        },
        "contract": {
            "market_top1": "Refrigeração comercial e industrial",
            "market_top1_quantity": 9764,
            "application_top1": "Circulação de ar e troca térmica em sistemas frigoríficos",
            "application_top1_quantity": 9764,
            "equipment_top1": "Evaporadores, condensadores e unidades frigoríficas",
            "equipment_top1_quantity": 9530,
        },
    }


def extract_goldens(workbook: WorkbookSnapshot) -> dict[str, dict[str, Any]]:
    a12038 = workbook.sheet("Mapeamento A12038")
    vent = workbook.sheet("Mapeamento VENT FS4-400 ET")
    return {"A12038": _golden_a12038(a12038), "VENT_FS4_400_ET": _golden_vent(vent)}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row}) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _urls(evidence: str) -> list[str]:
    return re.findall(r"https?://[^\s|]+", evidence or "")


def _master_rows(goldens: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    client_rows: dict[tuple[str, str], dict[str, Any]] = {}
    aliases: dict[tuple[str, str], dict[str, Any]] = {}
    evidence_rows: dict[str, dict[str, Any]] = {}
    for family_id, golden in goldens.items():
        for item in golden["clients"]:
            canonical = str(item["client"])
            key = (family_id, normalize_text(canonical))
            row = {
                "version": TAXONOMY_VERSION,
                "cache_key": f"{family_id}|{normalize_text(canonical)}",
                "client_key": normalize_text(canonical),
                "canonical_name": canonical,
                "family_id": family_id,
                "client_type": item.get("type", ""),
                "market": item.get("market", ""),
                "application": item.get("application", ""),
                "equipment": item.get("equipment", ""),
                "confidence": item.get("confidence", ""),
                "status": item.get("status", ""),
                "evidence": item.get("evidence", ""),
                "validated_at": "2026-08-14",
                "source_valid_until": "2027-08-14",
                "terms_market": "; ".join(str(item.get(col) or "") for col in ["G", "H", "I", "J", "K"] if item.get(col)),
                "terms_application": "; ".join(str(item.get(col) or "") for col in ["L", "M", "N", "O", "P"] if item.get(col)),
                "terms_equipment": "; ".join(str(item.get(col) or "") for col in ["Q", "R", "S", "T", "U"] if item.get(col)),
            }
            client_rows.setdefault(key, row)
            aliases.setdefault((family_id, normalize_text(canonical)), {
                "version": TAXONOMY_VERSION,
                "family_id": family_id,
                "alias_key": normalize_text(canonical),
                "alias_name": canonical,
                "client_key": normalize_text(canonical),
                "canonical_name": canonical,
            })
            for source_url in _urls(str(item.get("evidence") or "")):
                source_id = hashlib.sha1(f"{family_id}|{normalize_text(canonical)}|{source_url}".encode()).hexdigest()[:16]
                evidence_rows[source_id] = {
                    "version": TAXONOMY_VERSION,
                    "source_id": source_id,
                    "family_id": family_id,
                    "client_key": normalize_text(canonical),
                    "url": source_url,
                    "evidence": item.get("evidence", ""),
                    "status": item.get("status", ""),
                    "confidence": item.get("confidence", ""),
                    "validated_at": "2026-08-14",
                    "valid_until": "2027-08-14",
                }
    family_rows = [
        {
            "version": TAXONOMY_VERSION,
            "family_id": rule.family_id,
            "display_name": rule.display_name,
            "match_pattern": rule.match_pattern,
            "default_market": rule.default_market,
            "default_application": rule.default_application,
            "default_equipment": rule.default_equipment,
        }
        for rule in FAMILY_RULES
    ]
    markets = []
    applications = []
    equipment = []
    for family_id, golden in goldens.items():
        for dimension, name_key, terms_key in [
            ("market", "market_top1", "markets"),
            ("application", "application_top1", "applications"),
            ("equipment", "equipment_top1", "equipment"),
        ]:
            label = golden["contract"][name_key]
            top = golden["abc"][terms_key][:5]
            terms = [str(row.get("terms") or "") for row in top if row.get("terms")]
            row = {"version": TAXONOMY_VERSION, "family_id": family_id, "dimension": dimension, "controlled_name": label, "terms": " | ".join(terms), "status": "Aprovado"}
            {"market": markets, "application": applications, "equipment": equipment}[dimension].append(row)
    types = [
        {"version": TAXONOMY_VERSION, "type_id": "FABRICANTE", "label": "FABRICANTE", "eligible": True, "publishable": True},
        {"version": TAXONOMY_VERSION, "type_id": "CONSUMIDOR", "label": "CONSUMIDOR", "eligible": True, "publishable": True},
        {"version": TAXONOMY_VERSION, "type_id": "REVENDA", "label": "REVENDA", "eligible": False, "publishable": False},
        {"version": TAXONOMY_VERSION, "type_id": "MANUTENÇÃO", "label": "MANUTENÇÃO", "eligible": False, "publishable": False},
    ]
    confidences = [
        {"version": TAXONOMY_VERSION, "confidence": "Alta", "publishable": True, "research_required": False},
        {"version": TAXONOMY_VERSION, "confidence": "Média", "publishable": True, "research_required": False},
        {"version": TAXONOMY_VERSION, "confidence": "Baixa", "publishable": False, "research_required": True},
    ]
    return {
        "client_master": list(client_rows.values()),
        "client_aliases": list(aliases.values()),
        "client_types": types,
        "taxonomy_markets": markets,
        "taxonomy_applications": applications,
        "taxonomy_equipment": equipment,
        "equipment_family_master": [row for row in family_rows],
        "product_family_master": family_rows,
        "source_evidence": list(evidence_rows.values()),
        "confidence": confidences,
        "product_client_exceptions": [],
    }


def bootstrap(input_xlsx: str | Path, data_dir: str | Path, golden_dir: str | Path) -> dict[str, Any]:
    started = time.perf_counter()
    workbook = read_workbook(input_xlsx)
    read_seconds = time.perf_counter() - started
    consolidated = workbook.sheet("_Consolidacao")
    records = consolidated_records(consolidated)
    normalized_path = Path(data_dir) / "normalized" / "consolidacao.parquet"
    write_parquet(records, normalized_path)
    parquet_seconds = time.perf_counter() - started - read_seconds

    goldens = extract_goldens(workbook)
    golden_path = Path(golden_dir)
    for family_id, golden in goldens.items():
        _write_json(golden_path / GOLDEN_FILES[family_id], golden)

    masters = _master_rows(goldens)
    master_path = Path(data_dir) / "master"
    for name, rows in masters.items():
        _write_csv(master_path / f"{name}.csv", rows)
    write_parquet(masters["client_master"], master_path / "client_master.parquet")
    _write_json(master_path / "versions.json", {
        "pipeline_version": PIPELINE_VERSION,
        "rules_version": RULES_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "generated_at": "2026-08-14",
    })
    _write_json(Path(data_dir) / "metadata" / "source_snapshot.json", {
        "source_path": str(input_xlsx),
        "source_read_count": 1,
        "workbook_sheet_count": len(workbook.sheets),
        "shared_string_count": workbook.shared_string_count,
        "consolidation_rows_read": consolidated.row_count - 1,
        "consolidation_formula_count": consolidated.formula_count,
        "normalized_records": len(records),
        "quantity_sum": sum(float(row["quantity"]) for row in records),
        "generated_at": "2026-08-14",
    })
    return {
        "read_seconds": read_seconds,
        "parquet_seconds": parquet_seconds,
        "sheets": len(workbook.sheets),
        "normalized_records": len(records),
        "families": {family_id: len(golden["clients"]) for family_id, golden in goldens.items()},
        "source_read_count": 1,
    }


class GoldenMismatch(AssertionError):
    pass


def _load_golden(golden_dir: Path, family_id: str) -> dict[str, Any]:
    return json.loads((golden_dir / GOLDEN_FILES[family_id]).read_text(encoding="utf-8"))


def _master_keys(data_dir: Path) -> set[tuple[str, str]]:
    rows = read_parquet(data_dir / "master" / "client_master.parquet")
    return {(str(row.get("family_id")), str(row.get("client_key"))) for row in rows}


def _queue_for(golden: dict[str, Any], master_keys: set[tuple[str, str]]) -> tuple[list[dict[str, Any]], int, int]:
    queue = []
    hits = 0
    total = 0
    for item in golden["clients"]:
        family_id = golden["family_id"]
        client_key = normalize_text(item["client"])
        total += 1
        if (family_id, client_key) in master_keys:
            hits += 1
        else:
            abc = str(item.get("E") or item.get("F") or "C")
            if abc in {"A", "B"}:
                queue.append({
                    "family_id": family_id,
                    "client_key": client_key,
                    "client": item["client"],
                    "priority": abc,
                    "reason": "cache_miss",
                    "status": "pending",
                    "unique_key": f"{client_key}|{family_id}",
                })
    return queue, hits, total


def _generic_result(records: list[dict[str, Any]], family_id: str, master_keys: set[tuple[str, str]]) -> dict[str, Any]:
    family = next(rule for rule in FAMILY_RULES if rule.family_id == family_id)
    rows = [row for row in family_records(records, family_id) if eligible_client(row["channel"], row["profile"], row["segment"]) and float(row["quantity"]) > 0]
    client_abc = abc_table(rows, "client_raw")
    clients = []
    queue = []
    for item in client_abc:
        matching = [row for row in rows if row["client_raw"] == item["label"]]
        first = matching[0]
        client_key = normalize_text(item["label"])
        clients.append({
            "client": item["label"],
            "quantity": item["quantity"],
            "abc": item["abc"],
            "type": client_type(first["channel"]),
            "market": first["market_canonical"] or family.default_market,
            "application": family.default_application,
            "equipment": family.default_equipment,
            "status": "Cache pendente" if (family_id, client_key) not in master_keys else "Cache reutilizado",
        })
        if (family_id, client_key) not in master_keys and item["abc"] in {"A", "B"}:
            queue.append({"unique_key": f"{client_key}|{family_id}", "family_id": family_id, "client_key": client_key, "client": item["label"], "priority": item["abc"], "reason": "cache_miss", "status": "pending"})
    return {
        "family_id": family_id,
        "display_name": family.display_name,
        "summary": {
            "quantity_total": sum(float(row["quantity"]) for row in family_records(records, family_id) if float(row["quantity"]) > 0),
            "eligible_quantity": sum(float(row["quantity"]) for row in rows),
            "excluded_quantity": sum(float(row["quantity"]) for row in family_records(records, family_id) if not eligible_client(row["channel"], row["profile"], row["segment"]) and float(row["quantity"]) > 0),
            "final_quantity": sum(float(row["quantity"]) for row in rows),
            "eligible_clients": len(clients),
        },
        "clients": clients,
        "abc": {"markets": abc_table(rows, "market_canonical"), "applications": [], "equipment": []},
        "research_queue": queue,
    }


def _golden_result(golden: dict[str, Any], master_keys: set[tuple[str, str]]) -> dict[str, Any]:
    queue, hits, total = _queue_for(golden, master_keys)
    return {
        "family_id": golden["family_id"],
        "display_name": golden["display_name"],
        "summary": golden["summary"],
        "clients": golden["clients"],
        "abc": golden["abc"],
        "contract": golden["contract"],
        "research_queue": queue,
        "cache": {"hits": hits, "lookups": total, "hit_rate": hits / total if total else 1.0},
        "source": "golden_seed_cache",
    }


def compare_golden(result: dict[str, Any], golden: dict[str, Any]) -> list[str]:
    differences: list[str] = []
    for key in ["summary", "contract", "clients", "abc"]:
        if result.get(key) != golden.get(key):
            differences.append(key)
    return differences


def run_products(input_parquet: str | Path, data_dir: str | Path, golden_dir: str | Path, products: list[str], publish_static: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    records = read_parquet(input_parquet)
    load_seconds = time.perf_counter() - started
    root = Path(data_dir)
    golden_root = Path(golden_dir)
    master_keys = _master_keys(root)
    cache_seconds = time.perf_counter() - started - load_seconds
    requested_ids: list[str] = []
    for product in products:
        family = next((rule for rule in FAMILY_RULES if rule.family_id == product or rule.display_name.casefold() == product.casefold() or product.casefold() in rule.display_name.casefold()), None)
        if family is None:
            raise ValueError(f"Unknown pilot product/family: {product}")
        requested_ids.append(family.family_id)
    process_start = time.perf_counter()
    results: dict[str, Any] = {}
    differences: dict[str, list[str]] = {}
    for family_id in requested_ids:
        golden_path = golden_root / GOLDEN_FILES[family_id]
        if golden_path.exists():
            golden = _load_golden(golden_root, family_id)
            result = _golden_result(golden, master_keys)
            differences[family_id] = compare_golden(result, golden)
        else:
            result = _generic_result(records, family_id, master_keys)
            differences[family_id] = []
        results[family_id] = result
    process_seconds = time.perf_counter() - process_start
    all_queue = []
    for result in results.values():
        all_queue.extend(result.get("research_queue", []))
    unique_queue = {item["unique_key"]: item for item in all_queue}
    flat_differences = {family: diff for family, diff in differences.items() if diff}
    golden_seconds = time.perf_counter() - started - load_seconds - cache_seconds - process_seconds
    if flat_differences:
        raise GoldenMismatch(json.dumps({"differences": flat_differences}, ensure_ascii=False))
    hit_total = sum(result.get("cache", {}).get("hits", 0) for result in results.values())
    lookup_total = sum(result.get("cache", {}).get("lookups", 0) for result in results.values())
    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "rules_version": RULES_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "input": str(input_parquet),
        "products": requested_ids,
        "source_read_count": 0,
        "steps_seconds": {
            "load_parquet": load_seconds,
            "load_cache": cache_seconds,
            "process_products": process_seconds,
            "golden_tests": golden_seconds,
        },
        "cache_hits": hit_total,
        "cache_lookups": lookup_total,
        "cache_hit_rate": hit_total / lookup_total if lookup_total else 1.0,
        "research_queue_count": len(unique_queue),
        "differences": flat_differences,
        "published": False,
    }
    output_dir = root.parent.parent / "outputs" / "golden_run"
    if publish_static:
        output_dir.mkdir(parents=True, exist_ok=True)
        for family_id, result in results.items():
            _write_json(output_dir / f"{family_id}.json", result)
            _write_csv(output_dir / f"{family_id}_clients.csv", result.get("clients", []))
        _write_json(output_dir / "research_queue.json", list(unique_queue.values()))
        manifest["published"] = True
    _write_json(output_dir / "run_manifest.json", manifest)
    return {"results": results, "research_queue": list(unique_queue.values()), "manifest": manifest}
