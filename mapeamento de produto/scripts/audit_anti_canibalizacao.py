"""Auditoria Anti-Canibalizacao e Coerencia Fisica.

Verifica que nenhum produto herdou mercados/aplicacoes/equipamentos
de outro produto via cache contaminado.

Regras verificadas:
1. Cache do A12038 / VENT FS4-400 ET NAO pode vazar para microventiladores,
   centrifugos ou radiais sem validacao especifica.
2. Equipamentos devem ser fisicamente compativeis com o porte do produto.
3. Mercados nao podem ser fragmentados artificialmente.
4. Termos de uma familia nao podem aparecer em outra sem evidencia.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mapping.parquet_io import read_parquet
from mapping.rules import eligible_client, normalize_text

# Carregar dados
all_rows = read_parquet(ROOT / "data" / "normalized" / "consolidacao.parquet")
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
]

# Mapear de qual familia golden cada cliente veio no cache
cache_origin: dict[str, str] = {}
for r in master_rows:
    key = str(r.get("client_key") or "")
    fam = str(r.get("family_id") or "")
    if key and fam:
        cache_origin[key] = fam

print("=" * 90)
print("AUDITORIA ANTI-CANIBALIZACAO E COERENCIA FISICA")
print("=" * 90)

issues: list[dict] = []
clean_count = 0
contaminated_count = 0

for product in PRODUCTS:
    prod_rows = [r for r in all_rows if r.get("product") == product and float(r.get("quantity") or 0) > 0]
    eligible = [r for r in prod_rows if eligible_client(r.get("channel"), r.get("profile"), r.get("segment"))]
    family = eligible[0].get("technical_family", "") if eligible else ""

    print(f"\n{'─' * 90}")
    print(f"PRODUTO: {product}")
    print(f"FAMILIA TECNICA: {family}")
    print(f"CLIENTES ELEGIVEIS: {len(eligible)}")

    # Identificar clientes unicos
    clients_seen: dict[str, dict] = {}
    for r in eligible:
        key = normalize_text(r.get("client_raw"))
        if key not in clients_seen:
            clients_seen[key] = r

    cache_hits = 0
    contaminated_clients = []
    clean_clients = []

    for key, r in clients_seen.items():
        cached = cache.get(key)
        if not cached:
            continue
        cache_hits += 1

        origin = cache_origin.get(key, "desconhecido")
        c_market = cached.get("market", "")
        c_application = cached.get("application", "")
        c_equipment = cached.get("equipment", "")

        # Verificar contaminacao cruzada
        # Se o cache veio de A12038 ou VENT_FS4_400_ET (refrigeracao)
        # e o produto atual NAO e axial de refrigeracao, pode ser contaminacao
        is_refrig_cache = origin in ("A12038", "VENT_FS4_400_ET")
        is_refrig_product = family == "AXIAL"  # Somente AXIAL sao os de refrigeracao

        # Termos de refrigeracao que NAO devem vazar para outras familias
        refrig_markers = [
            "evaporador", "frigor", "condensador", "plug-in",
            "refrigeracao", "cadeia do frio", "forcador",
            "congelamento", "tunnel", "bau"
        ]

        market_contaminated = False
        app_contaminated = False
        equip_contaminated = False

        if is_refrig_cache and not is_refrig_product:
            # Verificar se mercado de refrigeracao vazou
            for marker in refrig_markers:
                if marker in c_market.lower():
                    market_contaminated = True
                if marker in c_application.lower():
                    app_contaminated = True
                if marker in c_equipment.lower():
                    equip_contaminated = True

        # Verificar coerencia fisica: microventilador 172mm nao atua em
        # maquinario pesado, evaporadores grandes, etc.
        if "MICROVENTILADOR" in family or "MICRO" in family:
            heavy_equip = ["evaporador de camara", "tunel de", "unidade condensadora",
                           "bau", "carroceria", "compressor"]
            for he in heavy_equip:
                if he in c_equipment.lower():
                    equip_contaminated = True

        any_issue = market_contaminated or app_contaminated or equip_contaminated

        if any_issue:
            contaminated_clients.append({
                "client": r.get("client_raw", ""),
                "client_key": key,
                "cache_origin": origin,
                "cache_market": c_market,
                "cache_application": c_application,
                "cache_equipment": c_equipment,
                "market_contaminated": market_contaminated,
                "app_contaminated": app_contaminated,
                "equip_contaminated": equip_contaminated,
                "product_segment": r.get("segment", ""),
                "product_market_canonical": r.get("market_canonical", ""),
                "product_equip_1": r.get("equipment_candidate_1", ""),
            })
            contaminated_count += 1
        else:
            clean_clients.append(key)
            clean_count += 1

    print(f"  Cache hits: {cache_hits}")
    print(f"  Clientes LIMPOS (sem contaminacao): {len(clean_clients)}")
    print(f"  Clientes CONTAMINADOS: {len(contaminated_clients)}")

    if contaminated_clients:
        print(f"\n  *** ALERTA DE CANIBALIZACAO ***")
        for cc in contaminated_clients:
            print(f"\n  CLIENTE: {cc['client'][:60]}")
            print(f"    Cache veio de: {cc['cache_origin']}")
            print(f"    Cache mercado: {cc['cache_market']}")
            print(f"    Cache aplicacao: {cc['cache_application']}")
            print(f"    Cache equipamento: {cc['cache_equipment']}")
            print(f"    Segmento REAL do cliente neste produto: {cc['product_segment']}")
            print(f"    Mercado canonico REAL: {cc['product_market_canonical']}")
            print(f"    Equipamento candidate REAL: {cc['product_equip_1']}")
            flags = []
            if cc["market_contaminated"]:
                flags.append("MERCADO CONTAMINADO")
            if cc["app_contaminated"]:
                flags.append("APLICACAO CONTAMINADA")
            if cc["equip_contaminated"]:
                flags.append("EQUIPAMENTO CONTAMINADO")
            print(f"    PROBLEMAS: {', '.join(flags)}")
            issues.append({
                "product": product,
                "family": family,
                **cc,
            })
    else:
        print(f"  OK - Nenhuma contaminacao detectada")

# Verificar tambem se mercados estao fragmentados entre produtos
print(f"\n\n{'=' * 90}")
print("VERIFICACAO DE FRAGMENTACAO DE MERCADOS")
print("=" * 90)

product_markets: dict[str, dict[str, float]] = {}
for product in PRODUCTS:
    prod_rows = [r for r in all_rows if r.get("product") == product and float(r.get("quantity") or 0) > 0]
    eligible = [r for r in prod_rows if eligible_client(r.get("channel"), r.get("profile"), r.get("segment"))]
    markets: dict[str, float] = defaultdict(float)
    for r in eligible:
        key = normalize_text(r.get("client_raw"))
        c = cache.get(key)
        if c and c.get("market"):
            m = c["market"]
        else:
            m = r.get("market_canonical") or r.get("market_base") or "Revisar"
        qty = float(r.get("quantity") or 0)
        markets[m] += qty
    product_markets[product] = dict(markets)

# Imprimir matriz de mercados por produto
all_markets = sorted({m for ms in product_markets.values() for m in ms})
print(f"\nMercados unicos encontrados: {len(all_markets)}")
for m in all_markets:
    prods_using = [(p, q) for p, ms in product_markets.items() if (q := ms.get(m, 0)) > 0]
    if len(prods_using) > 1:
        print(f"\n  MERCADO COMPARTILHADO: {m}")
        for p, q in prods_using:
            fam = next((r.get("technical_family") for r in all_rows if r.get("product") == p), "")
            print(f"    {p} ({fam}): {q:.0f} unidades")

print(f"\n\n{'=' * 90}")
print("RESUMO FINAL")
print("=" * 90)
print(f"  Clientes com cache limpo: {clean_count}")
print(f"  Clientes com contaminacao detectada: {contaminated_count}")
print(f"  Total de problemas: {len(issues)}")

if issues:
    print(f"\n  RESULTADO: *** FALHA *** - Ha {len(issues)} contaminacoes que precisam ser corrigidas")
    # Salvar issues
    output = ROOT / "outputs" / "auditoria_anti_canibalizacao.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(issues, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"  Detalhes salvos em: {output}")
else:
    print(f"\n  RESULTADO: OK - Nenhuma contaminacao cruzada detectada")
