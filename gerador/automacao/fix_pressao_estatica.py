# -*- coding: utf-8 -*-
import sys, json, os, glob, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from regras import sanitizar_produto, validar_produto_completo

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DADOS_DIR = os.path.join(BASE_DIR, "gerador", "dados")

# Esses 7 ainda têm 'pressão estática elevada' — removemos o 'elevada'
for arq in glob.glob(os.path.join(DADOS_DIR, "*.json")):
    with open(arq, encoding="utf-8") as f:
        txt = f.read()
    txt2 = re.sub(r"pressao estatica elevada", "pressao estatica", txt, flags=re.IGNORECASE)
    txt2 = re.sub(r"pressão estática elevada", "pressão estática", txt2, flags=re.IGNORECASE)
    if txt2 != txt:
        with open(arq, "w", encoding="utf-8") as f:
            f.write(txt2)
        with open(arq, encoding="utf-8") as f:
            prod = json.load(f)
        ok, erros = validar_produto_completo(prod)
        slug = os.path.basename(arq).replace(".json", "")
        status = "OK" if ok else str(erros[:1])
        print(slug + " -> " + status)
