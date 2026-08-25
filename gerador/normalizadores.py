# -*- coding: utf-8 -*-
"""
======================================================================
Demo Store — MÓDULO MESTRE DE NORMALIZAÇÃO DE SEGMENTOS E EQUIPAMENTOS
======================================================================
"""

import re

# Termos expressamente proibidos em qualquer página ou tabela B2B
FORBIDDEN_SEGMENTS = {
    "CONSUMIDORES PF",
    "CONSUMIDOR PF",
    "PESSOA FISICA",
    "PESSOA FÍSICA",
    "EM BRANCO",
    "SEM SEGMENTO",
    "OUTROS",
    "NAO INFORMADO",
    "NÃO INFORMADO"
}

# Dicionário Mestre Completo para os 55 Segmentos do ERP Sell-Parts
SEGMENT_DICTIONARY = {
    "AR CONDICONADO DE PAINEL": "Climatização e ar-condicionado para painéis elétricos",
    "ARMAZENAMENTO E LOGISTICA": "Centros logísticos, armazenagem frigorificada e galpões",
    "AUTOMACAO BANCARIA ELETRONICOS ELEVADORES E GUINDASTES": "Automação, elevadores e equipamentos eletromecânicos",
    "BARES RESTAURANTES E HOTELARIA": "Cozinhas profissionais, restaurantes, hotelaria e food service",
    "BOMBAS E TROCADORES DE CALOR": "Trocadores de calor, bombas e sistemas hidráulicos",
    "CAMINHÃO FRIGORIFICO": "Refrigeração veicular e transporte frigorífico",
    "CAMINHAO FRIGORIFICO": "Refrigeração veicular e transporte frigorífico",
    "COIFAS / CHURRASQUEIRAS": "Ventilação de cozinhas profissionais, coifas e churrasqueiras",
    "COMERCIO DE ALIMENTOS": "Comércio, distribuição e entrepostos de alimentos",
    "COMPRESSOR DE AR COMPRIMIDO": "Compressores industriais e sistemas de ar comprimido",
    "COMPRESSOR DE AR": "Compressores industriais e sistemas de ar comprimido",
    "COZINHAS INDUSTRIAIS BALCAO FRIGORIFICO E EXPOSITORES": "Refrigeração comercial, balcões frigoríficos e expositores",
    "DEMAIS LOJAS REVENDEDORAS": "Revendas técnicas e distribuidores de componentes",
    "ENGENHARIA E PROJETOS": "Empresas de engenharia, integração e projetos industriais",
    "EQUIPAMENTO MEDICO ODONTOLOGICO E HOSPITALAR": "Equipamentos médicos, hospitalares e laboratoriais",
    "EQUIPAMENTO MEDICO": "Equipamentos médicos, hospitalares e laboratoriais",
    "ESTUFAS / LAREIRAS / CHOCADEIRAS": "Estufas industriais, chocadeiras e sistemas de aquecimento",
    "FABRIC ALIMENTOS": "Indústria alimentícia e processamento de alimentos",
    "FABRIC BEBIDAS": "Indústria de bebidas, cervejarias e engarrafadoras",
    "FABRIC CALCADOS": "Indústria calçadista, coureira e conformação térmica",
    "FABRIC CALÇADOS": "Indústria calçadista, coureira e conformação térmica",
    "MAQUINAS DE CALÇADOS": "Indústria calçadista, coureira e conformação térmica",
    "MAQUINAS DE CALCADOS": "Indústria calçadista, coureira e conformação térmica",
    "FABRIC CIMENTO E ARTEFATOS": "Indústria de cimento, mineração e materiais de construção",
    "FABRIC DE PROD QUIM E FARM": "Indústria química, farmacêutica e cosméticos",
    "FABRIC DERIV DO PETR E BIOCOMB": "Petroquímica, biocombustíveis e refinarias",
    "FABRIC MAQ APAR MAT ELETRICOS E ELETRONICOS": "Fabricantes OEM de máquinas e equipamentos eletroeletrônicos",
    "FABRIC PAPEL E PROD DE PAPEL": "Indústria de papel, celulose e cartonagem",
    "FABRIC PROD CERÂMICOS": "Indústria cerâmica, olarias e fornos refratários",
    "FABRIC PROD CERAMICOS": "Indústria cerâmica, olarias e fornos refratários",
    "FABRIC PROD DE MADEIRA E VIDRO": "Indústria vidreira, moveleira e beneficiamento de madeira",
    "FABRIC PROD TEXTEIS": "Indústria têxtil, tecelagem e fiações",
    "GERACAO DE ENERGIA E PAINEIS SOLARES": "Geração de energia, inversores solares e renováveis",
    "GERAÇÃO DE ENERGIA E PAINEIS SOLARES": "Geração de energia, inversores solares e renováveis",
    "GRANDES VAREGISTAS": "Redes de supermercados e centros de distribuição",
    "HOSPITAIS CLINICAS E LABORATORIOS": "Hospitais, clínicas e laboratórios de análise",
    "INDUSTRIA AUTOMOTIVA E AUTOPEÇAS": "Indústria automotiva e montadoras de autopeças",
    "INDUSTRIA AUTOMOTIVA E AUTOPECAS": "Indústria automotiva e montadoras de autopeças",
    "INDUSTRIA DE PLASTICOS E EMBALAGENS": "Indústria plástica, transformadoras e embalagens",
    "MAQUINAS DE EMBALAGEM": "Indústria plástica, transformadoras e embalagens",
    "INDÚSTRIA DE FERRAGENS E FERRAMENTAS": "Indústria metalmecânica, estamparia e ferramentas",
    "INDUSTRIA DE FERRAGENS E FERRAMENTAS": "Indústria metalmecânica, estamparia e ferramentas",
    "LOJAS DE PECAS DE MANUTENCAO": "Distribuidores e revendedores de manutenção industrial",
    "LOJAS DE PECAS DE REFRIGERACAO": "Refrigeração comercial e distribuidores de reposição técnica",
    "LOJAS DE PECAS ELETRONICAS": "Distribuidores de componentes eletrônicos e automação",
    "MANUTENCAO DE REFRIGERACAO": "Prestadores de serviços de HVAC e refrigeração",
    "MANUTENCAO INDUSTRIAL": "Manutenção industrial, montagens e facilities",
    "MAQ E EQUIP CLIMAT E DESUMID E QUEIMADORES": "Climatização, desumidificação e sistemas de aquecimento",
    "MAQ E EQUIP IND AGRIC ALIMENT SORV RESF DE LEITE": "Máquinas agrícolas, agroindústria e resfriadores de leite",
    "MAQUINAS DE SOLDA ESTABIL RETIFIC": "Fabricantes de máquinas de solda e fontes industriais",
    "MOTORES GERAD TRANSF PAINEIS GABIN RACKS NOBREAK FONTES": "Painéis elétricos, transformadores a seco e grupos geradores",
    "ORGAOS PUBLICOS E INSTITUTOS": "Institutos de pesquisa, universidades e infraestrutura pública",
    "REFRESQUEIRAS / BEBEDOUROS / GELA CANECA": "Equipamentos comerciais de refrigeração e bebidas",
    "SETOR SUCROENERGETICO E AGRICOLA": "Setor sucroenergético, usinas e agroindústria",
    "SIDERURGIA METALURGIA E PECAS": "Siderurgia, metalurgia e fornos de processo",
    "TRANSPORTADORA": "Logística de transporte e movimentação de cargas",
    "UNID DE REFRIG CAMARAS FRIGOR PLUG-IN TUNEL DE CONGEL": "Câmaras frigoríficas, túneis de congelamento e refrigeração",
    "UNIDADE DE AGUA GELADA E TORRE DE CONGELAMENTO": "Chillers, unidades de água gelada e torres de resfriamento",
    "VENTILACAO EXAUSTAO SALAS LIMPAS E CAPELAS": "Salas limpas, capelas de laboratório e exaustão industrial"
}

