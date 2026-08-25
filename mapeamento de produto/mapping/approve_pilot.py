from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from mapping.abc import abc_table
from mapping.rules import normalize_text


APPROVAL_VERSION = "pilot-approval-2026-08-14"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row}) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _merge_rows(existing: list[dict[str, Any]], additions: list[dict[str, Any]], key_fields: list[str]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in existing + additions:
        key = tuple(str(row.get(field) or "") for field in key_fields)
        merged[key] = row
    return list(merged.values())


def _approval_registry(terms: list[dict[str, Any]], existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    additions = []
    for item in terms:
        term = str(item.get("term") or "")
        additions.append({
            "version": APPROVAL_VERSION,
            "approval_status": "Aprovado",
            "approved_at": "2026-08-14",
            "approval_source": "Aprovação do usuário no piloto de 10 produtos",
            "product": item.get("product", ""),
            "technical_family": item.get("technical_family", ""),
            "dimension": item.get("dimension", ""),
            "term": term,
            "data_quality_flag": "caractere de substituição U+FFFD presente" if "\ufffd" in term else "",
        })
    return _merge_rows(existing, additions, ["product", "technical_family", "dimension", "term"])


def _family_cache(results: list[dict[str, Any]], existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    additions: list[dict[str, Any]] = []
    for result in results:
        for client in result.get("clients", []):
            if not client.get("cache_customer_reused"):
                continue
            client_key = normalize_text(client.get("client"))
            family = str(result.get("technical_family") or "")
            additions.append({
                "version": APPROVAL_VERSION,
                "cache_key": f"{client_key}|{family}",
                "client_key": client_key,
                "canonical_name": client.get("client", ""),
                "technical_family": family,
                "client_type": client.get("type", ""),
                "market": client.get("market", ""),
                "application": client.get("application", ""),
                "equipment": client.get("equipment", ""),
                "confidence": client.get("confidence", ""),
                "status": "Aprovado — cache mestre reutilizado; família aprovada",
                "evidence": "Cache mestre existente; aprovação do piloto; sem nova pesquisa",
                "validated_at": "2026-08-14",
                "source_valid_until": "2027-08-14",
            })
    return _merge_rows(existing, additions, ["cache_key"])


def _publicable_abc(clients: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows = [{"client": row["client"], "market": row["market"], "application": row["application"], "equipment": row["equipment"], "quantity": row["quantity"]} for row in clients]
    return {
        "clients": abc_table(rows, "client"),
        "markets": abc_table(rows, "market"),
        "applications": abc_table(rows, "application"),
        "equipment": abc_table(rows, "equipment"),
    }


def approve(input_dir: str | Path, data_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    source = Path(input_dir)
    master = Path(data_dir) / "master"
    destination = Path(output_dir)
    results = _read_json(source / "pilot_results.json")
    terms = _read_json(source / "new_terms_for_approval.json")

    approved_registry = _approval_registry(terms, _read_csv(master / "approval_registry.csv"))
    family_cache = _family_cache(results, _read_csv(master / "client_family_cache.csv"))
    _write_csv(master / "approval_registry.csv", approved_registry)
    _write_csv(master / "client_family_cache.csv", family_cache)

    approved_results: list[dict[str, Any]] = []
    publicable_client_rows: list[dict[str, Any]] = []
    review_client_rows: list[dict[str, Any]] = []
    approved_queue: dict[str, dict[str, Any]] = {}
    for result in results:
        copied = json.loads(json.dumps(result, ensure_ascii=False))
        publicable = []
        review = []
        for client in copied.get("clients", []):
            client["family_approval_status"] = "Aprovado"
            client["publishable"] = bool(client.get("cache_customer_reused"))
            if client["publishable"]:
                client["status"] = "Comprovado — cache reutilizado; família aprovada"
                publicable.append(client)
                publicable_client_rows.append({"product": copied["product"], "technical_family": copied["technical_family"], **client})
            else:
                client["status"] = "Revisar — cliente sem cache"
                review.append(client)
                review_client_rows.append({"product": copied["product"], "technical_family": copied["technical_family"], **client})
        copied["approval"] = {
            "version": APPROVAL_VERSION,
            "status": "Aprovado",
            "approved_at": "2026-08-14",
            "scope": "família técnica e termos; clientes sem cache permanecem em revisão",
        }
        copied["publicable_clients"] = publicable
        copied["review_clients"] = review
        copied["abc_publicable"] = _publicable_abc(publicable)
        copied["summary"]["quantity_publicable"] = sum(float(row.get("quantity") or 0) for row in publicable)
        copied["summary"]["quantity_under_review"] = sum(float(row.get("quantity") or 0) for row in review)
        copied["summary"]["publicable_clients"] = len(publicable)
        copied["summary"]["review_clients"] = len(review)
        copied["differences"]["new_technical_family"] = False
        copied["differences"]["technical_family_requires_approval"] = False
        copied["differences"]["not_publicable_until_approval"] = False
        copied["differences"]["approval_status"] = "Aprovado"
        copied["new_terms_for_approval"] = {
            dimension: [{"term": term, "status": "Aprovado"} for term in values]
            for dimension, values in copied.get("new_terms_for_approval", {}).items()
        }
        copied["research_queue"] = [item for item in copied.get("research_queue", []) if item.get("reason") == "cache_miss"]
        for item in copied["research_queue"]:
            approved_queue[item["unique_key"]] = item
        approved_results.append(copied)

    approved_terms = [{**term, "status": "Aprovado"} for term in terms]
    _write_json(destination / "pilot_results_aprovado.json", approved_results)
    _write_json(destination / "approved_terms.json", approved_terms)
    _write_json(destination / "research_queue.json", list(approved_queue.values()))
    _write_json(destination / "publicable_clients.json", publicable_client_rows)
    _write_json(destination / "review_clients.json", review_client_rows)
    _write_json(destination / "differences.json", [{"product": result["product"], **result["differences"]} for result in approved_results])
    flat_clients = publicable_client_rows + review_client_rows
    manifest = {
        "pilot": "pilot_10",
        "approval_version": APPROVAL_VERSION,
        "approval_status": "Aprovado",
        "products_processed": len(approved_results),
        "source_read_count": 0,
        "external_research_executed": False,
        "cache_customer_hits": len(publicable_client_rows),
        "cache_customer_lookups": len(flat_clients),
        "cache_customer_hit_rate": len(publicable_client_rows) / len(flat_clients) if flat_clients else 1.0,
        "technical_family_cache_entries": len(family_cache),
        "approved_terms": len(approved_terms),
        "publicable_client_rows": len(publicable_client_rows),
        "review_client_rows": len(review_client_rows),
        "research_queue_count": len(approved_queue),
        "research_queue_reasons": {"cache_miss": len(approved_queue)},
        "published": True,
        "publication_scope": "static pilot output; only cached clients are publicable",
        "review_rows_included": True,
    }
    _write_json(destination / "pilot_manifest_aprovado.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply explicit approval to the 10-product pilot and publish static outputs")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(approve(args.input_dir, args.data_dir, args.output_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
