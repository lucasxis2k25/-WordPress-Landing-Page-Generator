# -*- coding: utf-8 -*-
"""
Diagnóstico Batch — Sell-Parts
Roda validar_produto_completo() em todos os JSONs de gerador/dados/
e imprime um relatório resumido.
"""
import sys, json, os, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regras import validar_produto_completo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados")

resultados = []
for f in sorted(glob.glob(os.path.join(DADOS_DIR, "*.json"))):
    slug = os.path.basename(f).replace(".json", "")
    try:
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        valido, erros = validar_produto_completo(data)
        resultados.append({"slug": slug, "ok": valido, "erros": erros})
    except Exception as e:
        resultados.append({"slug": slug, "ok": False, "erros": [f"ERRO CRITICO: {e}"]})

total = len(resultados)
ok    = sum(1 for r in resultados if r["ok"])
falhos = [r for r in resultados if not r["ok"]]

print(f"Total de JSONs : {total}")
print(f"Aprovados      : {ok}")
print(f"Com falhas     : {len(falhos)}")
print()

if not falhos:
    print("Todos os produtos passaram na validacao!")
    sys.exit(0)

print("=" * 70)
print("PRODUTOS COM FALHA")
print("=" * 70)
for r in falhos:
    print(f"\n[{r['slug']}]")
    for e in r["erros"]:
        print(f"  > {e}")

sys.exit(1 if falhos else 0)
