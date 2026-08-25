# -*- coding: utf-8 -*-
"""
Módulo de Renderização HTML Premium - Gera os blocos ACF com as novas classes .sp-
Identidade Visual: Azul Sell-Parts #1250B2 | Cinza #36404F | Branco #FFFFFF
"""
import urllib.parse

def _gerar_pills_curtas(produto_data):
    """
    Gera chips/pills curtos e objetivos (estilo idêntico ao 2º print):
    Ex: '220/380 V trifásico', 'Sentido soprador', 'Proteção IP54', 'Rolamento de esferas'
    """
    import unicodedata
    def strip_accents(text):
        return ''.join(c for c in unicodedata.normalize('NFD', str(text)) if unicodedata.category(c) != 'Mn').lower().strip()

    # 1. Se o hero_checklist explícito existir, use ele como prioridade absoluta
    if "hero_checklist" in produto_data and produto_data["hero_checklist"]:
        pills = []
        for item in produto_data["hero_checklist"]:
            txt = str(item).lstrip("✓").lstrip("•").lstrip("-").strip()
            if txt:
                pills.append(txt)
        if len(pills) > 0:
            return pills

    # Caso contrário, faz a inferência automática
    specs = {strip_accents(s.get("atributo", "")): str(s.get("valor", "")).strip() for s in produto_data.get("especificacoes", []) if s.get("valor")}
    
    pills = []
    
    # 1. Tensão / Alimentação (Apenas o valor principal ex: 220 V)
    tensao = specs.get("tensao nominal", specs.get("voltagem nominal", specs.get("tensao", "")))
    if tensao:
        val_t = tensao.split("(")[0].replace(" / ", "/").strip()
        if len(val_t) > 15:
            val_t = val_t.split(" ")[0] + " V"
        pills.append(val_t)
            
    # 2. Sentido / Fluxo / Tipo (Apenas uma palavra)
    nome_p = produto_data.get("nome", "").lower()
    slug_p = produto_data.get("slug", "").lower()
    if "micro" in nome_p or "micro" in slug_p:
        pills.append("Microventilador")
    elif "soprador" in nome_p or "soprador" in slug_p or "vt" in slug_p or "vm" in slug_p:
        pills.append("Soprador")
    elif "exaustor" in nome_p or "exaustor" in slug_p or "et" in slug_p or "em" in slug_p:
        pills.append("Exaustor")
    elif "in-line" in slug_p:
        pills.append("In-Line")
    elif "radial" in slug_p:
        pills.append("Radial")
    elif "centrifugo" in slug_p or "centrífugo" in nome_p:
        pills.append("Centrífugo")
        
    # 3. Grau de Proteção IP (Apenas ex: IP54)
    ip = specs.get("grau de protecao (ip)", specs.get("protecao mecanica", specs.get("grau de protecao", specs.get("ip", ""))))
    if ip:
        ip_clean = ip.replace("Proteção", "").replace("IP-", "IP").replace("IP ", "IP").strip()
        pills.append(ip_clean if ip_clean.startswith("IP") else f"IP{ip_clean}")
        
    # 4. Mancal / Rolamento (Apenas 'Rolamento')
    mancal = specs.get("mancais", specs.get("mancal", specs.get("tipo de mancal", "")))
    if mancal and ("rolamento" in mancal.lower() or "bearing" in mancal.lower()):
        pills.append("Rolamento")
        
    # 5. Diâmetro Nominal (Fallback, ex: 250mm)
    diam = specs.get("diametro nominal", specs.get("diametro", ""))
    if diam and len(pills) < 4:
        pills.append(diam)

    return pills


def render_resumo_tecnico(produto_data):
    """Gera o HTML da descrição + pills curtas para o Hero (idêntico ao mockup)."""
    desc = produto_data.get("resumo_tecnico", "").strip()
    
    # Converte quebras de linha do JSON em parágrafos espaçados
    paras = [p.strip() for p in desc.split("\n\n") if p.strip()]
    if paras:
        desc_html = "".join(f"<p>{p}</p>\n" for p in paras).strip()
    elif desc:
        desc_html = f"<p>{desc}</p>"
    else:
        desc_html = ""
    
    html = '<div class="sp-hero-desc">\n'
    html += f'{desc_html}\n\n'
    
    pills = _gerar_pills_curtas(produto_data)
    
    if pills:
        html += '<div class="sp-hero-pills" style="display: flex; flex-wrap: wrap; gap: 8px; margin: 15px 0 20px 0; align-items: center;">\n'
        for pill in pills:
            html += f'  <span style="background-color: #eff6ff; color: #1250b2; padding: 5px 12px; border-radius: 99px; font-size: 12.5px; font-weight: 600; border: 1px solid #bfdbfe; display: inline-flex; align-items: center; white-space: nowrap;">{pill}</span>\n'
        html += '</div>\n\n'

    html += f'<p class="sp-hero-modelo" style="margin-top: 14px; font-size: 15px; color: #1250b2;"><strong>Modelo / Código: {produto_data["sku"]}</strong></p>\n'
    html += '</div>'
    return html

