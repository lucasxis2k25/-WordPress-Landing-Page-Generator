# -*- coding: utf-8 -*-
"""
Script para injetar as informações literais do Alimentador (Mercado, Aplicações, Equipamentos)
diretamente nos JSONs gerados pela IA, garantindo 100% de precisão taxônomica.
"""
import os
import sys
import glob
import re
import json

# Adiciona diretórios ao sys.path
GERADOR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(GERADOR_DIR)
DADOS_DIR = os.path.join(GERADOR_DIR, "dados")
FEEDER_DIR = os.path.join(PROJ_DIR, "mapeamento de produto", "outputs", "mapeamento_produtos")

def parse_markdown_feeder(md_path):
    """Extrai os itens estruturados do Markdown gerado pelo Feeder."""
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

def mesclar_dados(json_path, mercados, aplicacoes, equipamentos):
    """Sobreescreve as seções no JSON."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. MERCADOS
    if mercados:
        data['mercados'] = mercados

    # 2. APLICAÇÕES
    if aplicacoes:
        if 'aplicacoes_categoria' not in data:
            data['aplicacoes_categoria'] = {"titulo": "Aplicações Técnicas", "intro": "Principais aplicações operacionais", "cards": []}
        
        # Mantém a estrutura, substituindo os títulos e esvaziando a descrição (para não misturar com invenção da IA)
        cards_app = []
        for app in aplicacoes:
            cards_app.append({
                "titulo": app,
                "descricao": app # Como o feeder traz apenas o nome, usamos como descrição seca
            })
        data['aplicacoes_categoria']['cards'] = cards_app

    # 3. EQUIPAMENTOS (Onde Usar)
    if equipamentos:
        if 'aplicacoes_equipamento' not in data:
            data['aplicacoes_equipamento'] = {"titulo": "Equipamentos de Instalação", "intro": "Onde o produto é instalado", "cards": []}
        
        cards_eq = []
        for eq in equipamentos:
            cards_eq.append({
                "titulo": eq,
                "descricao": eq
            })
        data['aplicacoes_equipamento']['cards'] = cards_eq

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    if not os.path.exists(FEEDER_DIR):
        print(f"Diretório do feeder não encontrado: {FEEDER_DIR}")
        return
        
    md_files = glob.glob(os.path.join(FEEDER_DIR, "*.md"))
    
    sucessos = 0
    for md_file in md_files:
        filename = os.path.basename(md_file)
        if filename.upper() == "README.MD":
            continue
            
        with open(md_file, 'r', encoding='utf-8') as f:
            first_line = f.readline()
        
        match = re.search(r'`(.*?)`', first_line)
        if not match:
            continue
            
        product_name = match.group(1)
        slug = formatar_slug(product_name)
        
        json_path = os.path.join(DADOS_DIR, f"{slug}.json")
        if not os.path.exists(json_path):
            print(f"[PULADO] Arquivo JSON gerado pela IA não encontrado para {slug}")
            continue
            
        mercados, aplicacoes, equipamentos = parse_markdown_feeder(md_file)
        mesclar_dados(json_path, mercados, aplicacoes, equipamentos)
        print(f"[OK] Injetado dados literais do Feeder no produto {slug}")
        sucessos += 1
        
    print(f"\nFinalizado! {sucessos} produtos foram 100% atualizados com os dados do Alimentador.")

if __name__ == "__main__":
    main()
