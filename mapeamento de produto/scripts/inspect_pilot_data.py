"""Inspect what data is available for each pilot product."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

from mapping.parquet_io import read_parquet
from mapping.rules import eligible_client, normalize_text, client_type

ROOT = Path(__file__).resolve().parent.parent

rows = read_parquet(ROOT / "data" / "normalized" / "consolidacao.parquet")

# Load client master cache
master_rows = read_parquet(ROOT / "data" / "master" / "client_master.parquet")
cache: dict[str, dict] = {}
for r in master_rows:
    cache.setdefault(str(r.get("client_key") or ""), r)

PRODUCTS = [
    "VENT. FF/2-146 P 220V",
    "VENT. FS/4-400 EMBT - 230 V",
    "MICROVENTILADOR A17251VBHBL - 110/220V",
    "VENT.FB/2-190MCD- 230V. 50/60",
    "VENT. FS/2-300 EM -  230 V",
    "VENT. FF/2-160 VS- 220V. 60 HZ",
    "VENT. ECM 30 - 50/60HZ",
]

for product in PRODUCTS:
    prod_rows = [r for r in rows if r.get("product") == product and float(r.get("quantity") or 0) > 0]
    eligible = [r for r in prod_rows if eligible_client(r.get("channel"), r.get("profile"), r.get("segment"))]
    
    cached_clients = set()
    for r in eligible:
        key = normalize_text(r.get("client_raw"))
        if cache.get(key):
            cached_clients.add(key)
    
    equip_cols = ["equipment_candidate_1", "equipment_candidate_2", "equipment_candidate_3", "equipment_candidate_4", "equipment_candidate_5"]
    equip_filled = sum(1 for r in eligible if any(r.get(c) for c in equip_cols))
    
    print(f"\n{'='*80}")
    print(f"PRODUTO: {product}")
    print(f"  Elegíveis: {len(eligible)}, Com cache: {len(cached_clients)}, Com equip candidates: {equip_filled}")
    
    # Show 2 cached clients with their terms
    shown = 0
    for r in eligible:
        key = normalize_text(r.get("client_raw"))
        c = cache.get(key)
        if c and shown < 2:
            print(f"\n  [CACHED] {r.get('client_raw', '')[:60]}")
            print(f"    cache.market: {c.get('market', '')}")
            print(f"    cache.application: {c.get('application', '')}")
            print(f"    cache.equipment: {c.get('equipment', '')}")
            print(f"    cache.terms_market: {c.get('terms_market', '')}")
            print(f"    cache.terms_application: {c.get('terms_application', '')}")
            print(f"    cache.terms_equipment: {c.get('terms_equipment', '')}")
            shown += 1
    
    # Show 2 non-cached clients with parquet data
    shown = 0
    for r in eligible:
        key = normalize_text(r.get("client_raw"))
        if not cache.get(key) and shown < 2:
            print(f"\n  [SEM CACHE] {r.get('client_raw', '')[:60]}")
            print(f"    market_canonical: {r.get('market_canonical', '')}")
            print(f"    market_base: {r.get('market_base', '')}")
            print(f"    segment: {r.get('segment', '')}")
            for ec in equip_cols:
                val = r.get(ec, "")
                if val:
                    print(f"    {ec}: {val}")
            shown += 1

    # Show all unique markets and equipments for this product
    markets = Counter()
    equips = Counter()
    for r in eligible:
        qty = float(r.get("quantity") or 0)
        key = normalize_text(r.get("client_raw"))
        c = cache.get(key)
        if c:
            markets[c.get("market", "Revisar")] += qty
            equips[c.get("equipment", "Revisar")] += qty
        else:
            markets[r.get("market_canonical") or r.get("market_base") or "Revisar"] += qty
            equips[r.get("equipment_candidate_1") or "Revisar"] += qty
    
    print(f"\n  Mercados (top 5):")
    for m, q in markets.most_common(5):
        print(f"    {q:.0f}  {m}")
    print(f"\n  Equipamentos (top 5):")
    for e, q in equips.most_common(5):
        print(f"    {q:.0f}  {e}")