def render_especificacoes(specs_confirmadas, alerta_tabela="", curva_html=""):
    """Gera o HTML da tabela técnica industrial premium com badge de seção, alerta opcional e curva aerodinâmica SVG."""
    html = '<div class="sp-especificacoes">\n'
    html += '    <div class="sp-especificacoes-header">\n'
    html += '        <span class="sp-badge-secao" style="background: rgba(255,255,255,0.2); color: #fff; border-color: rgba(255,255,255,0.4); margin-bottom: 0;">ESPECIFICAÇÕES DO PRODUTO</span>\n'
    html += '    </div>\n'
    html += '    <table class="sp-table">\n'
    html += '        <tbody>\n'

    for spec in specs_confirmadas:
        val = spec["valor"]
        if spec.get("campo") == "categoria_header":
            html += f'            <tr>\n                <td colspan="2" style="background-color: #36404f; color: #ffffff; padding: 12px 16px; font-weight: 800; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; text-align: center; border: none;">{spec["atributo"]}</td>\n            </tr>\n'
        else:
            cls = ' class="sp-value-numeric"' if "modelo" in spec["atributo"].lower() or "código" in spec["atributo"].lower() else ""
            html += f'            <tr>\n                <td><strong>{spec["atributo"]}</strong></td>\n                <td{cls}>{val}</td>\n            </tr>\n'

    html += '        </tbody>\n    </table>\n'
    
    if alerta_tabela:
        html += f'    <div class="sp-alerta-tabela" style="margin-top: 20px; padding: 16px; background-color: #eff6ff; border-left: 4px solid #1250b2; color: #1e3a8a; font-size: 14px; line-height: 1.5; border-radius: 4px;">\n'
        html += f'        {alerta_tabela}\n'
        html += '    </div>\n'
        
    if curva_html:
        html += f'\n{curva_html}\n'
        
    html += '</div>'
    return html

def render_aplicacoes_categoria(produto_input):
    """
    Gera o HTML do Bloco 1 - Aplicações por Categoria (Nível 1 - O QUE O PRODUTO FAZ).
    Suporta dict 'aplicacoes_categoria' ou lista 'aplicacoes'.
    """
    if not isinstance(produto_input, dict):
        return ""

    app_cat = produto_input.get("aplicacoes_categoria")
    nome_p = produto_input.get("nome", "").replace(" - " + produto_input.get("sku", ""), "").strip()

    cards_cat = []
    tit_cat = f"Aplicações do {nome_p}"
    intro_cat = "Soluções técnicas de ventilação e circulação de ar para alta eficiência operacional."

    if isinstance(app_cat, dict):
        tit_cat = app_cat.get("titulo") or tit_cat
        intro_cat = app_cat.get("intro") or intro_cat
        cards_cat = app_cat.get("cards", [])
    elif isinstance(produto_input.get("aplicacoes"), list):
        cards_cat = produto_input.get("aplicacoes")
    elif isinstance(produto_input.get("aplicacoes"), dict):
        app_dict = produto_input.get("aplicacoes")
        tit_cat = app_dict.get("titulo") or tit_cat
        intro_cat = app_dict.get("intro") or intro_cat
        cards_cat = app_dict.get("cards", [])

    if not cards_cat:
        return ""

    html = '<div class="sp-secao-aplicacoes sp-secao-bloco" style="margin-bottom: 40px; font-family: inherit;">\n'
    html += f'  <h2 class="sp-secao-titulo" style="color: #36404f; font-size: 28px; font-weight: 800; margin: 0 0 8px 0; line-height: 1.25;">{tit_cat}</h2>\n'
    if intro_cat:
        html += f'  <p class="sp-secao-intro" style="color: #475569; font-size: 14.5px; font-weight: 400; margin: 0 0 24px 0; line-height: 1.5;">{intro_cat}</p>\n'

    html += '  <div class="sp-grid-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">\n'
    for card in cards_cat:
        if isinstance(card, dict):
            t = card.get("titulo", "")
            d = card.get("descricao", "")
        else:
            t = str(card)
            d = ""
        html += '    <div class="sp-card-item" style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; position: relative; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 1px 3px rgba(0,0,0,0.03); transition: all 0.3s ease;">\n'
        html += f'      <h3 class="sp-card-titulo" style="color: #36404f; font-size: 17px; font-weight: 800; margin: 0 0 10px 0; line-height: 1.35;">{t}</h3>\n'
        if d:
            html += f'      <p class="sp-card-desc" style="color: #334155; font-size: 14px; font-weight: 400; margin: 0; line-height: 1.6;">{d}</p>\n'
        html += '    </div>\n'
    html += '  </div>\n'
    html += '</div>'
    return html

