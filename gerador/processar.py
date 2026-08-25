import os
import sys
import json

# Adiciona gerador e gerador/automacao ao path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOMACAO_DIR = os.path.join(BASE_DIR, 'automacao')
sys.path.append(BASE_DIR)
sys.path.append(AUTOMACAO_DIR)

from catalogo import CATALOGO_TOP40
from scraper import scrape_DemoStore_product
from builder import build_clean_json
from renderizador import (
    render_resumo_tecnico, render_especificacoes, render_aplicacoes,
    render_beneficios, render_diferenciais, render_downloads,
    render_faq, render_alerta, render_schema_product, render_schema_faq
)

DADOS_DIR = os.path.join(BASE_DIR, 'dados')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
PRODUTOS_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'produtos'))

def exibir_menu():
    print("\n" + "=" * 70)
    print("  PAINEL Demo Store - DEEP RESEARCH & AUTOMACAO SEO B2B")
    print("=" * 70)
    print("  POS  STATUS      CLIQUES  IMPRESSOES  PRODUTO")
    print("  ---  ----------  -------  ----------  " + "-" * 38)
    for p in CATALOGO_TOP40:
        status = "[FEITO]" if p["status"] == "concluido" else "[PENDENTE]"
        print(f"  {p['pos']:>3}  {status:<10}  {p['cliques']:>7}  {p['impressoes']:>10}  {p['nome'][:40]}")
    print("-" * 70)

def processar_produto_por_pos(pos):
    produto = next((p for p in CATALOGO_TOP40 if p['pos'] == pos), None)
    if not produto:
        print(f"[!] Produto #{pos} não encontrado no catálogo Top 40.")
        return

    slug = produto['slug']
    url = f"https://DemoStore.com.br/produto/{slug}/"
    
    print(f"\n============================================================")
    print(f"[*] INICIANDO DEEP RESEARCH & GERACAO: #{pos} - {produto['nome']}")
    print(f"============================================================")
    
    # 1. Scraping técnico oficial
    print(f"\n[Etapa 1/4] Raspando especificações técnicas oficiais...")
    raw_data = scrape_DemoStore_product(url)
    
    # 2. Deep Research Builder & Estruturação
    print(f"\n[Etapa 2/4] Estruturando Inteligência de Busca e SEO B2B...")
    clean_data = build_clean_json(slug)
    
    if not clean_data:
        print(f"[!] Falha na geração dos dados limpos.")
        return

    # 3. Geração dos Blocos ACF + Schema JSON-LD
    print(f"\n[Etapa 3/4] Renderizando blocos HTML (.sp-) e Schemas JSON-LD...")
    specs_confirmadas = [
        s for s in clean_data.get("especificacoes", [])
        if s.get("confianca") == "100%" and s.get("valor") is not None
    ]

    payload = {
        "slug": clean_data["slug"],
        "nome": clean_data["nome"],
        "sku": clean_data["sku"],
        "acf": {
            "sp_resumo_tecnico": render_resumo_tecnico(clean_data),
            "sp_especificacoes": render_especificacoes(specs_confirmadas),
            "sp_aplicacoes": render_aplicacoes(clean_data.get("aplicacoes", []), clean_data.get("categoria_link")),
            "sp_beneficios": render_beneficios(clean_data.get("beneficios", [])),
            "sp_diferenciais": render_diferenciais(clean_data.get("diferenciais", [])),
            "sp_downloads": render_downloads(clean_data["nome"]),
            "sp_faq": render_faq(clean_data.get("faq", [])),
            "sp_alerta_tecnico": render_alerta(clean_data.get("alerta_tecnico", "")),
        },
        "schema_jsonld": {
            "product": render_schema_product(clean_data),
            "faq": render_schema_faq(clean_data.get("faq", [])),
        },
    }

    # Salva Output ACF
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    acf_json_path = os.path.join(OUTPUT_DIR, f"{slug}_acf.json")
    with open(acf_json_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 4. Salva Relatório de Pesquisa Markdown no diretório produtos/
    prod_folder = os.path.join(PRODUTOS_DIR, slug)
    os.makedirs(prod_folder, exist_ok=True)
    report_path = os.path.join(prod_folder, "pesquisa-concorrentes.md")
    
    report_content = f"""# Pesquisa de Inteligência Competitiva - {produto['nome']}

## 1. Grau de Confiança (Especificações Técnicas Oficiais)

| Informação | Valor | Confiança | Fonte |
| :--- | :--- | :--- | :--- |
"""
    for spec in clean_data.get("especificacoes", []):
        report_content += f"| **{spec['atributo']}** | {spec['valor']} | {spec['confianca']} | {spec['fonte']} |\n"

    report_content += f"""
---

## 2. Palavras-Chave e Intenções de Busca (SEO)

- **Grupo A (Código/SKU):** `{clean_data['sku']}`, `{slug}`
- **Grupo B (Aplicação):** {', '.join(clean_data.get('aplicacoes', [])[:3])}
- **Grupo C (Urgência/Troca):** Reposição urgente, manutenção de refrigeração B2B

---

## 3. Schemas Gerados
- **Product Schema:** OK (Nativo + Custom)
- **FAQPage Schema:** OK ({len(clean_data.get('faq', []))} perguntas renderizadas)
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"\n============================================================")
    print(f"[OK] PROCESSO CONCLUIDO COM SUCESSO PARA O PRODUTO #{pos}!")
    print(f"============================================================")
    print(f"  - Payload ACF Gerado:   {acf_json_path}")
    print(f"  - Pesquisa Salva em:    {report_path}")
    print(f"============================================================\n")

def main():
    if len(sys.argv) > 1:
        try:
            pos = int(sys.argv[1])
            processar_produto_por_pos(pos)
            return
        except ValueError:
            pass

    exibir_menu()
    try:
        escolha = input("\nDigite o número (POS 1-40) do produto para executar Deep Research & Automação (0 para sair): ")
        pos = int(escolha.strip())
        if pos > 0:
            processar_produto_por_pos(pos)
    except (ValueError, KeyboardInterrupt, EOFError):
        print("\nSaindo...")

if __name__ == '__main__':
    main()
