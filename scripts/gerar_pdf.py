# -*- coding: utf-8 -*-
"""
Gerador de Documento Executivo de Apresentacao e Validacao do Projeto de Landing Pages B2B
Demo Store - Catalogo Digital Industrial 2026
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os

class DocumentoExecutivoProjetoPDF(FPDF):
    """PDF Executivo Corporativo para Apresentacao a Diretoria e Gestao."""

    def header(self):
        if self.page_no() > 1:
            self.set_fill_color(15, 23, 42) # Slate 900
            self.rect(0, 0, 210, 14, 'F')
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(255, 255, 255)
            self.set_xy(10, 3)
            self.cell(0, 8, 'Demo Store  |  PROJETO DE REFORMULAÇÃO DO CATÁLOGO B2B - PROPOSTA EXECUTIVA', new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.set_font('Helvetica', '', 8)
            self.set_text_color(148, 163, 184)
            self.cell(0, 8, 'DOCUMENTO DE VALIDAÇÃO INTERNA', align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(6)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-12)
            self.set_font('Helvetica', '', 8)
            self.set_text_color(148, 163, 184)
            self.cell(110, 8, 'Demo Store Industria e Comercio - Proposta de Engenharia e Marketing Digital', align='L')
            self.cell(0, 8, f'Pagina {self.page_no()}/{{nb}}', align='R')

    def draw_section_header(self, title, subtitle=""):
        self.ln(4)
        self.set_fill_color(37, 99, 235) # Blue 600
        self.rect(10, self.get_y(), 4, 14, 'F')
        self.set_xy(17, self.get_y())
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(15, 23, 42)
        self.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if subtitle:
            self.set_xy(17, self.get_y())
            self.set_font('Helvetica', '', 8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 5, subtitle, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def draw_card(self, title, content_dict):
        self.set_fill_color(248, 250, 252)
        self.set_draw_color(226, 232, 240)
        y_start = self.get_y()
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(30, 41, 59)
        
        height = 10 + len(content_dict) * 6
        if y_start + height > self.h - 20:
            self.add_page()
            y_start = self.get_y()

        self.rect(10, y_start, 190, height, 'FD')
        self.set_xy(14, y_start + 3)
        self.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.set_font('Helvetica', '', 8)
        for k, v in content_dict.items():
            self.set_x(14)
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(71, 85, 105)
            self.cell(42, 5.5, f"{k}:")
            self.set_font('Helvetica', '', 8)
            self.set_text_color(15, 23, 42)
            self.cell(0, 5.5, str(v), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)

    def draw_badge(self, text, bg_rgb=(37, 99, 235), text_rgb=(255, 255, 255)):
        w = self.get_string_width(text) + 8
        if self.get_x() + w > 195:
            self.ln(7)
            self.set_x(10)
        x = self.get_x()
        y = self.get_y()
        self.set_fill_color(*bg_rgb)
        self.rect(x, y, w, 6, 'F')
        self.set_xy(x, y)
        self.set_font('Helvetica', 'B', 7.5)
        self.set_text_color(*text_rgb)
        self.cell(w, 6, text, align='C', new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_x(x + w + 3)

    def draw_table(self, headers, data, col_widths):
        self.set_font('Helvetica', 'B', 8)
        self.set_fill_color(15, 23, 42)
        self.set_text_color(255, 255, 255)
        
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=0, fill=True, align='C')
        self.ln()

        self.set_font('Helvetica', '', 8)
        fill = False
        for row in data:
            if self.get_y() + 8 > self.h - 20:
                self.add_page()
                self.set_font('Helvetica', 'B', 8)
                self.set_fill_color(15, 23, 42)
                self.set_text_color(255, 255, 255)
                for i, h in enumerate(headers):
                    self.cell(col_widths[i], 7, h, border=0, fill=True, align='C')
                self.ln()
                self.set_font('Helvetica', '', 8)

            self.set_fill_color(241, 245, 249) if fill else self.set_fill_color(255, 255, 255)
            x_start = self.get_x()
            y_start = self.get_y()
            
            max_lines = 1
            for i, cell in enumerate(row):
                lines = len(str(cell)) // max(1, int(col_widths[i] / 2.2)) + 1
                if lines > max_lines:
                    max_lines = lines
            row_h = max(7, max_lines * 5)

            self.rect(x_start, y_start, sum(col_widths), row_h, 'F')
            self.set_draw_color(226, 232, 240)
            self.rect(x_start, y_start, sum(col_widths), row_h, 'D')

            for i, cell in enumerate(row):
                x = x_start + sum(col_widths[:i])
                self.set_xy(x + 1, y_start + 1)
                self.set_text_color(30, 41, 59)
                
                if str(cell) == "100%" or str(cell) == "Confirmado" or "[x]" in str(cell):
                    self.set_text_color(22, 101, 52)
                    self.set_font('Helvetica', 'B', 8)
                elif str(cell) == "0%" or str(cell) == "Nao Encontrado":
                    self.set_text_color(185, 28, 28)
                    self.set_font('Helvetica', 'B', 8)

                self.multi_cell(col_widths[i] - 2, 4.5, str(cell))
                self.set_font('Helvetica', '', 8)

            self.set_xy(x_start, y_start + row_h)
            fill = not fill
        self.ln(4)

def build_pdf():
    pdf = DocumentoExecutivoProjetoPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)

    # =========================================================================
    # CAPA EXECUTIVA
    # =========================================================================
    pdf.add_page()
    
    # Header Banner Dark
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 28, 'F')
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(12, 10)
    pdf.cell(0, 8, 'Demo Store  |  INDUSTRIAL B2B SOLUTIONS', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(18)

    # Status Badge Cover
    pdf.set_x(10)
    pdf.draw_badge('DOCUMENTO DE VALIDAÇÃO DO PROJETO DE LANDING PAGES', (234, 88, 12), (255, 255, 255))
    pdf.draw_badge('STATUS: EM VALIDAÇÃO EXECUTIVA', (15, 23, 42), (255, 255, 255))
    pdf.ln(12)

    # Title
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 9, 'Plano Estratégico Executivo:\nModernização do Catálogo Digital B2B')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(0, 7, 'Arquitetura Reutilizavel, SEO/GEO de Alta Performance e Rigor Tecnico', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Metadata Card
    pdf.draw_card('DADOS DE APRESENTAÇÃO E SUBMISSÃO', {
        'Projeto': 'Reformulação Estratégica das Paginas de Produtos B2B (WordPress / Elementor)',
        'Escopo': '216 Produtos do Catalogo (Piloto Inicial: Top 3 Produtos Curva A)',
        'Data da Proposta': '24 de Julho de 2026',
        'Submetido por': 'Equipe de Inteligencia de Mercado e Engenharia Digital',
        'Destinatarios': 'Diretoria, Gestao Comercial, Marketing B2B, Equipe de Engenharia',
        'Status do Documento': 'EM VALIDAÇÃO EXECUTIVA (Aguardando Parecer para Entrada em Producao)'
    })

    # Summary Box
    pdf.set_fill_color(239, 246, 255)
    pdf.set_draw_color(191, 219, 254)
    y_res = pdf.get_y()
    pdf.rect(10, y_res, 190, 48, 'FD')
    pdf.set_xy(14, y_res + 4)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 6, 'SUMÁRIO EXECUTIVO DA PROPOSTA', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_x(14)
    pdf.set_font('Helvetica', '', 8.5)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(182, 4.8, 
        'Esta proposta apresenta a estrategia de modernizacao e padronizacao digital de todo o catalogo B2B da Demo Store. '
        'Substituiremos a estrutura de e-commerce generica por um Sistema de Landing Page Unico no WordPress/Elementor, '
        'escalavel para 216 produtos. O projeto elimina inferencias tecnicas sem comprovacao (Politica Zero Alucinacao), '
        'garante conformidade com engenharia de aplicacao e posiciona a Demo Store no topo dos motores de busca (SEO/GEO).')

    # =========================================================================
    # PAGINA 2: ESTRATÉGIA MACRO (PROBLEMA X SOLUÇÃO X RESULTADO)
    # =========================================================================
    pdf.add_page()
    pdf.draw_section_header('1. Diagnostico Estratégico e Visao Geral', 'Por que estamos reformulando todo o catalogo B2B da Demo Store')

    # 3 Cards: Problema -> Solucao -> Resultado
    w_card = 58
    y_top = pdf.get_y()

    # Box 1: Problema
    pdf.set_fill_color(254, 242, 242)
    pdf.set_draw_color(252, 165, 165)
    pdf.rect(10, y_top, w_card, 52, 'FD')
    pdf.set_xy(13, y_top + 3)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(153, 27, 27)
    pdf.cell(w_card - 6, 6, 'PROBLEMA ATUAL', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 7.5)
    pdf.set_text_color(79, 70, 229)
    prob_text = (
        '- Catalogo em formato e-commerce generico\n'
        '- Conteudo tecnico basico ou incompleto\n'
        '- Perda de vendas B2B por falta de dados\n'
        '- Baixa autoridade organica no Google\n'
        '- Ausencia de respostas estruturadas para IA (GEO)'
    )
    pdf.set_x(13)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(w_card - 6, 4.2, prob_text)

    # Box 2: Solucao
    pdf.set_fill_color(239, 246, 255)
    pdf.set_draw_color(147, 197, 253)
    pdf.rect(76, y_top, w_card, 52, 'FD')
    pdf.set_xy(79, y_top + 3)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(w_card - 6, 6, 'SOLUCÃO PROPOSTA', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    sol_text = (
        '- Single Product Template padronizado\n'
        '- Politica "Zero Inferencias Tecnicas"\n'
        '- Pagina orientada a orcamento PJ / B2B\n'
        '- SEO Semantico + Schema Product/FAQ\n'
        '- Design moderno estilo multinacional'
    )
    pdf.set_x(79)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(w_card - 6, 4.2, sol_text)

    # Box 3: Resultado
    pdf.set_fill_color(240, 253, 244)
    pdf.set_draw_color(134, 239, 172)
    pdf.rect(142, y_top, w_card, 52, 'FD')
    pdf.set_xy(145, y_top + 3)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(w_card - 6, 6, 'RESULTADO ESPERADO', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    res_text = (
        '- Aumento expressivo no tráfego organico\n'
        '- Maior conversao de leads qualificados PJ\n'
        '- Reducao de devolucoes (RMA) por dados errados\n'
        '- Posicionamento de lideranca tecnica B2B\n'
        '- Escalabilidade para 216 produtos'
    )
    pdf.set_x(145)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(w_card - 6, 4.2, res_text)

    pdf.set_y(y_top + 58)

    # Comparativo Antes x Depois
    pdf.draw_section_header('2. Comparativo Estratégico: Hoje no Site x Nova Landing Page B2B', 'Diferencas praticas entre o modelo atual e o novo padrao')

    before_after = [
        ['Descricao de Produto', 'Texto simples e basico de e-commerce', 'Hero comercial + Copy B2B orientada a aplicacao'],
        ['SEO & Indexacao', 'Tagging basico do WooCommerce', 'SEO Semantico completo + Schema Product & FAQPage'],
        ['Confiabilidade Tecnica', 'Dados misturados ou estimados sem fonte', 'Politica Zero Inferencias (Transparencia 100%/0%)'],
        ['Engenharia de Reposicao', 'Inexistente (Risco de compra errada)', 'Checklist de 8 Parametros Obrigatorios para validacao'],
        ['Suporte a Instalacao', 'Sem informacoes eletricas', 'Orientacao expressa de fechamento na placa do motor'],
        ['Foco Comercial', 'Varejo / Botao "Comprar" generico', 'B2B / Orcamento PJ em Lote + Faturamento CNPJ']
    ]
    pdf.draw_table(['Dimensao do Projeto', 'Modelo Atual no Site', 'Nova Landing Page B2B (Demo Store)'], before_after, [40, 75, 75])

    # =========================================================================
    # PAGINA 3: ARQUITETURA DE ESCALABILIDADE (SINGLE PRODUCT TEMPLATE)
    # =========================================================================
    pdf.add_page()
    pdf.draw_section_header('3. Arquitetura do Sistema e Escalabilidade', 'Como o investimento se multiplica por 216 produtos com custo reduzido')

    pdf.draw_card('ARQUITETURA REUTILIZÁVEL NO WORDPRESS + ELEMENTOR PRO', {
        'Conceito Tecnico': 'SINGLE PRODUCT TEMPLATE UNICO no Elementor Pro',
        'Estilização Central': 'Estilos CSS globais isolados com prefixo .sp- (Sem conflitos com o tema)',
        'Componentes Fixos': 'Hero, Beneficios, Ficha Tecnica, Checklist, FAQ, Schemas, CTAs (Layout 100% Fixo)',
        'Conteudo Variavel': 'Apenas os textos, especificacoes e FAQs especificos de cada produto (Preenchimento em Lote)',
        'Vantagem Operacional': 'Uma alteracao visual no Template reflete INSTANTANEAMENTE nos 216 produtos do catalogo.',
        'Economia de Recursos': 'Zero necessidade de desenhar ou codificar 216 paginas individuais.'
    })

    # Diagrama de Escalabilidade
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, 'Diagrama Visual da Arquitetura do Sistema:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    y_diag = pdf.get_y()
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(55, y_diag, 100, 12, 'F')
    pdf.set_xy(55, y_diag + 3)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(100, 6, 'SINGLE PRODUCT TEMPLATE (ELEMENTOR PRO)', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Linhas conectoras
    pdf.set_draw_color(37, 99, 235)
    pdf.set_line_width(0.8)
    pdf.line(105, y_diag + 12, 105, y_diag + 20)
    pdf.line(35, y_diag + 20, 175, y_diag + 20)
    pdf.line(35, y_diag + 20, 35, y_diag + 25)
    pdf.line(105, y_diag + 20, 105, y_diag + 25)
    pdf.line(175, y_diag + 20, 175, y_diag + 25)

    y_boxes = y_diag + 25
    # Box Prod 1
    pdf.set_fill_color(239, 246, 255)
    pdf.set_draw_color(147, 197, 253)
    pdf.rect(10, y_boxes, 50, 16, 'FD')
    pdf.set_xy(10, y_boxes + 2)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(50, 4, 'Produto Piloto 1', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 7.5)
    pdf.cell(50, 4, 'MicroVent. A25089VBHBL', align='C')

    # Box Prod 2
    pdf.set_fill_color(239, 246, 255)
    pdf.rect(80, y_boxes, 50, 16, 'FD')
    pdf.set_xy(80, y_boxes + 2)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(50, 4, 'Produto Piloto 2', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 7.5)
    pdf.cell(50, 4, 'Exaustor FS 4-500 ET', align='C')

    # Box Prod 3...216
    pdf.set_fill_color(240, 253, 244)
    pdf.set_draw_color(134, 239, 172)
    pdf.rect(150, y_boxes, 50, 16, 'FD')
    pdf.set_xy(150, y_boxes + 2)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(50, 4, 'Demais 213 Produtos', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 7.5)
    pdf.cell(50, 4, 'Alimentacao em Lote', align='C')

    pdf.set_y(y_boxes + 22)

    # =========================================================================
    # PAGINA 4: ESTRUTURA VISUAL DO WIREFRAME E FLUXO DE CONVERSÃO
    # =========================================================================
    pdf.draw_section_header('4. Wireframe Visual e Arquitetura de Bloco da Landing Page', 'Sequencia exata do funil visual de conversao')

    wireframe_blocks = [
        ['1. HERO SECTION', 'Titulo H1 + Codigo SKU + Badges B2B + Botoes CTA Cotacao PJ e Ficha Tecnica'],
        ['2. BENEFÍCIOS B2B', '3 Cards destacados: Pronta Entrega, Faturamento Corporativo CNPJ, Garantia Demo Store'],
        ['3. FICHA TÉCNICA TRANSPARENTE', 'Tabela Zebrada mostrando estritamente dados confirmados (100% Confiabilidade)'],
        ['4. CHECKLIST DE REPOSIÇÃO', 'Alerta de Engenharia: Lista de 8 parametros para checagem previa de equivalencia'],
        ['5. ORIENTAÇÃO DE INSTALAÇÃO', 'Instrucao tecnica orientando checagem de fechamento na placa do motor'],
        ['6. FAQ ESTRUTURADO (JSON-LD)', 'Perguntas Frequentes ativando snippets no Google e respostas para Inteligencias Artificiais'],
        ['7. CTA FINAL CORPORATIVO', 'Banner de contato direto via WhatsApp / Telefone com equipe de Engenharia da Demo Store']
    ]

    for label, desc in wireframe_blocks:
        y_wf = pdf.get_y()
        pdf.set_fill_color(15, 23, 42)
        pdf.rect(10, y_wf, 45, 7, 'F')
        pdf.set_xy(10, y_wf + 1)
        pdf.set_font('Helvetica', 'B', 7.5)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(45, 5, label, align='C')
        
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(57, y_wf, 143, 7, 'FD')
        pdf.set_xy(59, y_wf + 1)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(140, 5, desc)
        pdf.ln(8)

    # =========================================================================
    # PAGINA 5: EXEMPLO DE VALIDAÇÃO DE CONTEÚDO (PRODUTO PILOTO FS 4-500 ET)
    # =========================================================================
    pdf.add_page()
    pdf.draw_section_header('5. Exemplo de Validacao Tecnicas: Produto Piloto FS 4-500 ET', 'Aplicacao pratica da metodologia Zero Inferencias')

    pdf.set_font('Helvetica', 'B', 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, 'Matriz de Confiabilidade de Dados (FS 4-500 ET):', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)

    tech_matrix = [
        ['Modelo / SKU', 'FS 4-500 ET', 'Descricao Demo Store', '100%', 'Confirmado'],
        ['Diametro Nominal', '500 mm', 'Descricao Demo Store', '100%', 'Confirmado'],
        ['Numero de Polos', '8 Polos', 'Descricao Demo Store', '100%', 'Confirmado'],
        ['Alimentacao Eletrica', 'Trifasico 220V/380V', 'Descricao Demo Store', '100%', 'Confirmado'],
        ['Acessorios', 'Grade e Difusor inclusos', 'Descricao Demo Store', '100%', 'Confirmado'],
        ['Corrente (A) / Vazao', 'Nao informadas no lote atual', 'Requer Datasheet do fabricante', '0%', 'Nao Encontrado'],
        ['Grau de Protecao IP', 'Nao informado no lote atual', 'Requer Datasheet do fabricante', '0%', 'Nao Encontrado']
    ]
    pdf.draw_table(['Atributo', 'Valor Declarado', 'Fonte Oficial', 'Confianca', 'Status'], tech_matrix, [32, 45, 63, 25, 25])

    # =========================================================================
    # PAGINA 6: METODOLOGIA E FLUXO DE PRODUÇÃO
    # =========================================================================
    pdf.draw_section_header('6. Fluxo Metodologico de Producao em Lote', 'Pipeline de trabalho para replicacao nos 216 produtos')

    pipeline_steps = [
        ['Etapa 1: Pesquisa de Fonte Oficial', 'Busca de dados unicamente em fontes confirmadas da Demo Store ou datasheet original.'],
        ['Etapa 2: Validacao de Confiabilidade', 'Classificacao dos atributos em 100% (Confirmados) ou 0% (Nao Encontrados). Zero inferencias.'],
        ['Etapa 3: Analise Factual de Mercado', 'Mapeamento de concorrentes para identificacao de lacunas de informacao e SEO.'],
        ['Etapa 4: Otimizacao SEO & GEO (IA)', 'Criacao de Headings H1/H2, Meta Descriptions e marcacoes Schema (Product/FAQPage).'],
        ['Etapa 5: Redacao de Conteudo B2B', 'Copywriting tecnico e comercial ajustado para orcamentistas e engenheiros.'],
        ['Etapa 6: Ingestao no Template Elementor', 'Alimentacao dos campos dinamicos no Single Product Template reutilizavel.'],
        ['Etapa 7: Revisao de Engenharia', 'Checagem final de conformidade antes da publicacao oficial.']
    ]
    pdf.draw_table(['Etapa do Pipeline', 'Descricao Operacional'], pipeline_steps, [48, 142])

    # =========================================================================
    # PAGINA 7: CRONOGRAMA, BENEFÍCIOS E PARECER DE SUBMISSÃO
    # =========================================================================
    pdf.add_page()
    pdf.draw_section_header('7. Cronograma de Execucao do Projeto', 'Status das fases de desenvolvimento')

    timeline = [
        ['Fase 1: Diagnostico e Priorizacao 80/20', 'Isolamento dos Top 40 produtos por volume de tráfego (GA4/GSC)', '[x] Concluido'],
        ['Fase 2: Definicao do Padrao Zero Inferencias', 'Criacao da metodologia de confiabilidade (100% / 0%)', '[x] Concluido'],
        ['Fase 3: Producao dos 3 Produtos Piloto', 'Desenvolvimento completo de conteudo para A25089VBHBL, FS 4-500 ET e P-FF 2-146 P', '[x] Concluido'],
        ['Fase 4: Criacao da Proposta Executiva PDF', 'Elaboracao deste documento de apresentacao para alinhamento interno', '[x] Concluido'],
        ['Fase 5: Validacao pela Diretoria / Gestao', 'Submissao deste documento para aprovacao de escopo e arquitetura', '[/] Em Validacao'],
        ['Fase 6: Montagem do Single Product Elementor', 'Implementacao dos blocos visuais e CSS .sp- no WordPress', '[ ] Proxima Etapa'],
        ['Fase 7: Producao em Lote (Curva A - 37 Prods)', 'Alimentacao dinamica do template para o Top 40', '[ ] Planejado'],
        ['Fase 8: Producao Cauda Longa (176 Prods)', 'Escalabilidade para a totalidade do catalogo Demo Store', '[ ] Planejado']
    ]
    pdf.draw_table(['Fase do Projeto', 'Escopo de Entrega', 'Status Actual'], timeline, [50, 110, 30])

    pdf.draw_section_header('8. Beneficios Estratégicos para a Demo Store', 'Retorno do investimento e ganhos institucionais')

    benefits = [
        'Padronização Visual e Tecnica de 216 produtos do catalogo.',
        'Dominancia Organica em SEO B2B com ranqueamento para termos de cauda longa.',
        'Prontidão para Busca por Inteligencia Artificial (GEO) via Schemas JSON-LD.',
        'Reducao Drastica do Tempo de Manutencao via Single Product Template reutilizavel.',
        'Diminuicao de Devolucoes (RMA) por inconsistencia de dados tecnicos.',
        'Posicionamento de Autoridade perante engenheiros e compradores industriais corporativos.'
    ]
    pdf.set_font('Helvetica', '', 8.5)
    pdf.set_text_color(30, 41, 59)
    for b in benefits:
        pdf.cell(5, 5, '')
        pdf.cell(0, 5, f'  > {b}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Submission Banner (EM VALIDAÇÃO EXECUTIVA)
    pdf.set_fill_color(254, 243, 199)
    pdf.set_draw_color(234, 179, 8)
    y_sub = pdf.get_y()
    pdf.rect(10, y_sub, 190, 24, 'FD')
    pdf.set_xy(14, y_sub + 3)
    pdf.set_font('Helvetica', 'B', 9.5)
    pdf.set_text_color(146, 64, 14)
    pdf.cell(0, 5, 'PARECER DE SUBMISSÃO: PROPOSTA SUBMETIDA PARA APROVAÇÃO EXECUTIVA', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_x(14)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(120, 53, 15)
    pdf.multi_cell(182, 4.2, 
        'Este documento formaliza a proposta de modernizacao do catalogo B2B da Demo Store. Solicitamos a avaliacao e '
        'parecer da diretoria e gestao comercial para autorizacao do inicio da montagem do template no Elementor Pro.')

    output_path = os.path.join(
        r'c:\Users\comercial\Desktop\Projeto landing pages',
        'Documento_Executivo_Projeto_LandingPages_DemoStore.pdf'
    )
    pdf.output(output_path)
    print(f"DOCUMENTO EXECUTIVO REVISADO GERADO COM SUCESSO: {output_path}")

if __name__ == '__main__':
    build_pdf()