def render_aplicacoes_equipamento(produto_input):
    """
    Gera o HTML do Bloco 2 - Aplicações por Equipamento (Nível 2 - ONDE USAR).
    Suporta dict 'aplicacoes_equipamento' ou listas 'onde_usar' / 'equipamentos'.
    """
    if not isinstance(produto_input, dict):
        return ""

    app_eq = produto_input.get("aplicacoes_equipamento")
    nome_p = produto_input.get("nome", "").replace(" - " + produto_input.get("sku", ""), "").strip()

    cards_eq = []
    tit_eq = f"Onde o {nome_p} pode ser instalado?"
    intro_eq = "Componente projetado para montagem direta e integração mecânica nos seguintes equipamentos industriais:"

    if isinstance(app_eq, dict):
        tit_eq = app_eq.get("titulo") or tit_eq
        intro_eq = app_eq.get("intro") or intro_eq
        cards_eq = app_eq.get("cards", [])
    else:
        raw_eq = produto_input.get("onde_usar") or produto_input.get("equipamentos") or produto_input.get("aplicacoes_equipamentos")
        if isinstance(raw_eq, list):
            cards_eq = raw_eq
        elif isinstance(raw_eq, dict):
            tit_eq = raw_eq.get("titulo") or tit_eq
            intro_eq = raw_eq.get("intro") or intro_eq
            cards_eq = raw_eq.get("cards", [])

    if not cards_eq:
        return ""

    html = '<div class="sp-secao-aplicacoes sp-secao-bloco" style="margin-bottom: 40px; font-family: inherit;">\n'
    html += f'  <h2 class="sp-secao-titulo" style="color: #36404f; font-size: 28px; font-weight: 800; margin: 0 0 8px 0; line-height: 1.25;">{tit_eq}</h2>\n'
    if intro_eq:
        html += f'  <p class="sp-secao-intro" style="color: #475569; font-size: 14.5px; font-weight: 400; margin: 0 0 24px 0; line-height: 1.5;">{intro_eq}</p>\n'

    html += '  <div class="sp-grid-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">\n'
    for card in cards_eq:
        if isinstance(card, dict):
            t = card.get("titulo", "")
            d = card.get("descricao", "")
        else:
            t = str(card)
            d = ""
        html += '    <div class="sp-card-item" style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; position: relative; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 1px 3px rgba(0,0,0,0.03); transition: all 0.3s ease;">\n'
        html += f'      <h3 class="sp-card-titulo" style="color: #36404f; font-size: 17px; font-weight: 800; margin: 0 0 10px 0; line-height: 1.35;">{t}</h3>\n'
        if d:
            html += f'      <p class="sp-card-desc" style="color: #334155; font-size: 14px; font-weight: 400; margin: 0; line-height: 1.6;">{d}</p>\n'
        html += '    </div>\n'
    html += '  </div>\n'
    html += '</div>'
    return html

def render_aplicacoes(produto_input, categoria_link=None):
    """
    Retorna APENAS o Bloco 1 - Aplicações por Categoria (Nível 1) no campo sp_aplicacoes.
    """
    return render_aplicacoes_categoria(produto_input)

def render_beneficios(lista_beneficios):
    """Gera o HTML no formato ultra-premium sp-cards numerados."""
    if not lista_beneficios:
        return ""
        
    html = '<div class="sp-beneficios">\n  <div class="sp-cards">\n'
    for i, ben in enumerate(lista_beneficios, start=1):
        num = f"{i:02d}"
        if isinstance(ben, dict):
            tit = ben.get("titulo", "")
            desc = ben.get("descricao", "")
        else:
            parts = ben.split(":", 1) if ":" in ben else (ben, "")
            tit = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            
        html += '    <div class="sp-card sp-card-item">\n'
        html += f'      <div class="sp-card-number">{num}</div>\n'
        html += f'      <h3 class="sp-card-title">{tit}</h3>\n'
        html += f'      <p class="sp-card-desc">{desc}</p>\n'
        html += '    </div>\n'
    
    html += '  </div>\n</div>'
    return html

