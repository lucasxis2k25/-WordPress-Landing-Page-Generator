# -*- coding: utf-8 -*-
"""
=============================================================
  Demo Store - GERADOR DE LANDING PAGES B2B
  Sistema de Produção de Conteúdo ACF para WordPress
=============================================================
"""

import json
import os
import sys

from catalogo import CATALOGO_TOP40, get_pendentes, get_concluidos
from regras import validar_produto_completo
from renderizador import (
    render_resumo_tecnico,
    render_especificacoes,
    render_aplicacoes,
    render_aplicacoes_categoria,
    render_aplicacoes_equipamento,
    render_beneficios,
    render_diferenciais,
    render_downloads,
    render_faq,
    render_alerta,
    render_mercado,
    render_schema_product,
    render_schema_faq,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def exibir_menu():
    """Mostra o menu de produtos ordenados por prioridade SEO."""
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 70)
    print("  Demo Store - GERADOR DE LANDING PAGES B2B")
    print("  Sistema de Producao de Conteudo ACF (WordPress)")
    print("=" * 70)
    print()
    concluidos = get_concluidos()
    pendentes = get_pendentes()
    print(f"  Produtos concluidos: {len(concluidos)}/40")
    print(f"  Produtos pendentes:  {len(pendentes)}/40")
    print("-" * 70)
    print()
    print("  POS  STATUS      CLIQUES  IMPRESSOES  PRODUTO")
    print("  ---  ----------  -------  ----------  " + "-" * 38)
    for p in CATALOGO_TOP40:
        status = "[FEITO]" if p["status"] == "concluido" else "[     ]"
        cor_status = status
        nome_curto = p["nome"][:42]
        print(f"  {p['pos']:>3}  {cor_status:<10}  {p['cliques']:>7}  {p['impressoes']:>10}  {nome_curto}")
    print()
    print("-" * 70)
    print("  Digite o NUMERO (pos) do produto para gerar o conteudo ACF.")
    print("  Digite 0 para sair.")
    print()

def selecionar_produto():
    while True:
        exibir_menu()
        try:
            escolha = int(input("  Produto (1-40): "))
        except (ValueError, EOFError):
            print("  Entrada invalida.")
            continue
        if escolha == 0:
            print("\n  Encerrando. Ate a proxima!")
            sys.exit(0)
        produto = next((p for p in CATALOGO_TOP40 if p["pos"] == escolha), None)
        if not produto:
            print(f"  Produto {escolha} nao encontrado. Tente novamente.")
            input("  Pressione Enter...")
            continue
        if produto["status"] == "concluido":
            resp = input(f"  '{produto['nome']}' ja foi concluido. Regerar? (s/n): ").strip().lower()
            if resp != "s":
                continue
        return produto

def carregar_dados(slug):
    caminho = os.path.join(DADOS_DIR, f"{slug}.json")
    if not os.path.exists(caminho):
        return None, caminho
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f), caminho


def gerar_payload_acf(produto_data):
    # Filtrar apenas specs confirmadas (100%)
    specs_confirmadas = [
        s for s in produto_data.get("especificacoes", [])
        if s.get("confianca") == "100%" and s.get("valor") is not None
    ]

    html_app_cat = render_aplicacoes_categoria(produto_data)
    html_app_eq = render_aplicacoes_equipamento(produto_data)
    html_mercado = render_mercado(produto_data)

    payload = {
        "slug": produto_data["slug"],
        "nome": produto_data["nome"],
        "sku": produto_data["sku"],
        "acf": {
            "sp_resumo_tecnico": render_resumo_tecnico(produto_data),
            "sp_especificacoes": render_especificacoes(specs_confirmadas, produto_data.get("alerta_tabela", ""), produto_data.get("curva_performance_html", "")),
            "sp_aplicacoes": html_app_cat,
            "Aplicacoes_equipamentos": html_app_eq,
            "aplicacoes_equipamentos": html_app_eq,
            "sp_aplicacoes_equipamentos": html_app_eq,
            "sp_aplicacoes_equipamento": html_app_eq,
            "sp_mercado": html_mercado,
            "sp_beneficios": render_beneficios(produto_data.get("beneficios", [])),
            "sp_diferenciais": render_diferenciais(produto_data.get("diferenciais", [])),
            "sp_downloads": render_downloads(produto_data["nome"]),
            "sp_faq": render_faq(produto_data.get("faq", [])),
            "sp_alerta_tecnico": render_alerta(produto_data.get("alerta_tecnico", "")),
        },
        "schema_jsonld": {
            "product": render_schema_product(produto_data),
            "faq": render_schema_faq(produto_data.get("faq", [])),
        },
    }
    return payload

