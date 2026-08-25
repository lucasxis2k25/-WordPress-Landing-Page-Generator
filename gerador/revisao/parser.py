# -*- coding: utf-8 -*-
"""
Parser Estruturado de Markdown para o Sistema de Revisão — Demo Store
Interpreta o Markdown e transforma em objetos Product, Section e Block.
"""
import re
import os
import unicodedata
from typing import List, Dict, Any, Optional
from .models import Product, Section, Block, BlockStatus, ProductStatus

def slugify(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text.lower()).strip()
    return re.sub(r'[-\s]+', '-', text)

class MarkdownProductParser:
    """
    Parser que converte arquivos .md de mapeamento ou landing page
    em uma árvore estruturada de Produto -> Seções -> Blocos Independentes.
    """

    @classmethod
    def parse_file(cls, filepath: str, lote: str = "Lote 001") -> Product:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        filename = os.path.basename(filepath)
        return cls.parse_content(content, source_file=filename, lote=lote)

    @classmethod
    def parse_content(cls, markdown_text: str, source_file: str = "", lote: str = "Lote 001") -> Product:
        lines = markdown_text.splitlines()
        
        # 1. Extração de Metadados Principais (Nome, SKU, Família, etc.)
        nome_produto = ""
        sku = ""
        familia = ""
        volume_elegivel = ""
        clientes_elegiveis = ""
        
        # Detecta primeiro título H1
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("# "):
                raw_title = line_str[2:].strip()
                # Limpa padrões como "MAPEAMENTO TÉCNICO E CURVAS ABC — PRODUTO `VENT. FF/2-146 P 220V`"
                if "PRODUTO" in raw_title.upper():
                    m_prod = re.search(r"PRODUTO\s*[`*]?([^`*\n]+)[`*]?", raw_title, re.IGNORECASE)
                    if m_prod:
                        raw_title = m_prod.group(1).strip()
                elif "—" in raw_title or "–" in raw_title:
                    parts = re.split(r"[—–]", raw_title)
                    if len(parts) >= 2 and ("MAPEAMENTO" in parts[0] or "DOCUMENTO" in parts[0]):
                        raw_title = parts[-1].strip().strip("`*# ")
                
                nome_produto = raw_title.replace("`", "").strip()
                break
        
        if not nome_produto:
            nome_produto = source_file.replace(".md", "").replace("_", " ") if source_file else "Produto Sem Nome"

        # Formatação e padronização amigável de nomes conhecidos
        if "A17251" in nome_produto.upper() or "17251" in source_file:
            nome_produto = "Micro Ventilador 172 mm - A17251VBHBL"
            sku = "A17251VBHBL"
        elif "146" in nome_produto.upper() and ("FF" in nome_produto.upper() or "P-FF" in nome_produto.upper() or "146" in source_file):
            nome_produto = "Ventilador Centrífugo 146 mm - P-FF 2-146 P 220V"
            sku = "P-FF 2-146 P"
        elif "A25089" in nome_produto.upper() or "25089" in source_file:
            nome_produto = "Micro Ventilador 250 mm - A25089VBHBL"
            sku = "A25089VBHBL"

        # Extrai SKU se ainda vazio
        if not sku:
            sku_match = re.search(r"\b([A-Z0-9]+(?:[/-][A-Z0-9]+)+|\b[A-Z]\d{4,6}[A-Z0-9-]*)\b", nome_produto)
            if sku_match:
                sku = sku_match.group(1).strip()
            else:
                sku = nome_produto.split()[-1] if nome_produto else "SKU"

        # Procura campos de cabeçalho tipo **Família Técnica:**
        for line in lines[:30]:
            if "Família Técnica:" in line or "Familia Tecnica:" in line:
                m = re.search(r"Fam[ií]lia T[eé]cnica:\s*`?([^`*\n]+)`?", line, re.IGNORECASE)
                if m: familia = m.group(1).strip()
            elif "Volume Elegível" in line or "Volume Elegivel" in line:
                m = re.search(r"Volume Eleg[ií]vel[^:]*:\s*`?([^`*\n]+)`?", line, re.IGNORECASE)
                if m: volume_elegivel = m.group(1).strip()
            elif "Clientes Elegíveis" in line or "Clientes Elegiveis" in line:
                m = re.search(r"Clientes Eleg[ií]veis[^:]*:\s*`?([^`*\n]+)`?", line, re.IGNORECASE)
                if m: clientes_elegiveis = m.group(1).strip()
            elif "SKU Limpo" in line or "SKU:" in line:
                m = re.search(r"SKU[^:]*:\s*`?([^`*\n]+)`?", line, re.IGNORECASE)
                if m: sku = m.group(1).strip()

        slug = slugify(nome_produto)
        if not slug:
            slug = slugify(source_file.replace(".md", ""))

        # 2. Decomposição em Seções e Blocos
        sections: List[Section] = []
        current_section: Optional[Section] = None
        current_blocks: List[Block] = []
        
        # Estruturas para acumular texto
        raw_sections = cls._split_into_raw_sections(lines)
        
        sec_order = 1
        for raw_sec in raw_sections:
            sec_title = raw_sec["title"]
            sec_type = cls._classify_section_type(sec_title)
            sec_lines = raw_sec["lines"]
            
            blocks = cls._parse_blocks_from_section(sec_type, sec_title, sec_lines)
            if blocks:
                section_obj = Section(
                    id=f"sec-{sec_type}-{sec_order}",
                    tipo=sec_type,
                    titulo=sec_title,
                    ordem=sec_order,
                    blocks=blocks
                )
                sections.append(section_obj)
                sec_order += 1

        # Se não encontrou seções estruturadas (ex: arquivo de mapeamento técnico), cria as seções padrão Demo Store
        if not sections:
            sections = cls._fallback_sections_from_text(lines, nome_produto, sku)

        product = Product(
            id=slug,
            slug=slug,
            nome=nome_produto,
            sku=sku,
            modelo=sku,
            categoria=familia or "Ventilação Industrial",
            familia=familia,
            volume_elegivel=volume_elegivel,
            clientes_elegiveis=clientes_elegiveis,
            source_file=source_file,
            lote=lote,
            status=ProductStatus.IMPORTADO.value,
            sections=sections,
            deleted_blocks=[],
            history=[{
                "timestamp": "Agora",
                "acao": "Importação de Arquivo",
                "detalhes": f"Arquivo {source_file} importado com {sum(len(s.blocks) for s in sections)} blocos detectados.",
                "bloco_id": ""
            }]
        )
        return product

    @classmethod
    def _split_into_raw_sections(cls, lines: List[str]) -> List[Dict[str, Any]]:
        raw_sections = []
        current_title = "Hero / Resumo Geral"
        current_lines = []
        
        for line in lines:
            if line.strip().startswith("## "):
                if current_lines or current_title != "Hero / Resumo Geral":
                    raw_sections.append({
                        "title": current_title,
                        "lines": current_lines
                    })
                current_title = line.strip()[3:].strip()
                current_lines = []
            else:
                current_lines.append(line)
                
        if current_lines:
            raw_sections.append({
                "title": current_title,
                "lines": current_lines
            })
        return raw_sections

    @classmethod
    def _classify_section_type(cls, title: str) -> str:
        t = title.upper()
        if "HERO" in t or "RESUMO" in t or "DESCRIÇÃO" in t or "DESCRICAO" in t:
            return "descricao"
        elif "APLICAÇÕES" in t or "APLICACOES" in t or "APLICAÇÃO" in t:
            return "aplicacoes"
        elif "EQUIPAMENTOS" in t or "ONDE USAR" in t or "ONDE O" in t:
            return "equipamentos"
        elif "ESPECIFICAÇÕES" in t or "ESPECIFICACOES" in t or "SPECS" in t:
            return "especificacoes"
        elif "MERCADO" in t or "SEGMENTO" in t or "SETORES" in t:
            return "mercado"
        elif "BENEFÍCIOS" in t or "BENEFICIOS" in t:
            return "beneficios"
        elif "DIFERENCIAIS" in t or "DIFERENCIAL" in t:
            return "diferenciais"
        elif "FAQ" in t or "PERGUNTAS" in t or "DÚVIDAS" in t:
            return "faq"
        elif "ALERTA" in t or "ATENÇÃO" in t:
            return "alerta"
        elif "TABELA" in t or "CURVA ABC" in t or "CLIENTES" in t:
            return "tabela_abc"
        return "geral"

    @classmethod
    def _parse_blocks_from_section(cls, sec_type: str, sec_title: str, lines: List[str]) -> List[Block]:
        blocks: List[Block] = []
        text_content = "\n".join(lines).strip()
        if not text_content:
            return []

        # 1. Seção de Subtítulos H3 (### Título)
        h3_splits = re.split(r"\n(?=###\s+)", "\n" + text_content)
        if len(h3_splits) > 1 and any(s.strip().startswith("###") for s in h3_splits):
            order = 1
            for split_part in h3_splits:
                part = split_part.strip()
                if not part:
                    continue
                if part.startswith("### "):
                    part_lines = part.splitlines()
                    b_title = part_lines[0][4:].strip()
                    b_content = "\n".join(part_lines[1:]).strip()
                else:
                    b_title = f"{sec_title} - Introdução"
                    b_content = part
                
                blocks.append(Block(
                    id=f"{sec_type}-{order:02d}",
                    tipo=sec_type,
                    titulo=b_title,
                    conteudo=b_content,
                    ordem=order
                ))
                order += 1
            return blocks

        # 2. Seção de Tabela Markdown (ex: Especificações ou Curva ABC)
        if "|" in text_content and "-|-" in text_content or "| :-" in text_content:
            table_lines = [l.strip() for l in lines if l.strip().startswith("|")]
            if len(table_lines) >= 3:
                # Trata como bloco de tabela estruturada
                blocks.append(Block(
                    id=f"{sec_type}-tabela-01",
                    tipo=sec_type,
                    titulo=f"Tabela de {sec_title}",
                    conteudo="\n".join(table_lines),
                    ordem=1,
                    metadata={"formato": "tabela"}
                ))
                # Textos ao redor da tabela
                non_table = [l for l in lines if not l.strip().startswith("|") and l.strip()]
                if non_table:
                    blocks.append(Block(
                        id=f"{sec_type}-obs-02",
                        tipo=sec_type,
                        titulo=f"Observações - {sec_title}",
                        conteudo="\n".join(non_table).strip(),
                        ordem=2
                    ))
                return blocks

        # 3. Seção em Lista com Marcadores (- Item ou * Item)
        list_items = [l.strip()[2:].strip() for l in lines if l.strip().startswith("- ") or l.strip().startswith("* ")]
        if len(list_items) >= 2 and sec_type in ("diferenciais", "mercado", "hero_checklist"):
            for i, item in enumerate(list_items, start=1):
                tit = f"Item {i:02d}"
                cont = item
                if ":" in item:
                    p = item.split(":", 1)
                    tit = p[0].strip()
                    cont = p[1].strip()
                blocks.append(Block(
                    id=f"{sec_type}-{i:02d}",
                    tipo=sec_type,
                    titulo=tit,
                    conteudo=cont,
                    ordem=i
                ))
            return blocks

        # 4. Parágrafos Normais (Hero / Descrição / Texto Geral)
        paras = [p.strip() for p in text_content.split("\n\n") if p.strip()]
        if len(paras) > 1:
            for i, p in enumerate(paras, start=1):
                blocks.append(Block(
                    id=f"{sec_type}-{i:02d}",
                    tipo=sec_type,
                    titulo=f"Parágrafo {i:02d}",
                    conteudo=p,
                    ordem=i
                ))
        else:
            blocks.append(Block(
                id=f"{sec_type}-01",
                tipo=sec_type,
                titulo=sec_title,
                conteudo=text_content,
                ordem=1
            ))

        return blocks

    @classmethod
    def _fallback_sections_from_text(cls, lines: List[str], nome: str, sku: str) -> List[Section]:
        """Cria seções básicas caso o documento seja texto bruto não-seccionado."""
        return [
            Section(
                id="sec-descricao-1",
                tipo="descricao",
                titulo="Descrição do Produto",
                ordem=1,
                blocks=[
                    Block(
                        id="desc-01",
                        tipo="descricao",
                        titulo="Resumo Técnico",
                        conteudo=f"O {nome} é um componente industrial de alta precisão projetado para regime contínuo.",
                        ordem=1
                    )
                ]
            )
        ]
