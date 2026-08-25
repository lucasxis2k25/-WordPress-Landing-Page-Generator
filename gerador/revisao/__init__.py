# -*- coding: utf-8 -*-
"""
Módulo de Revisão Técnica Estruturada por Blocos — Demo Store B2B
"""
from .models import Block, Section, Product, BlockStatus, ProductStatus
from .parser import MarkdownProductParser
from .storage import ReviewStorage
from .json_builder import build_product_json, build_acf_payload

__all__ = [
    "Block",
    "Section",
    "Product",
    "BlockStatus",
    "ProductStatus",
    "MarkdownProductParser",
    "ReviewStorage",
    "build_product_json",
    "build_acf_payload",
]
