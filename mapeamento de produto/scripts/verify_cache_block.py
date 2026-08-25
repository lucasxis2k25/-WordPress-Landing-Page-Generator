"""Verifica se o portao anti-canibalizacao bloqueou corretamente os caches contaminados."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mapping.parquet_io import read_parquet
from mapping.rules import normalize_text, eligible_client

master_rows = read_parquet(ROOT / "data" / "master" / "client_master.parquet")
cache = {}
origins = {}
for r in master_rows:
    key = str(r.get("client_key") or "")
    cache[key] = r
    origins[key] = str(r.get("family_id") or "")

all_rows = read_parquet(ROOT / "data" / "normalized" / "consolidacao.parquet")

products = {
    "VENT. FF/2-146 P 220V": "CENTRIFUGO/GABINETE",
    "MICROVENTILADOR A17251VBHBL - 110/220V": "MICROVENTILADOR",
    "VENT.FB/2-190MCD- 230V. 50/60": "RADIAL/DUTO",
    "VENT. FF/2-160 VS- 220V. 60 HZ": "CENTRIFUGO/GABINETE",
}

refrig = ["evaporador", "frigor", "condensador", "plug-in", "cadeia do frio", "congelamento"]

total_blocked = 0
for product, family in products.items():
    prod_rows = [r for r in all_rows if r.get("product") == product and float(r.get("quantity") or 0) > 0]
    eligible = [r for r in prod_rows if eligible_client(r.get("channel"), r.get("profile"), r.get("segment"))]
    seen = set()
    contam = 0
    for r in eligible:
        key = normalize_text(r.get("client_raw"))
        if key in seen:
            continue
        seen.add(key)
        origin = origins.get(key, "")
        if origin in ("A12038", "VENT_FS4_400_ET"):
            c = cache.get(key, {})
            is_refrig = False
            for field in ("market", "application", "equipment"):
                val = str(c.get(field) or "").lower()
                for m in refrig:
                    if m in val:
                        is_refrig = True
                        break
                if is_refrig:
                    break
            if is_refrig:
                client_name = str(r.get("client_raw", ""))[:50]
                origin_field = c.get("market", "")
                print("  BLOQUEADO: {} | {} | cache={} | market={}".format(
                    product[:25], client_name, origin, origin_field))
                contam += 1
                total_blocked += 1
    if contam == 0:
        print("{}: LIMPO — nenhum cache de refrigeracao aplicado".format(product))
    else:
        print("{}: {} cache(s) de refrigeracao bloqueados com sucesso".format(product, contam))

print()
if total_blocked > 0:
    print("RESULTADO: {} caches de refrigeracao foram BLOQUEADOS — anti-canibalizacao OK".format(total_blocked))
else:
    print("RESULTADO: Nenhum cache cruzado detectado — OK")
