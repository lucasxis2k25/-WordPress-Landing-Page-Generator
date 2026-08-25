# -*- coding: utf-8 -*-
import json
import os
import sys

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GERADOR_DIR = os.path.join(PROJ_DIR, "gerador")
sys.path.insert(0, GERADOR_DIR)
sys.path.insert(0, os.path.join(GERADOR_DIR, "automacao"))

from gerar_conteudo_acf import gerar_payload_acf, salvar_output
from publicar_wordpress import update_product_acf

img_url = "https://DemoStore.com.br/wp-content/uploads/2026/08/curva-desempenho-fs3-300-ec.png"

curva_html = f"""<div style="margin-top: 25px; text-align: center; background: #ffffff; padding: 15px; border-radius: 8px;">
  <img src="{img_url}" alt="Curva de Vazão x Pressão - FS/3-300 E EC" style="max-width: 460px; width: 100%; height: auto; display: inline-block;" />
</div>"""

slugs = ["exaustor-axial-ec-300mm-fs-3-300-e-ec", "exaustor-axial-de-rotor-externo-ec-fs-3-300-e-ec"]

for slug in slugs:
    json_path = os.path.join(GERADOR_DIR, "dados", f"{slug}.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["curva_performance_html"] = curva_html
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        payload = gerar_payload_acf(data)
        salvar_output(payload)
        print(f"[OK] Payload atualizado com imagem simples da curva para {slug}")

# Publica o produto no WooCommerce
ok = update_product_acf("exaustor-axial-ec-300mm-fs-3-300-e-ec", skip_validation=True)
print("Publicação WordPress status:", ok)
