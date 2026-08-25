from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from mapping.product_profiles import profile_for_product
from mapping.quality_gate import sanitize_client_record


def _sanitize_filename(name: str) -> str:
    valid_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    cleaned = "".join(c if c in valid_chars else "_" for c in name)
    return cleaned.strip().replace(" ", "_")


def _fmt_int(value: float | int | None) -> str:
    if value is None:
        return "0"
    return f"{int(round(float(value))):,}".replace(",", ".")


def _fmt_pct(value: float | int | None) -> str:
    if value is None:
        return "0,0%"
    return f"{float(value):.1f}%".replace(".", ",")


def _compute_dimension_table(clients: list[dict[str, Any]], dimension_key: str, term_keys: list[str]) -> list[dict[str, Any]]:
    grouped_qty: dict[str, float] = defaultdict(float)
    grouped_clients: dict[str, set[str]] = defaultdict(set)
    grouped_terms: dict[str, list[str]] = defaultdict(list)

    for c in clients:
        label = str(c.get(dimension_key) or "").strip()
        if not label:
            label = "Não comprovado — revisar"
        qty = float(c.get("quantity") or 0.0)
        cli_name = str(c.get("client") or c.get("B") or "")
        
        grouped_qty[label] += qty
        if cli_name:
            grouped_clients[label].add(cli_name)

        # Collect terms
        for tk in term_keys:
            raw_val = str(c.get(tk) or "").strip()
            if raw_val:
                for sub in raw_val.split(";"):
                    sub = sub.strip()
                    if sub and sub != label and not sub.startswith("http") and not sub.startswith("Base interna"):
                        grouped_terms[label].append(sub)

    total_qty = sum(grouped_qty.values())
    if total_qty == 0:
        return []

    # Sort descending by quantity
    sorted_items = sorted(grouped_qty.items(), key=lambda x: x[1], reverse=True)
    rows = []
    accum = 0.0

    for rank, (label, qty) in enumerate(sorted_items, 1):
        share = qty / total_qty
        accum += share
        
        # ABC class
        if accum - share < 0.80 or rank == 1:
            abc_class = "A"
        elif accum - share < 0.95:
            abc_class = "B"
        else:
            abc_class = "C"

        # Top 5 terms
        term_counts = Counter(grouped_terms[label])
        top5 = [t for t, _ in term_counts.most_common(5)]
        top5_str = "; ".join(top5) if top5 else label

        rows.append({
            "rank": rank,
            "label": label,
            "quantity": qty,
            "share": share * 100,
            "accumulated": min(accum * 100, 100.0),
            "abc": abc_class,
            "client_count": len(grouped_clients[label]),
            "terms": top5_str
        })

    return rows


def _sanitize_clients_for_product(
    product_name: str,
    clients: list[dict[str, Any]],
    technical_family: str,
) -> list[dict[str, Any]]:
    """Reaplica o perfil fechado do produto — evita mistura de aplicações entre SKUs."""
    sanitized: list[dict[str, Any]] = []
    for c in clients:
        cli_name = str(c.get("client") or c.get("A") or "").strip()
        if not cli_name:
            continue
        qty = float(c.get("quantity") or c.get("B") or 0.0)
        ctype = str(c.get("type") or c.get("F") or c.get("G") or "FABRICANTE")
        record = sanitize_client_record(
            product_code=product_name,
            tech_family=technical_family or str(c.get("technical_family") or ""),
            client_name=cli_name,
            quantity=qty,
            client_type=ctype,
            segment=str(c.get("segment") or ""),
            market_base="",
            channel=str(c.get("channel") or ctype),
        )
        if c.get("abc"):
            record["abc"] = c["abc"]
        sanitized.append(record)
    sanitized.sort(key=lambda x: float(x.get("quantity") or 0.0), reverse=True)
    return sanitized


