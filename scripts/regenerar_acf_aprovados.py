# -*- coding: utf-8 -*-
"""Regenera ACF + schema apenas para JSONs que passam em regras.py."""
import glob
import json
import os
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE, "gerador"))

from regras import validar_produto_completo
from gerar_conteudo_acf import gerar_payload_acf, salvar_output


def main():
    dados_dir = os.path.join(BASE, "gerador", "dados")
    ok_n = 0
    fail_n = 0
    for path in sorted(glob.glob(os.path.join(dados_dir, "*.json"))):
        slug = os.path.basename(path).replace(".json", "")
        with open(path, "r", encoding="utf-8") as f:
            dados = json.load(f)
        ok, erros = validar_produto_completo(dados, sanitizar=True)
        if not ok:
            fail_n += 1
            continue
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        payload = gerar_payload_acf(dados)
        # garantia extra: schema sem isSimilarTo
        schema_prod = json.loads(payload["schema_jsonld"]["product"])
        schema_prod.pop("isSimilarTo", None)
        payload["schema_jsonld"]["product"] = json.dumps(schema_prod, ensure_ascii=False, indent=2)
        salvar_output(payload)
        ok_n += 1
        print(f"  [ACF OK] {slug}")
    print(f"\nRegenerados: {ok_n} | Bloqueados (não regenerar): {fail_n}")


if __name__ == "__main__":
    main()