def salvar_output(payload):
    slug = payload["slug"]
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    json_path = os.path.join(OUTPUT_DIR, f"{slug}_acf.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    txt_path = os.path.join(OUTPUT_DIR, f"{slug}_acf_campos.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"{'='*70}\n")
        f.write(f"  PAYLOAD ACF - {payload['nome']}\n")
        f.write(f"  SKU: {payload['sku']}\n")
        f.write(f"{'='*70}\n\n")

        for campo, valor in payload["acf"].items():
            f.write(f"--- CAMPO: {campo} ---\n")
            f.write(f"Cole no ACF do WordPress (campo '{campo}'):\n\n")
            f.write(valor)
            f.write(f"\n\n{'~'*70}\n\n")

        f.write(f"\n--- SCHEMA JSON-LD (Product) ---\n")
        f.write(f'<script type="application/ld+json">\n{payload["schema_jsonld"]["product"]}\n</script>\n\n')

        f.write(f"\n--- SCHEMA JSON-LD (FAQPage) ---\n\n")
        f.write(f'<script type="application/ld+json">\n{payload["schema_jsonld"]["faq"]}\n</script>\n')

    # Salva também diretamente no diretório do produto (produtos/{slug}/acf-campos-prontos.md)
    PRODUTOS_DIR = os.path.join(os.path.dirname(BASE_DIR), "produtos", slug)
    os.makedirs(PRODUTOS_DIR, exist_ok=True)
    md_path = os.path.join(PRODUTOS_DIR, "acf-campos-prontos.md")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Campos ACF Prontos para Colar no WordPress\n")
        f.write(f"# Produto: {payload['nome']}\n")
        f.write(f"# Status: VALIDADO (Zero Inferência)\n\n")
        f.write(f"---\n\n")
        
        campos_map = [
            ("sp_resumo_tecnico", "CAMPO 1 — sp_resumo_tecnico", "Editor WYSIWYG"),
            ("sp_especificacoes", "CAMPO 2 — sp_especificacoes", "Editor WYSIWYG"),
            ("sp_aplicacoes", "CAMPO 3 — sp_aplicacoes (Aplicações)", "Editor WYSIWYG"),
            ("sp_aplicacoes_equipamento", "CAMPO 3.1 — sp_aplicacoes_equipamento (Onde Usar)", "Editor WYSIWYG"),
            ("sp_beneficios", "CAMPO 4 — sp_beneficios", "Editor WYSIWYG"),
            ("sp_diferenciais", "CAMPO 5 — sp_diferenciais", "Editor WYSIWYG"),
            ("sp_downloads", "CAMPO 6 — sp_downloads", "Editor WYSIWYG"),
            ("sp_faq", "CAMPO 7 — sp_faq", "Editor WYSIWYG"),
            ("sp_mercado", "CAMPO 8 — sp_mercado", "Editor WYSIWYG"),
            ("sp_alerta_tecnico", "CAMPO 9 — sp_alerta_tecnico", "Área de texto (texto puro)"),
        ]

        for key, titulo, tipo in campos_map:
            f.write(f"## {titulo}\n> Tipo: {tipo}\n\n")
            content = payload["acf"].get(key, "")
            if "texto puro" in tipo.lower():
                f.write(f"```\n{content}\n```\n\n---\n\n")
            else:
                f.write(f"```html\n{content}\n```\n\n---\n\n")

    return json_path, txt_path


def main():
    if len(sys.argv) > 1:
        # Se passar o arquivo json direto, extrai o slug
        arg = sys.argv[1]
        if arg.endswith('.json'):
            slug = os.path.basename(arg).replace('.json', '')
        else:
            slug = arg
        
        produto = next((p for p in CATALOGO_TOP40 if p["slug"] == slug), None)
        if not produto:
            print(f"Produto não encontrado no catálogo para o slug: {slug}")
            sys.exit(1)
        nome = produto["nome"]
    else:
        produto = selecionar_produto()
        slug = produto["slug"]
        nome = produto["nome"]

    print(f"\n  Produto selecionado: #{produto['pos']} - {nome}")
    print(f"  Slug: {slug}")
    print(f"  Buscando dados em: gerador/dados/{slug}.json")
    print()

    dados, caminho = carregar_dados(slug)
    if dados is None:
        print(f"  ERRO: Arquivo de dados nao encontrado!")
        print(f"  Caminho esperado: {caminho}")
        if len(sys.argv) <= 1:
            input("\n  Pressione Enter para voltar ao menu...")
            return main()
        else:
            sys.exit(1)

    print("  [1/3] Executando validacao Zero Inferencia...")
    valido, erros = validar_produto_completo(dados)

    if not valido:
        print("\n  VALIDACAO FALHOU! Inconsistencias detectadas:\n")
        for erro in erros:
            print(f"    > {erro}")
        print("\n  Corrija o arquivo JSON e tente novamente.")
        if len(sys.argv) <= 1:
            input("\n  Pressione Enter para voltar ao menu...")
            return main()
        else:
            sys.exit(1)

    print("    Todas as regras passaram com sucesso.")

    print("  [2/3] Gerando HTML dos blocos ACF...")
    payload = gerar_payload_acf(dados)

    print("  [3/3] Salvando output...")
    json_path, txt_path = salvar_output(payload)

    print("\n  " + "=" * 60)
    print("  CONTEUDO GERADO COM SUCESSO!")
    print("  " + "=" * 60 + "\n")
    print(f"  JSON completo:  {json_path}")
    print(f"  TXT (copiar):   {txt_path}\n")
    print(f"  Abra o arquivo TXT e copie cada campo para o ACF no WordPress.\n")

    if len(sys.argv) > 1:
        sys.exit(0)

    resp = input("  Gerar outro produto? (s/n): ").strip().lower()
    if resp == "s":
        return main()
    else:
        print("\n  Encerrando. Bom trabalho!")

if __name__ == "__main__":
    main()
