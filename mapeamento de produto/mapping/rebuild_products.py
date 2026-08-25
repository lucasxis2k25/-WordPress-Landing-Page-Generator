"""Rebuild and Sanitize Pilot Products according to Golden Standard Rules.

Enforces:
1. Canonical Macro Markets (Zero duplication/cannibalization).
2. Physical Coherence of Equipment.
3. Strict Golden Standard Markdown & Curva ABC generation.
"""

from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict

import pyarrow.parquet as pq

from mapping.quality_gate import sanitize_client_record
from mapping.rules import eligible_client, client_type, normalize_text
from mapping.export_markdown import generate_exact_product_markdown, _sanitize_filename


REBUILD_PRODUCTS = [
    ("VENT. FF/2-146 P 220V", "CENTRIFUGO/GABINETE"),
    ("VENT. FS/4-400 EMBT - 230 V", "AXIAL"),
    ("CONECTO FF", "ACESSORIOS"),
    ("MICROVENTILADOR A17251VBHBL - 110/220V", "MICROVENTILADOR"),
    ("VENT.FB/2-190MCD- 230V. 50/60", "CENTRIFUGO/TURBINA"),
    ("VENT. FS/2-300 EM -  230 V", "AXIAL"),
    ("VENT. TGH-240 V2- 220V. 60 HZ", "TANGENCIAL"),
    ("VENT. FF/2-160 VS- 220V. 60 HZ", "CENTRIFUGO/GABINETE"),
    ("VENT. ECM 30 - 50/60HZ", "MOTORES"),
    ("PLUS UNIC", "ACESSORIOS"),
]


def rebuild_all_products(data_dir: Path = Path("data"), out_dir: Path = Path("outputs/mapeamento_produtos")):
    parquet_path = data_dir / "normalized" / "consolidacao.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"Missing {parquet_path}")

    df = pq.read_table(parquet_path).to_pandas()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("INICIANDO RECONSTRUÇÃO E SANITIZAÇÃO COM QUALITY GATE")
    print("=" * 70)

    summary_results = []

    for product_name, default_family in REBUILD_PRODUCTS:
        # Match product rows
        prod_df = df[df["product"] == product_name]
        if prod_df.empty:
            # Try fuzzy match if needed
            prod_df = df[df["product"].str.contains(product_name.replace("-", "").replace("/", ""), case=False, na=False)]

        if prod_df.empty:
            print(f"[ALERTA] Nenhum registro encontrado para: {product_name}")
            continue

        # Filter positive and eligible
        pos_df = prod_df[prod_df["quantity"] > 0]
        
        # Aggregate by client
        client_groups = defaultdict(lambda: {
            "quantity": 0.0,
            "channel": "",
            "profile": "",
            "segment": "",
            "market_base": "",
            "tech_family": default_family,
            "raw_equipments": []
        })

        for _, row in pos_df.iterrows():
            ch = str(row.get("channel") or "")
            prof = str(row.get("profile") or "")
            seg = str(row.get("segment") or "")
            
            if not eligible_client(ch, prof, seg):
                continue
                
            cli_raw = str(row.get("client_raw") or "").strip()
            if not cli_raw:
                continue
                
            key = normalize_text(cli_raw)
            grp = client_groups[key]
            grp["client"] = cli_raw
            grp["quantity"] += float(row.get("quantity") or 0.0)
            if not grp["channel"]:
                grp["channel"] = ch
                grp["profile"] = prof
                grp["segment"] = seg
                grp["market_base"] = str(row.get("market_base") or "")
                grp["tech_family"] = str(row.get("technical_family") or default_family)
            for k in ["equipment_candidate_1", "equipment_candidate_2", "equipment_candidate_3"]:
                eq_cand = str(row.get(k) or "").strip()
                if eq_cand and eq_cand not in grp["raw_equipments"]:
                    grp["raw_equipments"].append(eq_cand)

        # Build clean client records with Quality Gate
        clients = []
        for key, grp in client_groups.items():
            cli_name = grp["client"]
            record = sanitize_client_record(
                product_code=product_name,
                tech_family=grp["tech_family"],
                client_name=cli_name,
                quantity=grp["quantity"],
                client_type=client_type(grp["channel"]),
                segment=grp["segment"],
                market_base=grp["market_base"],
                channel=grp["channel"],
            )
            clients.append(record)

        if not clients:
            print(f"[ALERTA] Nenhum cliente elegível para {product_name}")
            continue

        # Sort descending by quantity
        clients.sort(key=lambda x: x["quantity"], reverse=True)
        total_qty = sum(c["quantity"] for c in clients)
        
        # Calculate ABC
        accum = 0.0
        for idx, c in enumerate(clients, 1):
            share = c["quantity"] / total_qty * 100
            accum += share
            if accum - share < 80.0 or idx == 1:
                c["abc"] = "A"
            elif accum - share < 95.0:
                c["abc"] = "B"
            else:
                c["abc"] = "C"

        # Generate Markdown
        md = generate_exact_product_markdown(
            product_name=product_name,
            clients=clients,
            technical_family=default_family
        )

        filename = _sanitize_filename(product_name) + ".md"
        out_file = out_dir / filename
        out_file.write_text(md, encoding="utf-8")

        summary_results.append({
            "product": product_name,
            "family": default_family,
            "total_quantity": total_qty,
            "client_count": len(clients),
            "file": str(out_file.name)
        })
        print(f"[OK] Gerado com sucesso: {filename} ({len(clients)} clientes | {total_qty:,.0f} un)")

    print("=" * 70)
    print(f"CONCLUIDO: {len(summary_results)} produtos sanitizados e recriados!")
    print("=" * 70)


if __name__ == "__main__":
    rebuild_all_products()