def generate_exact_product_markdown(
    product_name: str,
    clients: list[dict[str, Any]],
    technical_family: str = "",
    precomputed_abc: dict[str, list[dict[str, Any]]] | None = None,
    skip_sanitize: bool = False,
) -> str:
    profile = profile_for_product(product_name, technical_family)
    if not skip_sanitize and product_name not in {"A12038", "VENT. FS/4-400 ET"}:
        clients = _sanitize_clients_for_product(product_name, clients, technical_family)
        # Não herdar market/application/equipment do cache legado de outro produto
        for c in clients:
            c.pop("market_base", None)

    total_qty = sum(float(c.get("quantity") or c.get("B") or 0.0) for c in clients)
    
    # Calculate tables dynamically with running accumulated %
    if precomputed_abc and "markets" in precomputed_abc:
        markets_table = []
        accum = 0.0
        for r in precomputed_abc["markets"]:
            label = r.get("label", "")
            qty = float(r.get("quantity", 0))
            share = (qty / total_qty * 100) if total_qty else 0.0
            accum += share
            abc_class = r.get("abc", "")
            terms = r.get("terms", "")
            cnt = sum(1 for c in clients if str(c.get("market") or c.get("X") or c.get("P") or "").strip() == label)
            markets_table.append({
                "rank": r.get("rank", len(markets_table) + 1),
                "label": label,
                "quantity": qty,
                "share": share,
                "accumulated": min(accum, 100.0),
                "abc": abc_class,
                "client_count": cnt,
                "terms": terms
            })
    else:
        markets_table = _compute_dimension_table(clients, "market", ["G", "H", "I", "J", "K", "terms", "market_terms"])

    if precomputed_abc and "applications" in precomputed_abc:
        apps_table = []
        accum = 0.0
        for r in precomputed_abc["applications"]:
            label = r.get("label", "")
            qty = float(r.get("quantity", 0))
            share = (qty / total_qty * 100) if total_qty else 0.0
            accum += share
            abc_class = r.get("abc", "")
            terms = r.get("terms", "")
            cnt = sum(1 for c in clients if str(c.get("application") or c.get("Y") or c.get("R") or "").strip() == label)
            apps_table.append({
                "rank": r.get("rank", len(apps_table) + 1),
                "label": label,
                "quantity": qty,
                "share": share,
                "accumulated": min(accum, 100.0),
                "abc": abc_class,
                "client_count": cnt,
                "terms": terms
            })
    else:
        apps_table = _compute_dimension_table(clients, "application", ["L", "M", "N", "O", "P", "terms", "application_terms"])

    if precomputed_abc and "equipment" in precomputed_abc:
        equip_table = []
        accum = 0.0
        for r in precomputed_abc["equipment"]:
            label = r.get("label", "")
            qty = float(r.get("quantity", 0))
            share = (qty / total_qty * 100) if total_qty else 0.0
            accum += share
            abc_class = r.get("abc", "")
            terms = r.get("terms", "")
            term_list = [t.strip().lower() for t in terms.split(";") if t.strip()]
            cnt = sum(1 for c in clients if any(t in str(c.get("equipment") or c.get("Z") or c.get("S") or "").lower() for t in term_list) or label.lower() in str(c.get("equipment") or c.get("Z") or c.get("S") or "").lower())
            equip_table.append({
                "rank": r.get("rank", len(equip_table) + 1),
                "label": label,
                "quantity": qty,
                "share": share,
                "accumulated": min(accum, 100.0),
                "abc": abc_class,
                "client_count": cnt,
                "terms": terms
            })
    else:
        equip_table = _compute_dimension_table(clients, "equipment", ["Q", "R", "S", "T", "U", "terms", "equipment_terms", "equipment_candidate_1", "equipment_candidate_2"])

    md = []
    md.append(f"# MAPEAMENTO TÉCNICO E CURVAS ABC — PRODUTO `{product_name}`\n")
    if technical_family:
        md.append(f"**Família Técnica:** `{technical_family}`  ")
    md.append(f"**Perfil de mapeamento:** `{profile.profile_id}`  ")
    md.append(f"**Função do produto:** {profile.product_role}  ")
    md.append(f"**Volume Elegível Mapeado:** `{_fmt_int(total_qty)} un`  ")
    md.append(f"**Clientes Elegíveis:** `{len(clients)}`\n")
    apps_list = "; ".join(f"`{a}`" for a in profile.allowed_applications if not a.startswith("Não comprovado"))
    md.append(f"**Aplicações permitidas neste produto (fechadas):** {apps_list}\n")
    md.append("> Cada produto usa apenas seu vocabulário técnico. Aplicações de outros SKUs (ex.: A12038) não são reutilizadas aqui.\n")
    md.append("---\n")

    # TABELA 1: MERCADOS
    md.append(f"## CURVA ABC — MERCADOS CONTROLADOS DO PRODUTO {product_name}\n")
    md.append("| Rank | Mercado controlado | Quantidade comprada | % do total | % acumulado | Curva ABC | Clientes | Termos principais comprovados (Top 5) |")
    md.append("| :-: | :--- | :---: | :---: | :---: | :-: | :-: | :--- |")
    for r in markets_table:
        md.append(f"| {r['rank']} | {r['label']} | {_fmt_int(r['quantity'])} | {_fmt_pct(r['share'])} | {_fmt_pct(r['accumulated'])} | **{r['abc']}** | {r['client_count']} | {r['terms']} |")
    md.append("\n---\n")

    # TABELA 2: APLICAÇÕES
    md.append(f"## CURVA ABC — APLICAÇÕES TÉRMICAS CONTROLADAS\n")
    md.append(f"| Rank | Aplicação térmica controlada | Termos técnicos principais comprovados (Top 5) | Quantidade {product_name} | Participação % | Acumulado % | Curva ABC | Clientes |")
    md.append("| :-: | :--- | :--- | :---: | :---: | :---: | :-: | :-: |")
    for r in apps_table:
        md.append(f"| {r['rank']} | {r['label']} | {r['terms']} | {_fmt_int(r['quantity'])} | {_fmt_pct(r['share'])} | {_fmt_pct(r['accumulated'])} | **{r['abc']}** | {r['client_count']} |")
    md.append("\n---\n")

    # TABELA 3: EQUIPAMENTOS
    md.append(f"## CURVA ABC — FAMÍLIAS DE EQUIPAMENTOS CONTROLADAS\n")
    md.append(f"| Rank | Família de equipamento controlada | Equipamentos / termos específicos (Top 5) | Quantidade {product_name} | Participação % | Acumulado % | Curva ABC | Clientes |")
    md.append("| :-: | :--- | :--- | :---: | :---: | :---: | :-: | :-: |")
    for r in equip_table:
        md.append(f"| {r['rank']} | {r['label']} | {r['terms']} | {_fmt_int(r['quantity'])} | {_fmt_pct(r['share'])} | {_fmt_pct(r['accumulated'])} | **{r['abc']}** | {r['client_count']} |")
    md.append("\n---\n")

    # TABELA 4: CLIENTES ABC
    md.append(f"## CURVA ABC — CLIENTES DO PRODUTO {product_name}\n")
    md.append("| Rank | Cliente | Quantidade | % Part. | % Acum. | Classe | Tipo | Mercado | Aplicação | Equipamento | Status / Evidência |")
    md.append("| :-: | :--- | :---: | :---: | :---: | :-: | :--- | :--- | :--- | :--- | :--- |")
    
    # Sort clients descending by quantity
    sorted_clients = sorted(clients, key=lambda x: float(x.get("quantity") or x.get("B") or 0.0), reverse=True)
    c_accum = 0.0
    for idx, c in enumerate(sorted_clients, 1):
        c_qty = float(c.get("quantity") or c.get("B") or 0.0)
        c_share = (c_qty / total_qty * 100) if total_qty else 0
        c_accum += c_share
        
        c_name = str(c.get("client") or c.get("A") or c.get("B") or "")
        c_type = str(c.get("type") or c.get("F") or c.get("G") or "")
        c_abc = str(c.get("abc") or c.get("E") or c.get("F") or ("A" if c_accum - c_share < 80 or idx == 1 else "B" if c_accum - c_share < 95 else "C"))
        c_market = str(c.get("market") or c.get("X") or c.get("P") or "")
        c_app = str(c.get("application") or c.get("Y") or c.get("R") or "")
        c_equip = str(c.get("equipment") or c.get("Z") or c.get("S") or "")
        c_status = str(c.get("status") or c.get("W") or c.get("T") or ("✅ Comprovado" if c.get("publishable") else "🔍 Revisar"))
        
        md.append(f"| {idx} | {c_name} | {_fmt_int(c_qty)} | {_fmt_pct(c_share)} | {_fmt_pct(min(c_accum, 100.0))} | **{c_abc}** | {c_type} | {c_market} | {c_app} | {c_equip} | {c_status} |")
    
    md.append("\n")
    return "\n".join(md)