MAPA_SEGMENTOS_PTBR = {
    "AR CONDICONADO DE PAINEL": "Ar-Condicionado de Painel Elétrico",
    "ARMAZENAMENTO E LOGISTICA": "Armazenamento e Logística",
    "AUTOMACAO BANCARIA ELETRONICOS ELEVADORES E GUINDASTES": "Automação Bancária, Eletrônicos, Elevadores e Guindastes",
    "BARES RESTAURANTES E HOTELARIA": "Bares, Restaurantes e Hotelaria (Food Service)",
    "BOMBAS E TROCADORES DE CALOR": "Bombas Industriais e Trocadores de Calor",
    "CAMINHÃO FRIGORIFICO": "Transporte e Caminhões Frigoríficos",
    "CAMINHÃO FRIGORÍFICO": "Transporte e Caminhões Frigoríficos",
    "CAMINHAO FRIGORIFICO": "Transporte e Caminhões Frigoríficos",
    "COIFAS / CHURRASQUEIRAS": "Fabricantes de Coifas e Sistemas de Exaustão",
    "COMERCIO DE ALIMENTOS": "Comércio e Distribuição de Alimentos",
    "COMPRESSOR DE AR COMPRIMIDO": "Compressores e Sistemas de Ar Comprimido",
    "CONSUMIDORES PF": "Consumidores Finais",
    "COZINHAS INDUSTRIAIS BALCAO FRIGORIFICO E EXPOSITORES": "Cozinhas Industriais, Balcões Frigoríficos e Expositores",
    "DEMAIS LOJAS REVENDEDORAS": "Lojas Revendedoras Multimarcas",
    "ENGENHARIA E PROJETOS": "Empresas de Engenharia e Projetos Industriais",
    "EQUIPAMENTO MEDICO ODONTOLOGICO E HOSPITALAR": "Equipamentos Médicos, Odontológicos e Hospitalares",
    "ESTUFAS / LAREIRAS / CHOCADEIRAS": "Estufas, Lareiras e Incubadoras",
    "FABRIC ALIMENTOS": "Fabricantes da Indústria de Alimentos",
    "FABRIC BEBIDAS": "Fabricantes da Indústria de Bebidas",
    "FABRIC CALCADOS": "Fabricantes da Indústria de Calçados",
    "FABRIC CALÇADOS": "Fabricantes da Indústria de Calçados",
    "FABRIC CIMENTO E ARTEFATOS": "Fabricantes de Cimento e Artefatos",
    "FABRIC DE PROD QUIM E FARM": "Fabricantes de Produtos Químicos e Farmacêuticos",
    "FABRIC DERIV DO PETR E BIOCOMB": "Fabricantes de Derivados de Petróleo e Biocombustíveis",
    "FABRIC MAQ APAR MAT ELETRICOS E ELETRONICOS": "Fabricantes de Máquinas, Aparelhos e Materiais Elétricos",
    "FABRIC PAPEL E PROD DE PAPEL": "Fabricantes de Papel e Celulose",
    "FABRIC PROD CERÂMICOS": "Fabricantes de Produtos Cerâmicos e Fornos",
    "FABRIC PROD CERAMICOS": "Fabricantes de Produtos Cerâmicos e Fornos",
    "FABRIC PROD DE MADEIRA E VIDRO": "Fabricantes de Produtos de Madeira e Vidro",
    "FABRIC PROD TEXTEIS": "Fabricantes de Produtos Têxteis",
    "GERACAO DE ENERGIA E PAINEIS SOLARES": "Geração de Energia e Painéis Solares",
    "GERAÇÃO DE ENERGIA E PAINEIS SOLARES": "Geração de Energia e Painéis Solares",
    "GRANDES VAREGISTAS": "Grandes Varejistas e Redes de Lojas",
    "HOSPITAIS CLINICAS E LABORATORIOS": "Hospitais, Clínicas e Laboratórios",
    "INDUSTRIA AUTOMOTIVA E AUTOPEÇAS": "Indústria Automotiva e Autopeças",
    "INDUSTRIA AUTOMOTIVA E AUTOPECAS": "Indústria Automotiva e Autopeças",
    "INDUSTRIA DE PLASTICOS E EMBALAGENS": "Indústria de Plásticos e Embalagens",
    "LOJAS DE PECAS DE MANUTENCAO": "Lojas de Peças de Manutenção Industrial",
    "LOJAS DE PECAS DE REFRIGERACAO": "Lojas de Peças de Refrigeração",
    "LOJAS DE PECAS ELETRONICAS": "Lojas de Peças Eletrônicas e Componentes",
    "MANUTENCAO DE REFRIGERACAO": "Empresas de Manutenção de Refrigeração",
    "MANUTENCAO INDUSTRIAL": "Manutenção Industrial e Utilidades",
    "MAQ E EQUIP CLIMAT E DESUMID E QUEIMADORES": "Máquinas de Climatização, Desumidificação e Queimadores",
    "MAQ E EQUIP IND AGRIC ALIMENT SORV RESF DE LEITE": "Fabricantes de Equipamentos Agrícolas, Alimentos e Laticínios",
    "MAQUINAS DE CALÇADOS": "Fabricantes de Máquinas para Calçados",
    "MAQUINAS DE CALCADOS": "Fabricantes de Máquinas para Calçados",
    "MAQUINAS DE EMBALAGEM": "Fabricantes de Máquinas de Embalagem",
    "MAQUINAS DE SOLDA ESTABIL RETIFIC": "Máquinas de Solda, Estabilizadores e Retificadores",
    "MOTORES GERAD TRANSF PAINEIS GABIN RACKS NOBREAK FONTES": "Fabricantes de Motores, Geradores, Painéis e Nobreaks",
    "ORGAOS PUBLICOS E INSTITUTOS": "Órgãos Públicos e Institutos de Pesquisa",
    "REFRESQUEIRAS / BEBEDOUROS / GELA CANECA": "Refresqueiras, Bebedouros e Equipamentos de Bebidas",
    "SETOR SUCROENERGETICO E AGRICOLA": "Setor Sucroenergético e Agrícola",
    "SIDERURGIA METALURGIA E PECAS": "Siderurgia, Metalurgia e Peças Industriais",
    "TRANSPORTADORA": "Empresas de Transporte e Logística",
    "UNID DE REFRIG CAMARAS FRIGOR PLUG-IN TUNEL DE CONGEL": "Unidades de Refrigeração, Câmaras Frigoríficas e Túneis",
    "UNIDADE DE AGUA GELADA E TORRE DE CONGELAMENTO": "Unidades de Água Gelada (Chillers) e Torres de Resfriamento",
    "VENTILACAO EXAUSTAO SALAS LIMPAS E CAPELAS": "Sistemas de Ventilação, Salas Limpas e Capelas"
}