def normalizar_segmento_mestre(s):
    """Normaliza qualquer segmento para português formal B2B ou retorna None se proibido."""
    if not s:
        return None
    s_raw = str(s).strip()
    s_clean = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚçÇâêôÂÊÔãõÃÕ ]', '', s_raw).upper().strip()
    
    # Verifica termos proibidos
    for f in FORBIDDEN_SEGMENTS:
        if f in s_clean:
            return None
            
    # Procura exato no dicionário
    if s_clean in SEGMENT_DICTIONARY:
        return SEGMENT_DICTIONARY[s_clean]
        
    for k, v in SEGMENT_DICTIONARY.items():
        k_clean = re.sub(r'[^a-zA-Z0-9 ]', '', k).upper().strip()
        if k_clean and (k_clean == s_clean or k_clean in s_clean or s_clean in k_clean):
            return v
            
    # Heurísticas adicionais
    if "TEXT" in s_clean:
        return "Indústria têxtil, tecelagem e fiações"
    if "CERAM" in s_clean or "CERÂM" in s_clean:
        return "Indústria cerâmica, olarias e fornos refratários"
    if "RESTAURAN" in s_clean or "HOTEL" in s_clean or "BARES" in s_clean:
        return "Cozinhas profissionais, restaurantes, hotelaria e food service"
    if "CALCAD" in s_clean or "CALÇAD" in s_clean:
        return "Indústria calçadista, coureira e conformação térmica"
    if "CLIMAT" in s_clean or "DESUMID" in s_clean or "QUEIMADOR" in s_clean:
        return "Climatização, desumidificação e sistemas de aquecimento"
    if "SALAS LIMPAS" in s_clean or "CAPELAS" in s_clean:
        return "Salas limpas, capelas de laboratório e exaustão industrial"
    if "COIFAS" in s_clean or "CHURRASQ" in s_clean:
        return "Ventilação de cozinhas profissionais, coifas e churrasqueiras"
    if "TUNEL" in s_clean or "CAMARAS FRIGOR" in s_clean or "CÂMARAS" in s_clean:
        return "Câmaras frigoríficas, túneis de congelamento e refrigeração"
    if "PAINEIS" in s_clean or "PAINÉIS" in s_clean or "TRANSF" in s_clean or "GERAD" in s_clean or "RACKS" in s_clean:
        return "Painéis elétricos, transformadores a seco e grupos geradores"
    if "COMPRESSOR" in s_clean:
        return "Compressores industriais e sistemas de ar comprimido"
    if "MEDIC" in s_clean or "MÉDIC" in s_clean or "HOSPITAL" in s_clean or "LABORAT" in s_clean:
        return "Equipamentos médicos, hospitalares e laboratoriais"
    if "SIDERURG" in s_clean or "METALURG" in s_clean:
        return "Siderurgia, metalurgia e fornos de processo"
    if "LEITE" in s_clean or "AGRIC" in s_clean or "AGRÍC" in s_clean:
        return "Máquinas agrícolas, agroindústria e resfriadores de leite"
    if "PLASTIC" in s_clean or "PLÁSTIC" in s_clean or "EMBALAG" in s_clean:
        return "Indústria plástica, transformadoras e embalagens"
    if "ALIMENT" in s_clean:
        return "Indústria alimentícia e processamento de alimentos"
    if "BEBIDAS" in s_clean or "CERVEJ" in s_clean:
        return "Indústria de bebidas, cervejarias e engarrafadoras"
    if "QUIM" in s_clean or "QUÍM" in s_clean or "FARMAC" in s_clean:
        return "Indústria química, farmacêutica e cosméticos"
        
    return s_raw.title()

def normalizar_equipamento_mestre(eq):
    """Limpa prefixos indesejados como 'Aplicação final provável' e travessões."""
    if not eq:
        return ""
    eq_str = str(eq).strip()
    eq_str = re.sub(r'(?i)aplica[çc][ãa]o\s+final\s+prov[áa]vel\s*[-–—:]*\s*', '', eq_str).strip()
    eq_str = re.sub(r'(?i)aplica[çc][ãa]o\s+prov[áa]vel\s*[-–—:]*\s*', '', eq_str).strip()
    return eq_str
