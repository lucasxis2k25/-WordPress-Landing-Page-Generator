# -*- coding: utf-8 -*-
"""Reexporta helpers de texto a partir de regras.py (fonte única)."""

from regras import (
    corrigir_separacao_mercado_aplicacoes,
    gerar_aplicacoes_padrao,
    gerar_texto_mercado,
    sanitizar_produto,
)

__all__ = [
    "corrigir_separacao_mercado_aplicacoes",
    "gerar_aplicacoes_padrao",
    "gerar_texto_mercado",
    "sanitizar_produto",
]
