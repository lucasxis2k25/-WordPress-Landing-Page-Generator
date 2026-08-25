# -*- coding: utf-8 -*-
"""
=============================================================
Demo Store — SINCRONIZADOR GLOBAL DEFINITIVO
Garante que 100% dos produtos tenham:
1. Diferenciais técnicos explicados e substantivos
2. Onde Usar com descrições contextuais de equipamentos
3. Zero Inferência e sem textos corrompidos
4. Sincronização nos arquivos JSON, Markdown e WordPress
=============================================================
"""

import os
import sys
import json

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GERADOR_DIR = os.path.join(PROJ_DIR, "gerador")
PRODUTOS_DIR = os.path.join(PROJ_DIR, "produtos")

sys.path.insert(0, GERADOR_DIR)
sys.path.insert(0, os.path.join(GERADOR_DIR, "automacao"))

from processar_33_produtos import extrair_dados_planilhas, match_product_mapping, construir_produto_zero_inferencia
from gerar_conteudo_acf import gerar_payload_acf, salvar_output
from publicar_wordpress import update_product_acf

DADOS_DIR = os.path.join(GERADOR_DIR, "dados")
DB_PATH = os.path.join(GERADOR_DIR, "produtos_db.json")


def main():
    print("=" * 70)
    print("  Demo Store — SINCRONIZANDO CORREÇÕES GLOBAIS EM TODOS OS PRODUTOS")
    print("=" * 70)

    mapeamentos = extrair_dados_planilhas()
    print(f"[*] Total de fontes de mapeamento indexadas: {len(mapeamentos)}")

    # Carrega banco local
    db = {}
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)

    json_files = [f for f in os.listdir(DADOS_DIR) if f.endswith(".json")]
    print(f"[*] Total de produtos JSON encontrados em dados/: {len(json_files)}")

    processados = 0
    atualizados_md = 0

    for jf in json_files:
        json_path = os.path.join(DADOS_DIR, jf)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        slug = data.get("slug")
        if not slug:
            continue

        # Mapeamento
        map_info = match_product_mapping(slug, mapeamentos)
        
        # Constrói com o novo motor aperfeiçoado
        novo_produto = construir_produto_zero_inferencia(data, map_info)

        # Salva o JSON em dados/
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(novo_produto, f, ensure_ascii=False, indent=2)

        # Gera e salva ACF payload
        payload = gerar_payload_acf(novo_produto)
        salvar_output(payload)

        # Atualiza acf-campos-prontos.md nas pastas de produtos se existir
        for root, dirs, files in os.walk(PRODUTOS_DIR):
            if os.path.basename(root) == slug and "acf-campos-prontos.md" in files:
                md_path = os.path.join(root, "acf-campos-prontos.md")
                # Gera conteúdo markdown formatado
                acf = payload.get("acf", {})
                md_content = f"""# {novo_produto['nome']} — Campos ACF Prontos para Copiar e Colar

> **Produto:** {novo_produto['nome']}  
> **SKU:** {novo_produto['sku']}  
> **Slug:** `{slug}`  

---

## CAMPO 1 — sp_resumo_tecnico
> Tipo: Área de Texto / WYSIWYG

```html
{acf.get('sp_resumo_tecnico', '')}
```

---

## CAMPO 2 — sp_especificacoes
> Tipo: Editor WYSIWYG

```html
{acf.get('sp_especificacoes', '')}
```

---

## CAMPO 3 — sp_aplicacoes (Aplicações)
> Tipo: Editor WYSIWYG

```html
{acf.get('sp_aplicacoes', '')}
```

---

## CAMPO 3.1 — sp_aplicacoes_equipamento (Onde Usar)
> Tipo: Editor WYSIWYG

```html
{acf.get('sp_aplicacoes_equipamento', '')}
```

---

## CAMPO 4 — sp_beneficios
> Tipo: Editor WYSIWYG

```html
{acf.get('sp_beneficios', '')}
```

---

## CAMPO 5 — sp_diferenciais
> Tipo: Editor WYSIWYG

```html
{acf.get('sp_diferenciais', '')}
```

---

## CAMPO 6 — sp_downloads
> Tipo: Editor WYSIWYG

```html
{acf.get('sp_downloads', '')}
```

---

## CAMPO 7 — sp_faq
> Tipo: Editor WYSIWYG

```html
{acf.get('sp_faq', '')}
```

---

## CAMPO 8 — sp_mercado
> Tipo: Editor WYSIWYG

```html
{acf.get('sp_mercado', '')}
```
"""
                with open(md_path, "w", encoding="utf-8") as mdf:
                    mdf.write(md_content)
                atualizados_md += 1

        processados += 1

    print(f"\n[OK] Produtos processados e regerados: {processados}")
    print(f"[OK] Arquivos Markdown atualizados na pasta produtos/: {atualizados_md}")

    # Publicação completa no WordPress
    print("\n" + "=" * 70)
    print("  ENVIANDO ATUALIZAÇÕES COMPLETAS PARA O WORDPRESS")
    print("=" * 70)

    from catalogo import CATALOGO_TOP40
    sucessos = 0
    falhas = 0

    for p in CATALOGO_TOP40:
        slug = p["slug"]
        json_file = os.path.join(DADOS_DIR, f"{slug}.json")
        if os.path.exists(json_file):
            print(f"[*] Sincronizando #{p['pos']:02d}: {p['nome']} ({slug})...")
            try:
                ok = update_product_acf(slug, skip_validation=True)
                if ok:
                    sucessos += 1
                    if slug in db:
                        db[slug]["status"] = "em_revisao"
                        db[slug]["aprovado_por"] = None
                else:
                    falhas += 1
            except Exception as e:
                print(f"[!] Erro ao publicar {slug}: {e}")
                falhas += 1

    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"  SINCRONIZAÇÃO GLOBAL CONCLUÍDA:")
    print(f"  Total de Produtos Atualizados no WP: {sucessos}")
    print(f"  Status mantido em: 'Em Revisão / Auditoria'")
    print("=" * 70)


if __name__ == "__main__":
    main()
