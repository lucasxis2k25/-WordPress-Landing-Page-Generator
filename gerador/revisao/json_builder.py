# -*- coding: utf-8 -*-
"""
Construtor de JSON Final e Payload ACF a partir dos Blocos Aprovados — Demo Store
Garante que apenas blocos com status APROVADO e NÃO EXCLUÍDOS entrem no arquivo final.
"""
import json
import os
import sys
from typing import Dict, Any, List
from .models import Product, BlockStatus

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from renderizador import (
    render_resumo_tecnico,
    render_especificacoes,
    render_aplicacoes_categoria,
    render_aplicacoes_equipamento,
    render_mercado,
    render_beneficios,
    render_diferenciais,
    render_downloads,
    render_faq,
    render_alerta,
    render_schema_product,
    render_schema_faq
)

def build_product_json(product: Product) -> Dict[str, Any]:
    """
    Constrói a estrutura JSON canônica de dados do produto.
    Filtra estritamente apenas os blocos com status APROVADO.
    """
    resumo_paras = []
    hero_checklist = []
    aplicacoes_cards = []
    equipamentos_cards = []
    beneficios_cards = []
    diferenciais_list = []
    mercados_list = []
    faq_items = []
    especificacoes_list = []
    alerta_tecnico = ""

    for section in product.sections:
        for block in section.blocks:
            if block.status != BlockStatus.APROVADO.value:
                continue

            tipo = block.tipo.lower()
            if tipo in ("descricao", "hero"):
                resumo_paras.append(block.conteudo)
            elif tipo == "aplicacoes":
                aplicacoes_cards.append({
                    "id": block.id,
                    "titulo": block.titulo,
                    "descricao": block.conteudo
                })
            elif tipo == "equipamentos":
                equipamentos_cards.append({
                    "id": block.id,
                    "titulo": block.titulo,
                    "descricao": block.conteudo
                })
            elif tipo == "beneficios":
                beneficios_cards.append({
                    "id": block.id,
                    "titulo": block.titulo,
                    "descricao": block.conteudo
                })
            elif tipo == "diferenciais":
                diferenciais_list.append(block.conteudo)
            elif tipo == "mercado":
                mercados_list.append(block.conteudo)
            elif tipo == "faq":
                faq_items.append({
                    "pergunta": block.titulo,
                    "resposta": block.conteudo
                })
            elif tipo == "alerta":
                alerta_tecnico = block.conteudo
            elif tipo == "especificacoes":
                if block.metadata.get("formato") == "tabela":
                    # Converte tabela Markdown em lista de specs
                    for line in block.conteudo.splitlines():
                        if "|" in line and not line.strip().startswith("|-") and not line.strip().startswith("| :-"):
                            cols = [c.strip().strip("*") for c in line.split("|") if c.strip()]
                            if len(cols) >= 2 and "atributo" not in cols[0].lower() and "informação" not in cols[0].lower():
                                especificacoes_list.append({
                                    "atributo": cols[0],
                                    "valor": cols[1],
                                    "confianca": "100%",
                                    "fonte": "Datasheet Oficial Sell-Parts"
                                })

    resumo_texto = "\n\n".join(resumo_paras) if resumo_paras else f"O {product.nome} é um equipamento industrial de alta confiabilidade."

    clean_json = {
        "slug": product.slug,
        "nome": product.nome,
        "sku": product.sku,
        "categoria": product.categoria,
        "familia": product.familia,
        "resumo_tecnico": resumo_texto,
        "hero_checklist": [
            "Pronta Entrega Sell-Parts",
            "Mancais com Rolamentos Blindados",
            "Garantia e Suporte de Engenharia"
        ],
        "especificacoes": especificacoes_list,
        "beneficios": beneficios_cards,
        "diferenciais": diferenciais_list,
        "mercados": mercados_list,
        "aplicacoes_categoria": {
            "titulo": f"Aplicações do {product.nome}",
            "intro": "Equipamento desenvolvido para ventilação e movimentação de ar em processos e sistemas industriais.",
            "cards": aplicacoes_cards
        },
        "aplicacoes_equipamento": {
            "titulo": f"Onde usar o {product.sku}",
            "intro": "Projetado para integração em equipamentos industriais que demandam confiabilidade térmica.",
            "cards": equipamentos_cards
        },
        "faq": faq_items,
        "alerta_tecnico": alerta_tecnico or f"Antes da instalação ou substituição do modelo {product.sku}, confira na etiqueta os parâmetros de tensão, corrente e furação de fixação."
    }
    return clean_json

def build_acf_payload(product: Product) -> Dict[str, Any]:
    """
    Renderiza os blocos HTML (.sp-) e Schemas JSON-LD a partir dos blocos aprovados.
    """
    clean_data = build_product_json(product)

    specs_confirmadas = [
        s for s in clean_data.get("especificacoes", [])
        if s.get("confianca") == "100%" and s.get("valor") is not None
    ]

    html_app_cat = render_aplicacoes_categoria(clean_data)
    html_app_eq = render_aplicacoes_equipamento(clean_data)
    html_mercado = render_mercado(clean_data)

    payload = {
        "slug": clean_data["slug"],
        "nome": clean_data["nome"],
        "sku": clean_data["sku"],
        "acf": {
            "sp_resumo_tecnico": render_resumo_tecnico(clean_data),
            "sp_especificacoes": render_especificacoes(specs_confirmadas, clean_data.get("alerta_tabela", "")),
            "sp_aplicacoes": html_app_cat,
            "Aplicacoes_equipamentos": html_app_eq,
            "aplicacoes_equipamentos": html_app_eq,
            "sp_aplicacoes_equipamentos": html_app_eq,
            "sp_mercado": html_mercado,
            "sp_beneficios": render_beneficios(clean_data.get("beneficios", [])),
            "sp_diferenciais": render_diferenciais(clean_data.get("diferenciais", [])),
            "sp_downloads": render_downloads(clean_data["nome"]),
            "sp_faq": render_faq(clean_data.get("faq", [])),
            "sp_alerta_tecnico": render_alerta(clean_data.get("alerta_tecnico", ""))
        },
        "schema_jsonld": {
            "product": render_schema_product(clean_data),
            "faq": render_schema_faq(clean_data.get("faq", []))
        }
    }
    return payload