def sanitizar_segmento_ptbr(s):
    if not s:
        return ""
    s_clean = str(s).strip()
    s_upper = s_clean.upper()
    if s_upper in MAPA_SEGMENTOS_PTBR:
        return MAPA_SEGMENTOS_PTBR[s_upper]
    
    if s_clean != s_upper:
        return s_clean
        
    palavras = s_clean.split()
    minusculas = {'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'para', 'com', 'ou'}
    resultado = []
    for i, p in enumerate(palavras):
        p_low = p.lower()
        if i > 0 and p_low in minusculas:
            resultado.append(p_low)
        else:
            resultado.append(p.capitalize())
    return " ".join(resultado)

def render_mercado(mercado_input, lista_segmentos=None):
    """
    Gera o HTML do bloco de Mercado e Segmentos no padrão idêntico de cards limpos com hover.
    Subtítulo limpo padrão B2B e cards diretos de setores.
    """
    mercados_list = []
    lista_segmentos = lista_segmentos or []

    if isinstance(mercado_input, dict):
        m_list = mercado_input.get("mercados_list") or mercado_input.get("mercados") or mercado_input.get("mercados_cards") or mercado_input.get("cards")
        m_texto = mercado_input.get("mercado") or mercado_input.get("resumo") or ""
        
        if isinstance(m_list, list) and m_list:
            mercados_list = m_list
        elif isinstance(m_texto, list) and m_texto:
            mercados_list = m_texto
        elif isinstance(m_texto, str) and m_texto.strip():
            mercados_list = [l.strip() for l in m_texto.split("\n") if l.strip()]

        lista_segmentos = mercado_input.get("segmentos") or lista_segmentos
    elif isinstance(mercado_input, list):
        mercados_list = mercado_input
    elif isinstance(mercado_input, str):
        if "\n" in mercado_input:
            mercados_list = [l.strip() for l in mercado_input.split("\n") if l.strip()]
        elif "atende" in mercado_input.lower() or "%" in mercado_input:
            partes = mercado_input.replace("atende prioritariamente os setores de ", "").replace("É a escolha de", "|").split("|")[0]
            mercados_list = [p.strip() for p in partes.split(",") if p.strip()]
        else:
            mercados_list = [mercado_input.strip()]

    if not mercados_list and not lista_segmentos:
        return ""

    intro = "Setores industriais e segmentos de aplicação comercial que utilizam este componente."

    html = '<div class="sp-mercado-container sp-secao-bloco" style="margin-bottom: 40px; font-family: inherit;">\n'
    html += '  <h2 class="sp-secao-titulo" style="color: #36404f; font-size: 28px; font-weight: 800; margin: 0 0 8px 0; line-height: 1.25;">Mercados Atendidos</h2>\n'
    html += f'  <p class="sp-secao-intro" style="color: #475569; font-size: 14.5px; font-weight: 400; margin: 0 0 24px 0; line-height: 1.5;">{intro}</p>\n'
    
    html += '  <div class="sp-grid-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">\n'
    if mercados_list:
        for m in mercados_list:
            if isinstance(m, dict):
                tit = m.get("titulo", "")
                desc = m.get("descricao", "")
                html += '    <div class="sp-card-item" style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; position: relative; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 1px 3px rgba(0,0,0,0.03); transition: all 0.3s ease;">\n'
                html += f'      <h3 class="sp-card-titulo" style="color: #36404f; font-size: 17px; font-weight: 800; margin: 0 0 10px 0; line-height: 1.35;">{tit}</h3>\n'
                if desc:
                    html += f'      <p class="sp-card-desc" style="color: #334155; font-size: 14px; font-weight: 400; margin: 0; line-height: 1.6;">{desc}</p>\n'
                html += '    </div>\n'
            else:
                html += f'    <div class="sp-card-item sp-card-mercado" style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); display: flex; align-items: center; transition: all 0.3s ease;"><span class="sp-mercado-texto" style="color: #334155; font-size: 14px; font-weight: 500; line-height: 1.5; margin: 0;">{m}</span></div>\n'

    if lista_segmentos:
        for seg in lista_segmentos:
            seg_formatted = sanitizar_segmento_ptbr(seg)
            if seg_formatted not in mercados_list:
                html += f'    <div class="sp-card-item sp-card-mercado" style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); display: flex; align-items: center; transition: all 0.3s ease;"><span class="sp-mercado-texto" style="color: #334155; font-size: 14px; font-weight: 500; line-height: 1.5; margin: 0;">{seg_formatted}</span></div>\n'

    html += '  </div>\n'
    html += '</div>'
    return html

def render_aplicacoes(produto_input, categoria_link=None):
    """
    Retorna APENAS o Bloco 1 - Aplicações por Categoria (Nível 1) no campo sp_aplicacoes.
    """
    return render_aplicacoes_categoria(produto_input)

def render_beneficios(lista_beneficios):
    """Gera o HTML no formato ultra-premium sp-cards numerados."""
    if not lista_beneficios:
        return ""
        
    html = '<div class="sp-beneficios">\n  <div class="sp-cards">\n'
    for i, ben in enumerate(lista_beneficios, start=1):
        num = f"{i:02d}"
        if isinstance(ben, dict):
            tit = ben.get("titulo", "")
            desc = ben.get("descricao", "")
        else:
            parts = ben.split(":", 1) if ":" in ben else (ben, "")
            tit = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            
        html += '    <div class="sp-card sp-card-item">\n'
        html += f'      <div class="sp-card-number">{num}</div>\n'
        html += f'      <h3 class="sp-card-title">{tit}</h3>\n'
        html += f'      <p class="sp-card-desc">{desc}</p>\n'
        html += '    </div>\n'
    
    html += '  </div>\n</div>'
    return html

MAPA_SEGMENTOS_PTBR = {
    "AR CONDICONADO DE PAINEL": "Ar-Condicionado de Painel Elétrico",
    "ARMAZENAMENTO E LOGISTICA": "Armazenamento e Logística",
    "AUTOMACAO BANCARIA ELETRONICOS ELEVADORES E GUINDASTES": "Automação Bancária, Eletrônicos, Elevadores e Guindastes",
    "BARES RESTAURANTES E HOTELARIA": "Bares, Restaurantes e Hotelaria (Food Service)",
    "BOMBAS E TROCADORES DE CALOR": "Bombas Industriais e Trocadores de Calor",
    "CAMINHÃO FRIGORIFICO": "Transporte e Caminhões Frigoríficos",
    "CAMINHÃO FRIGORÍFICO": "Transporte e Caminhões Frigoríficos",
    "CAMINHAO FRIGORIFICO": "Transporte e Caminhões Frigoríficos",
    "COIFAS / CHURRASQUEIRAS": "Fabricantes de Coifas e Sistemas de Exaustão",
    "COMERCIO DE ALIMENTOS": "Comércio e Distribuição de Alimentos",
    "COMPRESSOR DE AR COMPRIMIDO": "Compressores e Sistemas de Ar Comprimido",
    "CONSUMIDORES PF": "Consumidores Finais",
    "COZINHAS INDUSTRIAIS BALCAO FRIGORIFICO E EXPOSITORES": "Cozinhas Industriais, Balcões Frigoríficos e Expositores",
    "DEMAIS LOJAS REVENDEDORAS": "Lojas Revendedoras Multimarcas",
    "ENGENHARIA E PROJETOS": "Empresas de Engenharia e Projetos Industriais",
    "EQUIPAMENTO MEDICO ODONTOLOGICO E HOSPITALAR": "Equipamentos Médicos, Odontológicos e Hospitalares",
    "ESTUFAS / LAREIRAS / CHOCADEIRAS": "Estufas, Lareiras e Incubadoras",
    "FABRIC ALIMENTOS": "Fabricantes da Indústria de Alimentos",
    "FABRIC BEBIDAS": "Fabricantes da Indústria de Bebidas",
    "FABRIC CALCADOS": "Fabricantes da Indústria de Calçados",
    "FABRIC CALÇADOS": "Fabricantes da Indústria de Calçados",
    "FABRIC CIMENTO E ARTEFATOS": "Fabricantes de Cimento e Artefatos",
    "FABRIC DE PROD QUIM E FARM": "Fabricantes de Produtos Químicos e Farmacêuticos",
    "FABRIC DERIV DO PETR E BIOCOMB": "Fabricantes de Derivados de Petróleo e Biocombustíveis",
    "FABRIC MAQ APAR MAT ELETRICOS E ELETRONICOS": "Fabricantes de Máquinas, Aparelhos e Materiais Elétricos",
    "FABRIC PAPEL E PROD DE PAPEL": "Fabricantes de Papel e Celulose",
    "FABRIC PROD CERÂMICOS": "Fabricantes de Produtos Cerâmicos e Fornos",
    "FABRIC PROD CERAMICOS": "Fabricantes de Produtos Cerâmicos e Fornos",
    "FABRIC PROD DE MADEIRA E VIDRO": "Fabricantes de Produtos de Madeira e Vidro",
    "FABRIC PROD TEXTEIS": "Fabricantes de Produtos Têxteis",
    "GERACAO DE ENERGIA E PAINEIS SOLARES": "Geração de Energia e Painéis Solares",
    "GERAÇÃO DE ENERGIA E PAINEIS SOLARES": "Geração de Energia e Painéis Solares",
    "GRANDES VAREGISTAS": "Grandes Varejistas e Redes de Lojas",
    "HOSPITAIS CLINICAS E LABORATORIOS": "Hospitais, Clínicas e Laboratórios",
    "INDUSTRIA AUTOMOTIVA E AUTOPEÇAS": "Indústria Automotiva e Autopeças",
    "INDUSTRIA AUTOMOTIVA E AUTOPECAS": "Indústria Automotiva e Autopeças",
    "INDUSTRIA DE PLASTICOS E EMBALAGENS": "Indústria de Plásticos e Embalagens",
    "LOJAS DE PECAS DE MANUTENCAO": "Lojas de Peças de Manutenção Industrial",
    "LOJAS DE PECAS DE REFRIGERACAO": "Lojas de Peças de Refrigeração",
    "LOJAS DE PECAS ELETRONICAS": "Lojas de Peças Eletrônicas e Componentes",
    "MANUTENCAO DE REFRIGERACAO": "Empresas de Manutenção de Refrigeração",
    "MANUTENCAO INDUSTRIAL": "Manutenção Industrial e Utilidades",
    "MAQ E EQUIP CLIMAT E DESUMID E QUEIMADORES": "Máquinas de Climatização, Desumidificação e Queimadores",
    "MAQ E EQUIP IND AGRIC ALIMENT SORV RESF DE LEITE": "Fabricantes de Equipamentos Agrícolas, Alimentos e Laticínios",
    "MAQUINAS DE CALÇADOS": "Fabricantes de Máquinas para Calçados",
    "MAQUINAS DE CALCADOS": "Fabricantes de Máquinas para Calçados",
    "MAQUINAS DE EMBALAGEM": "Fabricantes de Máquinas de Embalagem",
    "MAQUINAS DE SOLDA ESTABIL RETIFIC": "Máquinas de Solda, Estabilizadores e Retificadores",
    "MOTORES GERAD TRANSF PAINEIS GABIN RACKS NOBREAK FONTES": "Fabricantes de Motores, Geradores, Painéis e Nobreaks",
    "ORGAOS PUBLICOS E INSTITUTOS": "Órgãos Públicos e Institutos de Pesquisa",
    "REFRESQUEIRAS / BEBEDOUROS / GELA CANECA": "Refresqueiras, Bebedouros e Equipamentos de Bebidas",
    "SETOR SUCROENERGETICO E AGRICOLA": "Setor Sucroenergético e Agrícola",
    "SIDERURGIA METALURGIA E PECAS": "Siderurgia, Metalurgia e Peças Industriais",
    "TRANSPORTADORA": "Empresas de Transporte e Logística",
    "UNID DE REFRIG CAMARAS FRIGOR PLUG-IN TUNEL DE CONGEL": "Unidades de Refrigeração, Câmaras Frigoríficas e Túneis",
    "UNIDADE DE AGUA GELADA E TORRE DE CONGELAMENTO": "Unidades de Água Gelada (Chillers) e Torres de Resfriamento",
    "VENTILACAO EXAUSTAO SALAS LIMPAS E CAPELAS": "Sistemas de Ventilação, Salas Limpas e Capelas"
}

def sanitizar_segmento_ptbr(s):
    if not s:
        return ""
    s_clean = str(s).strip()
    s_upper = s_clean.upper()
    if s_upper in MAPA_SEGMENTOS_PTBR:
        return MAPA_SEGMENTOS_PTBR[s_upper]
    
    if s_clean != s_upper:
        return s_clean
        
    palavras = s_clean.split()
    minusculas = {'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'para', 'com', 'ou'}
    resultado = []
    for i, p in enumerate(palavras):
        p_low = p.lower()
        if i > 0 and p_low in minusculas:
            resultado.append(p_low)
        else:
            resultado.append(p.capitalize())
    return " ".join(resultado)



def render_diferenciais(lista_diferenciais):
    """Gera os diferenciais no formato de lista padrão B2B."""
    html = '<div class="sp-diferenciais">\n<ul>\n'
    for dif in lista_diferenciais:
        html += f'<li>{dif}</li>\n'
    html += '</ul>\n</div>'
    return html

def render_faq(lista_faq):
    """Gera o HTML do accordion de FAQ usando tags details/summary nativas."""
    html = '<div class="sp-faq">\n'
    for faq in lista_faq:
        html += '  <details class="sp-faq-item">\n'
        html += f'    <summary class="sp-faq-question">{faq["pergunta"]}</summary>\n'
        html += f'    <div class="sp-faq-answer">{faq["resposta"]}</div>\n'
        html += '  </details>\n'
    html += '</div>'
    return html

def render_alerta(texto_alerta):
    """Retorna apenas o texto puro do alerta técnico."""
    return texto_alerta

def render_schema_product(produto_data):
    """
    Gera o JSON-LD do Product Schema (público) otimizado para produtos industriais B2B.

    REGRAS ESTRITAS:
    - Zero concorrentes ou marcas de terceiros.
    - Sem isSimilarTo.
    - Sem preços fictícios (sob orçamento).
    - Inclui especificações técnicas reais como PropertyValue em additionalProperty.
    """
    import json
    
    offers = {
        "@type": "Offer",
        "url": f"https://DemoStore.com.br/produto/{produto_data['slug']}/",
        "availability": "https://schema.org/InStock",
        "seller": {
            "@type": "Organization",
            "name": "Sell-Parts"
        }
    }
    
    # Se houver preço real informado no produto, inclui price e priceCurrency
    if "preco" in produto_data and produto_data["preco"]:
        try:
            offers["price"] = float(produto_data["preco"])
            offers["priceCurrency"] = "BRL"
        except (ValueError, TypeError):
            pass

    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": produto_data["nome"],
        "description": produto_data.get("resumo_tecnico", ""),
        "sku": produto_data.get("sku", produto_data["slug"]),
        "mpn": produto_data.get("sku", produto_data["slug"]),
        "brand": {
            "@type": "Brand",
            "name": "Sell-Parts"
        },
        "url": f"https://DemoStore.com.br/produto/{produto_data['slug']}/",
        "offers": offers
    }
    
    # Adiciona especificações técnicas reais como PropertyValue em additionalProperty
    specs = produto_data.get("especificacoes", [])
    if isinstance(specs, list) and specs:
        add_props = []
        for spec in specs:
            if isinstance(spec, dict):
                atrib = spec.get("atributo") or spec.get("nome")
                val = spec.get("valor")
                if atrib and val:
                    add_props.append({
                        "@type": "PropertyValue",
                        "name": str(atrib).strip(),
                        "value": str(val).strip()
                    })
        if add_props:
            schema["additionalProperty"] = add_props

    return json.dumps(schema, ensure_ascii=False, indent=2)

def render_schema_faq(lista_faq):
    """Gera o JSON-LD do FAQPage Schema factual e limpo."""
    import json
    entities = []
    if isinstance(lista_faq, list):
        for faq in lista_faq:
            if isinstance(faq, dict) and faq.get("pergunta") and faq.get("resposta"):
                entities.append({
                    "@type": "Question",
                    "name": str(faq["pergunta"]).strip(),
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": str(faq["resposta"]).strip()
                    }
                })
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)

def render_downloads(nome_produto):
    """Gera o HTML do bloco de downloads premium para B2B linkando direto pro WhatsApp."""
    msg = f"Olá! Gostaria de solicitar o datasheet / ficha técnica do produto: *{nome_produto}*."
    msg_encoded = urllib.parse.quote(msg)
    wa_link = f"https://wa.me/551156144466?text={msg_encoded}"
    
    html = '<div class="sp-downloads">\n'
    html += '  <div class="sp-downloads-card">\n'
    html += '    <div class="sp-downloads-content">\n'
    html += '      <h4 class="sp-downloads-title">Ficha Técnica e Desenho Técnico Cotado</h4>\n'
    html += '      <p class="sp-downloads-desc">Solicite o datasheet oficial e o desenho cotado com dimensões completas de furação para este produto.</p>\n'
    html += '    </div>\n'
    html += '    <div class="sp-downloads-action">\n'
    html += f'      <a href="{wa_link}" class="btn-primario" target="_blank" rel="noopener">\n'
    html += '        Solicitar Datasheet\n'
    html += '      </a>\n'
    html += '    </div>\n'
    html += '  </div>\n'
    html += '</div>'
    return html
