# -*- coding: utf-8 -*-
import os
import sys
import glob
import re
import json

# Adiciona diretórios ao sys.path
PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ_DIR)
GERADOR_DIR = os.path.join(PROJ_DIR, "gerador")
sys.path.insert(0, GERADOR_DIR)

from gerador.gerar_lpp_ia import generate_lpp_via_gemini

def parse_markdown_feeder(md_path):
    """Lê o arquivo Markdown do Feeder e extrai as listas de Mercados, Aplicações e Equipamentos."""
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    mercados = []
    aplicacoes = []
    equipamentos = []
    
    current_section = None
    
    for line in lines:
        if line.startswith("## CURVA ABC — MERCADOS"):
            current_section = "MERCADOS"
            continue
        elif line.startswith("## CURVA ABC — APLICAÇÕES"):
            current_section = "APLICACOES"
            continue
        elif line.startswith("## CURVA ABC — FAMÍLIAS DE EQUIPAMENTOS"):
            current_section = "EQUIPAMENTOS"
            continue
        elif line.startswith("## CURVA ABC — CLIENTES"):
            current_section = "CLIENTES"
            continue
            
        if current_section and line.startswith("|") and "Rank" not in line and ":---" not in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                # O termo principal geralmente está na segunda ou terceira coluna útil
                term = parts[2]
                if term:
                    if current_section == "MERCADOS" and term not in mercados:
                        mercados.append(term)
                    elif current_section == "APLICACOES" and term not in aplicacoes:
                        aplicacoes.append(term)
                    elif current_section == "EQUIPAMENTOS" and term not in equipamentos:
                        equipamentos.append(term)
                        
    return mercados[:6], aplicacoes[:4], equipamentos[:4]

def formatar_slug(nome):
    import unicodedata
    s = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s-]+', '-', s)
    return s.strip('-')

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-one", action="store_true", help="Testa apenas o primeiro arquivo")
    parser.add_argument("--slug", type=str, help="Testa um slug específico")
    args = parser.parse_args()

    feeder_dir = os.path.join(PROJ_DIR, "mapeamento de produto", "outputs", "mapeamento_produtos")
    if not os.path.exists(feeder_dir):
        print(f"Diretório do feeder não encontrado: {feeder_dir}")
        return
        
    md_files = glob.glob(os.path.join(feeder_dir, "*.md"))
    if not md_files:
        print("Nenhum arquivo .md encontrado no feeder.")
        return
        
    db_path = os.path.join(GERADOR_DIR, "produtos_db.json")
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
    else:
        db = {}
        
    for md_file in md_files:
        filename = os.path.basename(md_file)
        if filename.upper() == "README.MD":
            continue
            
        # Tenta extrair o nome do produto do título do arquivo MD
        with open(md_file, 'r', encoding='utf-8') as f:
            first_line = f.readline()
        
        match = re.search(r'`(.*?)`', first_line)
        if not match:
            continue
            
        product_name = match.group(1)
        slug = formatar_slug(product_name)
        
        if args.slug and slug != args.slug:
            continue
        
        # Garante que o produto existe no DB para o script de IA poder rodar
        if slug not in db:
            print(f"[*] Cadastrando novo produto no DB local: {slug}")
            db[slug] = {
                "nome": product_name,
                "sku": product_name.split("-")[-1].strip() if "-" in product_name else "",
                "status": "pendente",
                "datasheet_file": f"{slug}.pdf" # Assume a convenção
            }
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
                
        print(f"\n=======================================================")
        print(f"PROCESSANDO: {product_name} ({slug})")
        print(f"=======================================================")
        
        mercados, aplicacoes, equipamentos = parse_markdown_feeder(md_file)
        
        print(f"Extrato Feeder -> Mercados: {len(mercados)} | Aplicações: {len(aplicacoes)} | Equipamentos: {len(equipamentos)}")
        
        # Chama a inteligência artificial para gerar o restante, injetando os dados do feeder
        ok, erros = generate_lpp_via_gemini(
            slug, 
            feeder_mercados=mercados, 
            feeder_aplicacoes=aplicacoes, 
            feeder_equipamentos=equipamentos
        )
        
        if ok:
            print(f"[SUCESSO] Produto {slug} integrado e gerado. JSON salvo em gerador/dados/")
        else:
            print(f"[FALHA] Produto {slug} falhou na validação de IA.")
            
        if args.test_one:
            print("\n[!] Modo --test-one ativado. Parando após o primeiro produto.")
            break

if __name__ == "__main__":
    main()
