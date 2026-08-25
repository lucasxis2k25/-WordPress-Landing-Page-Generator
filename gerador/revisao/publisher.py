# -*- coding: utf-8 -*-
"""
Publicador WordPress Integrado ao Fluxo de Revisão — Demo Store
"""
import os
import sys
import json
from typing import Dict, Any, Tuple
from .models import Product, ProductStatus, BlockStatus
from .json_builder import build_acf_payload

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
AUTOMACAO_DIR = os.path.join(BASE_DIR, "automacao")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, AUTOMACAO_DIR)

from automacao.publicar_wordpress import update_product_acf

def publicar_produto_revisado(product: Product, output_dir: Optional[str] = None) -> Tuple[bool, str]:
    """
    Executa a publicação segura no WordPress apenas se o produto estiver devidamente validado.
    """
    # 1. Checagem de segurança
    metricas = product.metricas_blocos()
    if metricas["pendentes"] > 0:
        return False, f"Bloqueado: Existem {metricas['pendentes']} blocos pendentes de aprovação."

    if metricas["revisao"] > 0:
        return False, f"Bloqueado: Existem {metricas['revisao']} blocos marcados para revisão."

    # 2. Gera os arquivos ACF
    payload = build_acf_payload(product)
    
    out_dir = output_dir or os.path.join(BASE_DIR, "output")
    os.makedirs(out_dir, exist_ok=True)
    
    acf_json_path = os.path.join(out_dir, f"{product.slug}_acf.json")
    with open(acf_json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 3. Dispara a publicação na API
    try:
        sucesso = update_product_acf(product.slug)
        if sucesso:
            product.status = ProductStatus.PUBLICADO.value
            product.log_acao("Publicação WordPress", f"Versão v{product.version} publicada com sucesso.")
            return True, f"Produto '{product.nome}' publicado com sucesso no WordPress!"
        else:
            return False, "Falha na sincronização via REST API com o WordPress. Verifique logs."
    except Exception as e:
        return False, f"Erro inesperado durante publicação: {str(e)}"