def export_all():
    out_dir = Path("outputs/mapeamento_produtos")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Golden A12038
    golden_a12038_path = Path("tests/golden/a12038.json")
    if golden_a12038_path.exists():
        data = json.loads(golden_a12038_path.read_text(encoding="utf-8"))
        md = generate_exact_product_markdown(
            "A12038", data.get("clients", []), "A12038", data.get("abc"), skip_sanitize=True
        )
        (out_dir / "A12038.md").write_text(md, encoding="utf-8")
        print("Exportado A12038.md")

    # 2. Golden VENT_FS4_400_ET
    golden_vent_path = Path("tests/golden/vent_fs4_400_et.json")
    if golden_vent_path.exists():
        data = json.loads(golden_vent_path.read_text(encoding="utf-8"))
        md = generate_exact_product_markdown(
            "VENT. FS/4-400 ET", data.get("clients", []), "AXIAL", data.get("abc"), skip_sanitize=True
        )
        (out_dir / "VENT._FS_4-400_ET.md").write_text(md, encoding="utf-8")
        print("Exportado VENT._FS_4-400_ET.md")

    # 3. Pilot Products
    pilot_path = Path("outputs/pilot_10_aprovado/pilot_results_aprovado.json")
    if pilot_path.exists():
        pilot_results = json.loads(pilot_path.read_text(encoding="utf-8"))
        for item in pilot_results:
            p_name = item.get("product", "")
            p_family = item.get("technical_family", "")
            p_clients = item.get("clients", [])
            filename = f"{_sanitize_filename(p_name)}.md"
            md = generate_exact_product_markdown(p_name, p_clients, p_family)
            (out_dir / filename).write_text(md, encoding="utf-8")
            print(f"Exportado {filename}")

    # 4. Generate README.md index
    index_md = [
        "# Índice de Mapeamento Técnico de Produtos (Padrão Golden A12038)\n",
        "Cada produto possui **perfil fechado** (`product_profiles.py`): mercados, aplicações e equipamentos próprios, sem reutilizar vocabulário de outro SKU.\n",
        "Os arquivos `.md` listam as **aplicações permitidas** no cabeçalho e aplicam o quality gate antes da publicação.\n",
        "| # | Produto | Família Técnica | Perfil | Status | Arquivo |",
        "| :-: | :--- | :--- | :--- | :---: | :--- |",
        "| ⭐️ | `A12038` | A12038 | `A12038` | Dourado | [📄 A12038.md](A12038.md) |",
        "| ⭐️ | `VENT. FS/4-400 ET` | AXIAL | `VENT_FS4_400_ET` | Dourado | [📄 VENT._FS_4-400_ET.md](VENT._FS_4-400_ET.md) |",
    ]
    
    if pilot_path.exists():
        pilot_results = json.loads(pilot_path.read_text(encoding="utf-8"))
        for idx, item in enumerate(pilot_results, 1):
            p_name = item.get("product", "")
            p_family = item.get("technical_family", "")
            p_profile = profile_for_product(p_name, p_family).profile_id
            filename = f"{_sanitize_filename(p_name)}.md"
            index_md.append(
                f"| {idx} | `{p_name}` | {p_family} | `{p_profile}` | Piloto | [📄 {filename}]({filename}) |"
            )

    (out_dir / "README.md").write_text("\n".join(index_md), encoding="utf-8")
    print("Exportado README.md do índice.")


if __name__ == "__main__":
    export_all()
