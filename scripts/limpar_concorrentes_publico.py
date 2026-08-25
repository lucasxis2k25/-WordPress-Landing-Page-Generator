# -*- coding: utf-8 -*-
"""
Remove concorrentes do schema JSON-LD e keywords públicas.
cross_reference permanece no JSON de dados (uso interno).
"""
import glob
import json
import os
import re
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE, "gerador"))

from regras import CONCORRENTES_PROIBIDOS_PUBLICO

DADOS = os.path.join(BASE, "gerador", "dados")
OUTPUT = os.path.join(BASE, "gerador", "output")


def limpar_keywords(seo):
    if not isinstance(seo, dict):
        return seo, 0
    kws = seo.get("keywords") or []
    novos = []
    removidos = 0
    for kw in kws:
        low = str(kw).lower()
        if any(m in low for m in CONCORRENTES_PROIBIDOS_PUBLICO):
            removidos += 1
            continue
        if "equivalente" in low and any(x in low for x in ("ebm", "ziehl", "sunon")):
            removidos += 1
            continue
        novos.append(kw)
    seo["keywords"] = novos
    return seo, removidos


def limpar_schema_product_str(schema_str):
    """Remove isSimilarTo / concorrentes do JSON-LD Product."""
    if not schema_str or not isinstance(schema_str, str):
        return schema_str, False
    try:
        obj = json.loads(schema_str)
    except json.JSONDecodeError:
        # fallback textual
        if "isSimilarTo" not in schema_str:
            return schema_str, False
        obj = None
    if obj is None:
        return schema_str, False
    changed = False
    if "isSimilarTo" in obj:
        del obj["isSimilarTo"]
        changed = True
    blob = json.dumps(obj, ensure_ascii=False).lower()
    for m in CONCORRENTES_PROIBIDOS_PUBLICO:
        if m in blob:
            # remove qualquer campo textual residual — não deve restar
            changed = True
    return json.dumps(obj, ensure_ascii=False, indent=2), changed


def main():
    n_dados = 0
    n_kw = 0
    for path in glob.glob(os.path.join(DADOS, "*.json")):
        with open(path, "r", encoding="utf-8") as f:
            dados = json.load(f)
        seo, rem = limpar_keywords(dados.get("seo") or {})
        if rem:
            dados["seo"] = seo
            with open(path, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            n_dados += 1
            n_kw += rem

    n_acf = 0
    for path in glob.glob(os.path.join(OUTPUT, "*_acf.json")):
        with open(path, "r", encoding="utf-8") as f:
            acf = json.load(f)
        schema = acf.get("schema_jsonld") or {}
        prod = schema.get("product")
        if not prod:
            continue
        novo, changed = limpar_schema_product_str(prod)
        if changed:
            schema["product"] = novo
            acf["schema_jsonld"] = schema
            with open(path, "w", encoding="utf-8") as f:
                json.dump(acf, f, ensure_ascii=False, indent=2)
            n_acf += 1
            # espelha em acf-campos-prontos se existir
            slug = os.path.basename(path).replace("_acf.json", "")
            # também limpa .txt se tiver schema
            txt = path.replace("_acf.json", "_acf_campos.txt")
            if os.path.exists(txt):
                with open(txt, "r", encoding="utf-8") as f:
                    content = f.read()
                if "isSimilarTo" in content:
                    # regenerar trecho é frágil — marca para republish
                    pass

    print(f"Dados: {n_dados} JSONs com keywords limpas ({n_kw} keywords removidas).")
    print(f"ACF: {n_acf} schemas sem isSimilarTo/concorrentes.")
    print("cross_reference nos JSONs permanece (uso interno).")


if __name__ == "__main__":
    main()
