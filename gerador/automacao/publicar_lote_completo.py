# -*- coding: utf-8 -*-
"""
=============================================================
Demo Store — PUBLICADOR EM LOTE NO WORDPRESS (TOP CATALOGO)
Sincroniza todos os produtos do catálogo com o WooCommerce/WordPress
Atualiza campos ACF, Descrição, Meta Data e Schemas JSON-LD
=============================================================
"""

import os
import sys
import json
import time
import datetime

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GERADOR_DIR = os.path.join(PROJ_DIR, "gerador")
sys.path.insert(0, GERADOR_DIR)
sys.path.insert(0, os.path.join(GERADOR_DIR, "automacao"))

from catalogo import CATALOGO_TOP40
from publicar_wordpress import update_product_acf

DB_PATH = os.path.join(GERADOR_DIR, "produtos_db.json")
DADOS_DIR = os.path.join(GERADOR_DIR, "dados")


def main():
    print("=" * 70)
    print("  Demo Store — INICIANDO PUBLICAÇÃO EM LOTE NO WORDPRESS")
    print("=" * 70)

    # Carrega db local
    db = {}
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)

    sucessos = []
    falhas = []
    ignorados = []

    # Lista de slugs a processar
    slugs_para_publicar = []
    for p in CATALOGO_TOP40:
        slug = p["slug"]
        json_file = os.path.join(DADOS_DIR, f"{slug}.json")
        if os.path.exists(json_file):
            slugs_para_publicar.append((p["pos"], slug, p["nome"]))
        else:
            ignorados.append((slug, "Arquivo JSON não encontrado em dados/"))

    print(f"\nTotal de produtos para publicar: {len(slugs_para_publicar)}")
    print("-" * 70)

    for i, (pos, slug, nome) in enumerate(slugs_para_publicar, start=1):
        print(f"\n[{i}/{len(slugs_para_publicar)}] Publicando #{pos:02d}: {nome} ({slug})...")
        try:
            ok = update_product_acf(slug, skip_validation=True)
            if ok:
                sucessos.append((pos, slug, nome))
                # Atualiza DB local
                if slug in db:
                    db[slug]["status"] = "publicado"
                    db[slug]["data_publicacao"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db[slug]["log_publicacao"] = "Publicado automaticamente via API REST (Zero Inferência)"
                print(f"  --> [OK] Publicado com sucesso!")
            else:
                falhas.append((pos, slug, nome, "Erro na API do WordPress / Mismatch"))
                print(f"  --> [FALHA] Não foi possível publicar este produto.")
        except Exception as e:
            falhas.append((pos, slug, nome, str(e)))
            print(f"  --> [ERRO] Exceção: {e}")

        # Salva o banco a cada iteração para persistência
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

        # Pequena pausa entre requisições para evitar rate limit
        time.sleep(1)

    print("\n" + "=" * 70)
    print("  RELATÓRIO DE PUBLICAÇÃO NO WORDPRESS:")
    print("=" * 70)
    print(f"  Total Publicados com Sucesso: {len(sucessos)}")
    print(f"  Total com Falha:               {len(falhas)}")
    print(f"  Total Ignorados (Sem JSON):    {len(ignorados)}")

    if falhas:
        print("\n--- PRODUTOS COM FALHA ---")
        for pos, slug, nome, motivo in falhas:
            print(f"  #{pos:02d} | {slug} | Motivo: {motivo}")

    print("\n[OK] Processo de publicação em lote concluído!")


if __name__ == "__main__":
    main()
