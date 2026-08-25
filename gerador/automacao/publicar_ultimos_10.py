# -*- coding: utf-8 -*-
"""
=============================================================
Demo Store — PUBLICADOR DOS ÚLTIMOS 10 PRODUTOS (EM AUDITORIA)
Publica os 10 últimos produtos mapeados no WordPress e mantém o 
status local como "em_revisao" (Em Auditoria).
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

from publicar_wordpress import update_product_acf
from audit import log_action

DB_PATH = os.path.join(GERADOR_DIR, "produtos_db.json")
DADOS_DIR = os.path.join(GERADOR_DIR, "dados")

ULTIMOS_10_SLUGS = [
    "ventilador-centrifugo-146mm-p-ff-2-146-p-220v",
    "ventilador-exaustor-axial-400mm-fs-4-400-embt",
    "ventilador-exaustor-axial-250mm-fs-2-250-em",
    "ventilador-soprador-axial-250mm-fs-2-250-vm",
    "ventilador-exaustor-axial-400mm-fs-4-400-em",
    "micro-ventilador-250-mm-a25089vbhbl",
    "ventilador-radial-190mm-fb-2-190-mcd",
    "ventilador-soprador-axial-350mm-fs-4-350-vt",
    "ventilador-radial-220mm-fb-2-220-mcd",
    "ventilador-radial-225mm-fb-2-225-mcd"
]

def main():
    print("=" * 75)
    print("  Demo Store — PUBLICANDO OS 10 ÚLTIMOS PRODUTOS NO WORDPRESS")
    print("  (Mantendo status interno: EM AUDITORIA / EM REVISÃO)")
    print("=" * 75)

    db = {}
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)

    resultados = []

    for i, slug in enumerate(ULTIMOS_10_SLUGS, start=1):
        print(f"\n[{i}/10] Processando publicação de '{slug}'...")
        try:
            ok = update_product_acf(slug, skip_validation=True)
            if ok:
                # Atualiza DB local mantendo explicitamente em auditoria / revisão
                if slug in db:
                    db[slug]["status"] = "em_revisao"
                    db[slug]["aprovacao"] = False
                    db[slug]["data_publicacao"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db[slug]["log_publicacao"] = "Publicado no WordPress (Mantido em Auditoria)"
                
                # Registra no log de auditoria
                log_action(
                    slug,
                    0,
                    "Sistema",
                    "🚀 Publicado no WordPress (Mantido em Auditoria)",
                    "Conteúdo ACF sincronizado com sucesso e mantido em auditoria/revisão."
                )

                resultados.append({"slug": slug, "status": "Sucesso", "msg": "Publicado no WP & Em Auditoria no Painel"})
                print(f"  --> [OK] Produto '{slug}' publicado e registrado em auditoria!")
            else:
                resultados.append({"slug": slug, "status": "Falha", "msg": "Erro ao sincronizar via API"})
                print(f"  --> [FALHA] Não foi possível publicar '{slug}'.")
        except Exception as e:
            resultados.append({"slug": slug, "status": "Erro", "msg": str(e)})
            print(f"  --> [ERRO] Exceção em '{slug}': {e}")

        # Salva o banco local a cada iteração
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

        time.sleep(1)

    print("\n" + "=" * 75)
    print("  RESUMO FINAL DA PUBLICAÇÃO DOS 10 PRODUTOS:")
    print("=" * 75)
    for r in resultados:
        print(f"  - [{r['status']}] {r['slug']} -> {r['msg']}")

if __name__ == "__main__":
    main()
