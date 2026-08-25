# -*- coding: utf-8 -*-
"""
Módulo de Regras de Validação - Política Zero Inferência
Demo Store - Catálogo B2B Industrial

Todas as regras definidas durante a fase piloto estão codificadas aqui.
O script gerador DEVE passar por estas validações antes de gerar o output.
"""

import re
from urllib.parse import urlparse, unquote


# ========================================================================
# REGRA 1: Dados sem fonte oficial = Confiança 0%
# ========================================================================
CAMPOS_QUE_EXIGEM_FONTE = [
    "vazao", "corrente", "potencia", "rpm", "rotacao",
    "ip", "grau_protecao", "ruido", "peso", "material",
    "vida_util", "temperatura", "pressao", "dimensoes"
]

def validar_confianca(spec):
    """
    Se o atributo é técnico sensível e não tem fonte oficial,
    a confiança DEVE ser 0% e o valor DEVE ser None.
    Retorna (is_valid, mensagem_erro).
    """
    atributo_lower = spec.get("atributo", "").lower()
    eh_sensivel = any(campo in atributo_lower for campo in CAMPOS_QUE_EXIGEM_FONTE)

    if eh_sensivel and spec.get("fonte") is None and spec.get("valor") is not None:
        return False, f'BLOQUEADO: "{spec["atributo"]}" tem valor "{spec["valor"]}" mas sem fonte. Zero Inferência violada.'

    if spec.get("confianca") == "100%" and spec.get("fonte") is None:
        return False, f'BLOQUEADO: "{spec["atributo"]}" marcado 100% mas sem fonte declarada.'

    return True, "OK"


# ========================================================================
# REGRA 2: Termos proibidos (compatibilidade sem comprovação)
# ========================================================================
TERMOS_PROIBIDOS = [
    "substitui 100%",
    "compatível 100%",
    "substitui diretamente",
    "mesma furação",
    "mesmo desempenho",
    "equivalente direto",
    "drop-in replacement",
    "plug and play",
    "encaixa perfeitamente",
    "faturamento",
    "faturamos",
    "cnpj",
    "revendas",
    "nota fiscal",
    "transportadora parceira com rastreamento",
    "o envio é realizado via transportadora",
    "fabril",
    "fabris",
    "suporte de engenharia dedicated",
    "engenharia dedicada",
    "suporte especializado de engenharia",
    "equipe de engenharia dedicada",
    "atendimento de engenharia personalizado",
    "substitui exaustores",
    "substitui ventiladores",
    "metalplan",
    "fibrasil",
    "ebm-papst",
    "ebm papst",
    "ziehl-abegg",
    "ziehl abegg",
    "sunon",
    "metaltex",
    "weiguang",
    "adda",
    "equivalente ebm",
    "modelo equivalente",
]

# Marcas/concorrentes — nunca em schema, SEO público, FAQ, resumo, aplicações, etc.
CONCORRENTES_PROIBIDOS_PUBLICO = [
    "ebm-papst", "ebm papst", "ziehl-abegg", "ziehl abegg",
    "sunon", "metaltex", "weiguang", "adda", "asten", "elgin",
    "danfoss", "brahex", "soon", "metalplan", "fibrasil",
]

def validar_termos_proibidos(texto):
    """
    Verifica se o texto contém afirmações de compatibilidade
    sem comprovação técnica. Retorna (is_valid, termos_encontrados).
    """
    encontrados = []
    texto_lower = texto.lower()
    for termo in TERMOS_PROIBIDOS:
        if termo in texto_lower:
            encontrados.append(termo)

    if encontrados:
        return False, encontrados
    return True, []


# ========================================================================
# REGRA 3: Alerta de instalação elétrica obrigatório para trifásicos
# ========================================================================
ALERTA_TRIFASICO_PADRAO = (
    "Motores trifásicos possuem diferentes formas de fechamento elétrico "
    "(estrela ou triângulo). Consulte sempre o diagrama presente na placa "
    "do motor ou no manual do fabricante para determinar o fechamento correto. "
    "Recomendamos que a instalação seja feita exclusivamente por profissional qualificado."
)

def validar_alerta_trifasico(produto_data):
    """
    Se o produto é trifásico, o alerta de instalação é obrigatório.
    Retorna (is_valid, mensagem).
    """
    eh_trifasico = produto_data.get("motor_trifasico", False)

    # Detectar também pela tensão
    tensoes_trif = ["220/380", "380v", "440v", "trifásico", "trifasico"]
    for spec in produto_data.get("especificacoes", []):
        val = str(spec.get("valor", "")).lower()
        if any(t in val for t in tensoes_trif):
            eh_trifasico = True
            break

    if eh_trifasico:
        alerta = produto_data.get("alerta_tecnico", "")
        if not alerta or len(alerta) < 20:
            return False, "BLOQUEADO: Produto trifásico detectado mas sem alerta de instalação elétrica."

    return True, "OK"


# ========================================================================
# REGRA 4: Aviso de transparência obrigatório quando há specs pendentes
# ========================================================================
AVISO_SPECS_PENDENTES = (
    "Especificações elétricas detalhadas (corrente, potência, vazão e grau IP) "
    "devem ser consultadas na ficha técnica oficial do fabricante mediante "
    "solicitação comercial."
)

def validar_aviso_pendentes(produto_data):
    """
    Se há specs com confiança 0%, o produto DEVE ter o aviso de
    transparência comercial. Retorna (is_valid, mensagem).
    """
    tem_pendente = any(
        s.get("confianca") == "0%"
        for s in produto_data.get("especificacoes", [])
    )
    if not tem_pendente:
        return True, "OK"

    # Verificar se o alerta existe
    alerta = produto_data.get("alerta_tecnico", "")
    if not alerta:
        return False, "BLOQUEADO: Existem specs com 0% de confiança mas sem aviso de transparência."

    return True, "OK"


# ========================================================================
# REGRA 5: Checklist de reposição obrigatório
# ========================================================================
CHECKLIST_REPOSICAO_PADRAO = [
    "Vazão (m³/h)",
    "Rotação (RPM)",
    "Potência (W)",
    "Corrente (A)",
    "Sentido de fluxo",
    "Furação de fixação",
    "Tensão (V)",
    "Frequência (Hz)",
]


# ========================================================================
# PÓS-GERAÇÃO: bloqueia publicação se houver defeitos estruturais
# ========================================================================
# Ortografia / typos recorrentes do gerador (chave = forma errada em lower)
TYPOS_PT_BASICOS = {
    "graoss": "grãos",
    "grãoss": "grãos",
    "graosss": "grãos",
    "exaustãos": "exaustão",
    "industrials": "industriais",
    "evaporadors": "evaporadores",
    "manutencaos": "manutenções",
    "condensadors": "condensadores",
    "climatizadors": "climatizadores",
    "frigorificas": "frigoríficas",
    "frigorificos": "frigoríficos",
    "maquina ": "máquina ",
    "maquinas": "máquinas",
    "contnuo": "contínuo",
    "termoplastico": "termoplástico",
    "ul94-0": "UL94V-0",
}

# Acentos / formas canônicas (aplicadas por sanitizar_texto)
ACENTOS_PT = {
    "movimentacao": "movimentação",
    "refrigeracao": "refrigeração",
    "climatizacao": "climatização",
    "ventilacao": "ventilação",
    "exaustao": "exaustão",
    "protecao": "proteção",
    "mecanica": "mecânica",
    "mecanico": "mecânico",
    "operacao": "operação",
    "continuo": "contínuo",
    "continua": "contínua",
    "helice": "hélice",
    "tensao": "tensão",
    "frequencia": "frequência",
    "rotacao": "rotação",
    "potencia": "potência",
    "isolacao": "isolação",
    "dimensoes": "dimensões",
    "selecao": "seleção",
    "manutencao": "manutenção",
    "reposicao": "reposição",
    "distribuicao": "distribuição",
    "alimentacao": "alimentação",
    "ligacao": "ligação",
    "descricao": "descrição",
    "aplicacoes": "aplicações",
    "industria": "indústria",
    "industrias": "indústrias",
    "eletrico": "elétrico",
    "eletrica": "elétrica",
    "eletricos": "elétricos",
    "termica": "térmica",
    "termico": "térmico",
    "termicos": "térmicos",
    "solidas": "sólidas",
    "solidos": "sólidos",
    "agua": "água",
    "uteis": "úteis",
    "periodo": "período",
    "periodos": "períodos",
    "camara": "câmara",
    "camaras": "câmaras",
    "tuneis": "túneis",
    "tunel": "túnel",
    "aco": "aço",
    "po": "pó",
    "poliester": "poliéster",
    "resistencia": "resistência",
    "estabilidade": "estabilidade",
    "condicoes": "condições",
    "exigencias": "exigências",
    "servicos": "serviços",
    "ceramica": "cerâmica",
    "quimica": "química",
    "farmaceutica": "farmacêutica",
    "eletronicos": "eletrônicos",
    "eletronica": "eletrônica",
    "paineis": "painéis",
    "graos": "grãos",
    "grao": "grão",
    "util": "útil",
    "lacteo": "lácteo",
    "lacteos": "lácteos",
    "trifasica": "trifásica",
    "monofasica": "monofásica",
    "bimetalico": "bimetálico",
    "atraves": "através",
    "Atraves": "Através",
    "dinamico": "dinâmico",
    "emissao": "emissão",
    "acustica": "acústica",
    "reducao": "redução",
    "vibracoes": "vibrações",
    "vibracao": "vibração",
    "particulas": "partículas",
    "versao": "versão",
    "versoes": "versões",
    "criogenicos": "criogênicos",
    "criogenico": "criogênico",
    "furacao": "furação",
    "vazao": "vazão",
    "pressao": "pressão",
    "ruido": "ruído",
    "nivel": "nível",
    "tecnica": "técnica",
    "tecnico": "técnico",
    "tecnicas": "técnicas",
    "tecnicos": "técnicos",
    "ate ": "até ",
    "tambem": "também",
    "nao ": "não ",
    "sao ": "são ",
    "ja ": "já ",
    "circulacao": "circulação",
    "forcada": "forçada",
    "conservacao": "conservação",
    "exposicao": "exposição",
    "ventilacao": "ventilação",
    "exaustao": "exaustão",
    "insuflacao": "insuflação",
    "operacao": "operação",
    "operacoes": "operações",
    "aplicacao": "aplicação",
    "aplicacoes": "aplicações",
    "manutencao": "manutenção",
    "refrigeracao": "refrigeração",
    "instalacao": "instalação",
    "instalacoes": "instalações",
    "protecao": "proteção",
    "posicao": "posição",
    "posicoes": "posições",
    "fixacao": "fixação",
    "rotacao": "rotação",
    "substituicao": "substituição",
    "solucao": "solução",
    "solucoes": "soluções",
    "dimensao": "dimensão",
    "dimensoes": "dimensões",
    "duracao": "duração",
    "projecao": "projeção",
    "relacao": "relação",
    "opcao": "opção",
    "opcoes": "opções",
    "funcao": "função",
    "funcoes": "funções",
    "direcao": "direção",
    "geracao": "geração",
    "degradacao": "degradação",
    "elevacao": "elevação",
    "atuacao": "atuação",
    "camara": "câmara",
    "camaras": "câmaras",
    "frigorifica": "frigorífica",
    "frigorificas": "frigoríficas",
    "termica": "térmica",
    "termicas": "térmicas",
    "termico": "térmico",
    "termicos": "térmicos",
    "eletrica": "elétrica",
    "eletricas": "elétricas",
    "eletrico": "elétrico",
    "eletricos": "elétricos",
    "mecanica": "mecânica",
    "mecanicas": "mecânicas",
    "mecanico": "mecânico",
    "mecanicos": "mecânicos",
    "rapida": "rápida",
    "rapido": "rápido",
    "modulo": "módulo",
    "modulos": "módulos",
    "tunel": "túnel",
    "tuneis": "túneis",
    "automacao": "automação",
    "telecomunicacao": "telecomunicação",
    "telecomunicacoes": "telecomunicações",
    "ntilação": "ventilação",
    "ntilacao": "ventilação",
}

# Em mercado NÃO pode aparecer uso técnico copiado de Aplicações (frases, não setores)
PROIBIDO_EM_MERCADO = [
    "com aplicações em",
    "com aplicacoes em",
    "é utilizado em",
    "e utilizado em",
    "utilizado em ",
    "movimentacao de ar em",
    "movimentação de ar em",
    "resfriamento de motores",
    "resfriamento de motores, painéis",
    "resfriamento de motores, paineis",
    "exaustão de calor em máquinas",
    "exaustao de calor em maquinas",
    "na refrigeração comercial, é utilizado",
    "na refrigeracao comercial, e utilizado",
    "trocador de calor e resfriamento",
]

# Em títulos de Aplicações NÃO pode aparecer setor/mercado comprador
PROIBIDO_EM_APLICACAO = [
    "mercado de",
    "setor de",
    "segmento de",
    "indústria de",
    "industria de",
    "manutenção industrial e reposição",
    "manutencao industrial e reposicao",
    "refrigeração comercial e industrial",
    "refrigeracao comercial e industrial",
    "distribuição técnica",
    "distribuicao tecnica",
    "varejo alimentar",
    "oem",
    "integradores",
]

# Frases de marketing / copy genérico — proibidas (Zero Inferência)
FRASES_MARKETING_INVENTADAS = [
    "instalação simplificada",
    "instalacao simplificada",
    "alto rendimento",
    "alta performance",
    "excelente estabilidade",
    "vida útil estendida",
    "vida util estendida",
    "resistência mecânica elevada",
    "resistencia mecanica elevada",
    "garante a troca térmica ideal",
    "garante a troca termica ideal",
    "proporciona resfriamento uniforme",
    "fornece fluxo de ar constante",
    "auxilia na exaustão de calor",
    "auxilia na exaustao de calor",
    "ideal para controle térmico",
    "ideal para controle termico",
    "ideal para manter o fluxo",
    "ideal para manter",
    "equipamento de alta performance",
    "alta performance desenvolvido",
    "materiais de alto desempenho",
    "desenvolvido com materiais de alto desempenho",
    "construção robusta e durável",
    "construcao robusta e duravel",
    "construção robusta para ambiente industrial",
    "construcao robusta para ambiente industrial",
    "focado na dissipação térmica",
    "focado na dissipacao termica",
    "alto desempenho em aplicações industriais",
    "alto desempenho em aplicacoes industriais",
    "balanceamento dinâmico conforme iso 1940",
    "balanceamento dinamico conforme iso 1940",
    "missão crítica",
    "missao critica",
    "perdas incalculáveis",
    "padrão da indústria",
    "máxima proteção",
    "prevencao de superaquecimento",
    "prevenção de superaquecimento",
    "pressão estática elevada",
    "pressao estatica elevada",
    "ampla faixa térmica",
    "ampla faixa termica",
    "prolonga a vida útil",
    "prolonga a vida util",
    "adequação ao ambiente industrial",
    "adequacao ao ambiente industrial",
    "alta eficiência",
    "alta eficiencia",
    "mancal reforçado",
    "mancal reforcado",
    "paradas não programadas",
    "paradas nao programadas",
    "atuando com alta eficiência",
    "atuando com alta eficiencia",
    # Template Antigravity / copy repetido (bloqueio absoluto)
    "este fator é crucial para garantir a durabilidade e estabilidade do sistema mecânico ao longo dos anos",
    "este fator e crucial para garantir a durabilidade e estabilidade do sistema mecanico ao longo dos anos",
    "configuração validada e atestada pela engenharia térmica da sell-parts",
    "configuracao validada e atestada pela engenharia termica da sell-parts",
    "projetado para exaustão e movimentação de ar com controle eletrônico de velocidade otimizado",
    "projetado para exaustao e movimentacao de ar com controle eletronico de velocidade otimizado",
    "construção declarada no datasheet",
    "construcao declarada no datasheet",
]

# Frases que NÃO podem se repetir entre cards (benefícios / diferenciais)
FRASES_TEMPLATE_BLOQUEADAS = [
    "este fator é crucial para garantir a durabilidade e estabilidade do sistema mecânico ao longo dos anos",
    "este fator e crucial para garantir a durabilidade e estabilidade do sistema mecanico ao longo dos anos",
    "configuração validada e atestada pela engenharia térmica da sell-parts",
    "configuracao validada e atestada pela engenharia termica da sell-parts",
    "construção declarada no datasheet",
    "construcao declarada no datasheet",
]

# Sufixos inventados em títulos de aplicação (não vêm da planilha)
SUFIXOS_APLICACAO_INVENTADOS = [
    " e sistemas frigoríficos",
    " e sistemas frigorificos",
    " e climatizadores",
    " e instalações industriais",
    " e instalacoes industriais",
    " e sistemas industriais",
    " e instalações técnicas",
    " e instalacoes tecnicas",
    "freezers e plug-ins",
    "ultracongeladores e",
    "chillers e trocadores",
]

# Descrições-padrão genéricas / inventadas (fora da planilha)
DESCRICOES_APLICACAO_INVENTADAS = [
    "garante a troca térmica ideal em regime contínuo",
    "garante a troca termica ideal em regime continuo",
    "proporciona resfriamento uniforme em ambientes",
    "fornece fluxo de ar constante em evaporadores",
    "auxilia na exaustão de calor de compressores",
    "auxilia na exaustao de calor de compressores",
    "garante a exaustão ou ventilação ideal",
    "garante a exaustao ou ventilacao ideal",
    "circulação forçada de ar por serpentinas",
    "circulacao forcada de ar por serpentinas",
    "ventilação de equipamentos de conservação e exposição",
    "ventilacao de equipamentos de conservacao e exposicao",
    "movimento de ar para troca térmica e congelamento",
    "movimento de ar para troca termica e congelamento",
    "congelamento rápido de alimentos",
    "congelamento rapido de alimentos",
    "ventilação de serpentinas e conjuntos",
    "ventilacao de serpentinas e conjuntos",
]

RE_PALAVRA_DUPLICADA = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE | re.UNICODE)
RE_ESPACO_ANTES_PONTUACAO = re.compile(r"\s+([,.;:!?])")
RE_FALTA_ESPACO_APOS = re.compile(r"([,.;:!?])([A-Za-zÀ-ÿ])")
RE_ESPACOS_DUPLOS = re.compile(r" {2,}")
RE_UNIDADE_COLADA = re.compile(
    r"\b(\d+(?:[.,]\d+)?)\s*(mm|cm|m|v|w|kw|hz|rpm|dba|a|kg|°c|c)\b",
    re.IGNORECASE,
)


def sanitizar_texto(texto):
    """Corrige typos, acentos comuns e pontuação básica. Não inventa conteúdo."""
    if not isinstance(texto, str) or not texto:
        return texto
    out = texto
    # typos explícitos primeiro
    for errado, certo in TYPOS_PT_BASICOS.items():
        out = re.sub(re.escape(errado), certo, out, flags=re.IGNORECASE)
    # acentos (sempre com word-boundary — evita "tipo" → "tipó" via "po")
    for errado, certo in sorted(ACENTOS_PT.items(), key=lambda x: -len(x[0])):
        token = errado.rstrip()
        out = re.sub(rf"\b{re.escape(token)}\b", certo.rstrip(), out, flags=re.IGNORECASE)
    # pontuação
    out = RE_ESPACO_ANTES_PONTUACAO.sub(r"\1", out)
    out = RE_FALTA_ESPACO_APOS.sub(r"\1 \2", out)
    out = RE_ESPACOS_DUPLOS.sub(" ", out)
    # unidades: "250mm" → "250 mm" e normaliza dBA
    def _unit(m):
        num, u = m.group(1), m.group(2)
        u_norm = "dBA" if u.lower() == "dba" else u
        if u_norm.lower() == "c" and "°" not in m.group(0):
            # evita quebrar "classe F" etc — só corrige padrões tipo "-30 C"
            return f"{num} {u_norm.upper() if u_norm.lower() in ('v', 'w', 'a', 'hz') else u_norm}"
        return f"{num} {u_norm}"
    out = RE_UNIDADE_COLADA.sub(_unit, out)
    out = out.replace(" dba", " dBA").replace(" Dba", " dBA")
    # "e" verbal → "é" em padrões seguros
    for pat, repl in (
        (r"\bQual e a\b", "Qual é a"),
        (r"\bqual e a\b", "qual é a"),
        (r"\be utilizado\b", "é utilizado"),
        (r"\be especificamente\b", "é especificamente"),
        (r"\be um requisito\b", "é um requisito"),
        (r"\be puxada\b", "é puxada"),
        (r"\boperacao e (?=\d)", "operação é "),
        (r"\boperação e (?=\d)", "operação é "),
        (r"\bfrequencia de operacao e\b", "frequência de operação é"),
        (r"\bfrequência de operação e\b", "frequência de operação é"),
        (r"\bO modelo e\b", "O modelo é"),
        (r"\bo modelo e\b", "o modelo é"),
        (r"\bdemanda e\b", "demanda é"),
        (r"\bconfiabilidade sob regime S1 e requisito\b", "confiabilidade sob regime S1 é requisito"),
        # Linguagem técnica natural / neutra (sem redundâncias entre parênteses)
        (r"para insuflac[aã]o \(sopramento\)", "para insuflação de ar, proporcionando fluxo direcionado para aplicações de sopramento em sistemas industriais e comerciais"),
        (r"para insuflac[aã]o\b", "para insuflação de ar em sistemas industriais e comerciais"),
        (r"para exaustac[aã]o\b", "para exaustão de ar em sistemas industriais e comerciais"),
    ):
        out = re.sub(pat, repl, out)
    return out.strip() if out.strip() != texto.strip() or out != texto else out


def sanitizar_produto(produto_data):
    """Aplica sanitizar_texto em todos os campos textuais do produto (in-place)."""
    for campo in ("resumo_tecnico", "alerta_tecnico", "mercado"):
        if produto_data.get(campo):
            txt = sanitizar_texto(produto_data[campo])
            if txt and len(txt) > 5 and txt.strip()[-1] not in ".!?":
                txt = txt.strip() + "."
            produto_data[campo] = txt
    produto_data["hero_checklist"] = [
        sanitizar_texto(str(x)) for x in (produto_data.get("hero_checklist") or [])
    ]
    for faq in produto_data.get("faq") or []:
        if "pergunta" in faq:
            faq["pergunta"] = sanitizar_texto(faq["pergunta"])
        if "resposta" in faq:
            faq["resposta"] = sanitizar_texto(faq["resposta"])
    for ben in produto_data.get("beneficios") or []:
        if isinstance(ben, dict):
            if ben.get("titulo"):
                ben["titulo"] = sanitizar_texto(ben["titulo"])
            if ben.get("descricao"):
                ben["descricao"] = sanitizar_texto(ben["descricao"])
    apps = produto_data.get("aplicacoes") or []
    novos = []
    for app in apps:
        if isinstance(app, dict):
            tit = sanitizar_texto(app.get("titulo", "") or app.get("equipamento", ""))
            desc = sanitizar_texto(app.get("descricao", ""))
            if tit:
                tit = tit[0].upper() + tit[1:]
            if desc:
                desc = desc[0].upper() + desc[1:]
                if not desc.endswith("."):
                    desc += "."
            novos.append({
                **app,
                "titulo": tit,
                "descricao": desc,
            })
        else:
            txt = sanitizar_texto(str(app))
            if txt:
                txt = txt[0].upper() + txt[1:]
                if not txt.endswith("."):
                    txt += "."
            novos.append(txt)
    produto_data["aplicacoes"] = novos
    produto_data["diferenciais"] = [
        sanitizar_texto(str(d)) for d in (produto_data.get("diferenciais") or [])
    ]
    return produto_data


def _textos_do_produto(produto_data):
    def _to_str(val):
        if isinstance(val, dict):
            return str(val.get("texto") or val.get("descricao") or val)
        return str(val or "")

    textos = [
        _to_str(produto_data.get("resumo_tecnico")),
        _to_str(produto_data.get("alerta_tecnico")),
        _to_str(produto_data.get("mercado")),
    ]
    for item in produto_data.get("hero_checklist", []) or []:
        textos.append(_to_str(item))
    for faq in produto_data.get("faq", []) or []:
        textos.append(_to_str(faq.get("pergunta")))
        textos.append(_to_str(faq.get("resposta")))
    for beneficio in produto_data.get("beneficios", []) or []:
        textos.append(_to_str(beneficio.get("titulo")))
        textos.append(_to_str(beneficio.get("descricao")))
    for app in produto_data.get("aplicacoes", []) or []:
        if isinstance(app, dict):
            textos.append(_to_str(app.get("titulo")))
            textos.append(_to_str(app.get("descricao")))
        else:
            textos.append(_to_str(app))
    for dif in produto_data.get("diferenciais", []) or []:
        textos.append(_to_str(dif))
    return textos


def validar_palavras_duplicadas(produto_data):
    erros = []
    for texto in _textos_do_produto(produto_data):
        for m in RE_PALAVRA_DUPLICADA.finditer(texto or ""):
            erros.append(f"BLOQUEADO: palavra duplicada '{m.group(0)}'.")
    return len(erros) == 0, erros


def validar_typos_basicos(produto_data):
    erros = []
    blob = "\n".join(_textos_do_produto(produto_data)).lower()
    for errado, certo in TYPOS_PT_BASICOS.items():
        if errado in blob:
            erros.append(f"BLOQUEADO: typo '{errado}' (use '{certo}').")
    return len(erros) == 0, erros


def validar_pontuacao_basica(produto_data):
    """Falta de espaço após vírgula/ponto, espaço antes de pontuação, espaços duplos."""
    erros = []
    for texto in _textos_do_produto(produto_data):
        if not texto:
            continue
        if RE_ESPACO_ANTES_PONTUACAO.search(texto):
            erros.append("BLOQUEADO: espaço antes de pontuação (,.;:!?)." )
            break
        if RE_FALTA_ESPACO_APOS.search(texto):
            erros.append("BLOQUEADO: falta espaço após pontuação.")
            break
        if RE_ESPACOS_DUPLOS.search(texto):
            erros.append("BLOQUEADO: espaços duplos no texto.")
            break
    # Parágrafos longos de mercado/resumo devem terminar com pontuação
    for campo in ("resumo_tecnico", "mercado"):
        bloco = produto_data.get(campo) or ""
        if isinstance(bloco, dict):
            bloco = bloco.get("texto", "") or str(bloco)
        for para in re.split(r"\n\s*\n", str(bloco)):
            p = para.strip()
            if len(p) >= 60 and p[-1] not in ".!?":
                erros.append(
                    f"BLOQUEADO: parágrafo de '{campo}' sem ponto final "
                    f"('{p[:40]}...')."
                )
    return len(erros) == 0, erros


def _basename_imagem(url_ou_path):
    path = urlparse(str(url_ou_path)).path if "://" in str(url_ou_path) else str(url_ou_path)
    return unquote(path.rsplit("/", 1)[-1]).lower().strip()


def validar_imagens_unicas(produto_data):
    imgs = produto_data.get("imagens") or produto_data.get("gallery") or []
    if not imgs:
        return True, []
    vistos = set()
    dups = []
    for img in imgs:
        key = _basename_imagem(img)
        if not key:
            continue
        if key in vistos:
            dups.append(key)
        vistos.add(key)
    if dups:
        return False, [f"BLOQUEADO: imagens duplicadas no produto: {sorted(set(dups))}"]
    return True, []


def validar_separacao_aplicacoes_mercado(produto_data):
    """
    REGRA ESTRITA — sem redundância:
    - Aplicações = equipamento / uso técnico direto
    - Mercado = setor / indústria / perfil de comprador
    """
    apps = produto_data.get("aplicacoes", []) or []
    mercado = produto_data.get("mercado") or ""
    if isinstance(mercado, dict):
        mercado = mercado.get("texto", "") or str(mercado)
    mercado_l = str(mercado).lower()
    erros = []

    if not mercado_l:
        return True, []

    for frag in PROIBIDO_EM_MERCADO:
        if frag in mercado_l:
            erros.append(
                f"BLOQUEADO: mercado mistura aplicação/equipamento ('{frag}'). "
                "Mercado = setores compradores; Aplicações = uso técnico."
            )

    for app in apps:
        titulo = (app.get("titulo") if isinstance(app, dict) else str(app) or "").strip()
        titulo_l = titulo.lower()
        desc_l = (app.get("descricao", "") if isinstance(app, dict) else "").lower()
        if len(titulo) >= 12 and titulo_l in mercado_l:
            erros.append(
                f"BLOQUEADO: título de aplicação repetido em mercado ('{titulo[:60]}')."
            )
        for frag in PROIBIDO_EM_APLICACAO:
            if frag in titulo_l or frag in desc_l:
                erros.append(
                    f"BLOQUEADO: aplicação usa linguagem de mercado ('{frag}'). "
                    "Use equipamento/uso técnico no título."
                )
                break

    return len(erros) == 0, erros


def extrair_setores_do_mercado(mercado):
    """Extrai setores do 1º parágrafo válido do campo mercado."""
    if isinstance(mercado, dict):
        mercado = mercado.get("texto", "") or str(mercado)
    m = re.search(
        r"atende prioritariamente os setores de ([^\n.]+)",
        str(mercado) if mercado else "",
        re.IGNORECASE,
    )
    if not m:
        return None
    partes = [p.strip() for p in m.group(1).split(",") if p.strip()]
    return partes[:5] if partes else None


def gerar_texto_mercado(sku, mercados, eh_bt=False):
    """
    REGRA 8 — Mercado: apenas setores/indústrias compradoras (planilha).
    Nunca equipamentos nem usos técnicos (isso vai em aplicacoes).
    """
    m = list(mercados or [])[:5]
    while len(m) < 5:
        m.append(m[-1] if m else "reposição técnica industrial")

    blocos = [
        (
            f"O modelo {sku} atende prioritariamente os setores de "
            f"{', '.join(m[:3]).lower()}."
        ),
        (
            f"No segmento de {m[1].lower()}, a demanda é puxada por integradores, "
            f"OEMs e equipes de manutenção que operam em regime contínuo."
        ),
        (
            f"O setor de {m[3].lower()} representa parcela significativa da demanda "
            f"de reposição técnica multimarcas."
        ),
    ]
    if eh_bt:
        blocos.append(
            "A versão BT (Baixa Temperatura) é especificamente projetada para o "
            "mercado de frio negativo até -40 °C (fabricantes e integradoras de "
            "câmaras e túneis)."
        )
    else:
        blocos.append(
            f"Adicionalmente, atende o mercado de {m[4].lower()}, onde "
            f"confiabilidade sob regime S1 é requisito de compra."
        )
    txt = "\n\n".join(blocos)
    txt = txt.replace("b2b", "B2B").replace("B2b", "B2B")
    return sanitizar_texto(txt)


def gerar_aplicacoes_padrao(equipamentos, aplicacoes_excel=None, total=4):
    """
    REGRA 9 — Aplicações só com vocabulário da planilha:
      titulo    = nome do equipamento (lista equipamentos)
      descricao = linha técnica (lista aplicacoes_excel)
    Sem sufixos inventados nem copy genérico.
    """
    eq = list(equipamentos or [])
    excel = list(aplicacoes_excel or [])
    if len(eq) < total:
        raise ValueError(
            f"equipamentos incompleto: {len(eq)} itens (necessário {total}). "
            "Use apenas termos da planilha de SEO."
        )
    if len(excel) < total:
        raise ValueError(
            f"aplicacoes_excel incompleto: {len(excel)} itens (necessário {total}). "
            "Use apenas termos da planilha de SEO."
        )
    apps = []
    for i in range(total):
        apps.append({
            "titulo": sanitizar_texto(eq[i]),
            "descricao": sanitizar_texto(excel[i]),
        })
    return apps


def _spec_map(produto_ou_fonte):
    """Extrai mapa atributo→valor de especificacoes[] ou dict fonte."""
    if isinstance(produto_ou_fonte, dict) and "especificacoes" in produto_ou_fonte:
        m = {}
        for s in produto_ou_fonte.get("especificacoes") or []:
            atr = (s.get("atributo") or "").strip().lower()
            val = (s.get("valor") or "").strip()
            if atr and val and val.lower() not in ("não informado", "nao informado", "n/a"):
                m[atr] = val
        # campos soltos
        for k in (
            "tensao", "potencia", "velocidade", "corrente", "ruido", "peso",
            "temperatura", "protecao_mecanica", "mancais", "isolacao",
            "alimentacao", "regime", "material_helice", "caixa_ligacao",
            "protecao_eletrica", "descricao_ds", "sku",
        ):
            if produto_ou_fonte.get(k) and k not in m:
                m[k] = str(produto_ou_fonte[k])
        return m
    return {k: str(v) for k, v in (produto_ou_fonte or {}).items() if v}


def gerar_resumo_tecnico_datasheet(p, funcao=None):
    """Resumo em 2 parágrafos — descricao_ds + construção do datasheet."""
    desc = (p.get("descricao_ds") or "").strip()
    sku = p.get("sku", "")
    mancais = normalizar_mancais(p.get("mancais", ""))
    funcao_txt = (funcao or "ventilação").strip().lower()

    if desc.endswith("."):
        desc = desc[:-1]

    para1 = (
        f"{desc}, projetado para {funcao_txt} e movimentação de ar em equipamentos "
        f"de refrigeração, climatização e processos industriais."
    )

    para2 = (
        f"Construído para operação contínua sob regime {p.get('regime', '')}, o modelo {sku} oferece "
        f"proteção mecânica {p.get('protecao_mecanica', '')} e utiliza {mancais.lower()}. "
        f"O conjunto suporta faixa térmica de {p.get('temperatura', '')}, com emissão de ruído de {p.get('ruido', '')}."
    )

    return sanitizar_texto(f"{para1}\n\n{para2}")


def gerar_beneficios_datasheet(p, mancais=None):
    """
    4 benefícios ancorados no datasheet — cada um com CONCLUSÃO ÚNICA
    (proibido sufixo repetido tipo 'Este fator é crucial...').
    """
    mancais = normalizar_mancais(mancais or p.get("mancais", ""))
    sku = p.get("sku", "")
    ip = p.get("protecao_mecanica") or ""
    ruido = p.get("ruido") or ""
    temp = p.get("temperatura") or ""
    pot = p.get("potencia") or ""
    tensao = p.get("tensao") or ""
    alimentacao = p.get("alimentacao") or ""
    regime = p.get("regime") or "S1"
    material = p.get("material_helice") or ""
    isolacao = p.get("isolacao") or ""
    corrente = p.get("corrente") or ""
    vel = p.get("velocidade") or ""
    eh_ec = "EC" in sku.upper() or "ec" in (p.get("slug") or "")

    b1_titulo = "Tecnologia EC (comutação eletrônica)" if eh_ec else f"Proteção mecânica {ip or 'declarada'}"
    if eh_ec:
        b1_desc = (
            f"Motor EC do modelo {sku}"
            + (f" com potência {pot}" if pot else "")
            + " para modulação de velocidade sob demanda, "
            "reduzindo consumo em regime contínuo sem depender de inversor externo dedicado."
        )
    else:
        b1_desc = (
            f"Grau de proteção {ip} no datasheet Sell-Parts para {regime}, "
            "limitando ingresso de poeira e umidade na caixa de ligação e no conjunto elétrico."
        )

    b2_titulo = f"Mancais: {mancais}" if mancais else f"Regime {regime}"
    b2_desc = (
        f"Conjunto com {mancais.lower()} no modelo {sku}, adequado a operação contínua "
        f"({regime}), reduzindo intervenções de manutenção em serviço 24/7."
        if mancais
        else f"Regime de trabalho {regime} declarado para o modelo {sku}."
    )

    b3_titulo = f"Faixa térmica {temp}" if temp else f"Alimentação {alimentacao} {tensao}".strip()
    if temp:
        b3_desc = (
            f"Operação na faixa {temp}"
            + (f", isolamento classe {isolacao}" if isolacao else "")
            + (f", material {material.lower()}" if material else "")
            + " — parâmetros que o comprador B2B deve cruzar com a condição real do equipamento."
        )
    else:
        b3_desc = (
            f"Alimentação {alimentacao} {tensao}".strip()
            + (f", corrente {corrente}" if corrente else "")
            + (f", rotação {vel}" if vel else "")
            + f" conforme ficha técnica do {sku}."
        )

    if ruido and "não" not in ruido.lower() and "nao" not in ruido.lower():
        b4_titulo = f"Nível de ruído {ruido}"
        b4_desc = (
            f"Pressão sonora de {ruido} declarada para o {sku}, útil para dimensionar "
            "conforto acústico em câmaras, salas de máquinas e áreas com restrição de ruído."
        )
    else:
        b4_titulo = f"Alimentação {alimentacao} {tensao}".strip() or f"Dados elétricos {sku}"
        b4_desc = (
            (f"Potência {pot}, " if pot else "")
            + (f"corrente {corrente}, " if corrente else "")
            + (f"rotação {vel}. " if vel else "")
            + "Valores oficiais do datasheet — use a tabela de especificações como referência única."
        )

    return [
        {"titulo": sanitizar_texto(b1_titulo), "descricao": sanitizar_texto(b1_desc)},
        {"titulo": sanitizar_texto(b2_titulo), "descricao": sanitizar_texto(b2_desc)},
        {"titulo": sanitizar_texto(b3_titulo), "descricao": sanitizar_texto(b3_desc)},
        {"titulo": sanitizar_texto(b4_titulo), "descricao": sanitizar_texto(b4_desc)},
    ]


def gerar_diferenciais_datasheet(p, eh_bt=False):
    """
    4 diferenciais só com dados do datasheet.
    A frase de validação Sell-Parts, se usada, aparece no MÁXIMO 1 item.
    """
    sku = p.get("sku", "")
    items = []
    desc = (p.get("descricao_ds") or "").strip()
    if desc:
        items.append(f"Modelo {sku}: {desc}")
    else:
        items.append(f"Modelo {sku} conforme datasheet oficial Sell-Parts.")

    if eh_bt and "-40" in str(p.get("temperatura", "")):
        items.append(
            f"Versão BT: temperatura {p.get('temperatura')} com graxa adequada a frio negativo, "
            f"conforme datasheet oficial do modelo {sku}."
        )
    elif p.get("temperatura"):
        iso = f", isolamento classe {p['isolacao']}" if p.get("isolacao") else ""
        items.append(
            f"Temperatura de operação {p['temperatura']}{iso}, parâmetro declarado no datasheet "
            f"do modelo {sku} para seleção em regime contínuo."
        )
    else:
        items.append(
            f"Proteção mecânica {p.get('protecao_mecanica', 'conforme datasheet')} "
            f"e regime {p.get('regime', 'S1')} no modelo {sku}, conforme ficha técnica."
        )

    elet = " ".join(
        x for x in [
            p.get("alimentacao"),
            p.get("tensao"),
            f"potência {p['potencia']}" if p.get("potencia") else "",
            f"velocidade {p['velocidade']}" if p.get("velocidade") else "",
            f"corrente {p['corrente']}" if p.get("corrente") else "",
        ] if x
    ).strip()
    items.append(elet + "." if elet else f"Parâmetros elétricos do {sku} na tabela de especificações.")

    fecha = []
    if p.get("ruido") and "não" not in str(p.get("ruido")).lower():
        fecha.append(f"ruído {p['ruido']}")
    if p.get("peso"):
        fecha.append(f"peso {p['peso']}")
    if p.get("caixa_ligacao"):
        fecha.append(f"caixa de ligação: {p['caixa_ligacao']}")
    # Validação Sell-Parts UMA vez só, no último item se houver espaço
    if fecha:
        trecho = ", ".join(fecha)
        trecho = trecho[0].upper() + trecho[1:]
        items.append(
            f"{trecho}. Configuração validada pela engenharia Sell-Parts "
            f"com base no datasheet do {sku}."
        )
    else:
        items.append(
            f"Configuração validada pela engenharia Sell-Parts com base no datasheet do {sku}."
        )

    while len(items) < 4:
        items.append(f"Consulte o datasheet oficial do modelo {sku} para demais parâmetros.")
    return [sanitizar_texto(x) for x in items[:4]]


def gerar_faq_tecnico(p):
    """
    FAQ que agrega valor — NÃO só repetir tensão/potência/IP já no hero/tabela.
    Sem inventar vazão/L10/certificação se não estiver no datasheet.
    """
    sku = p.get("sku", "")
    faq = [
        {
            "pergunta": f"O que validar antes de substituir outro ventilador pelo {sku}?",
            "resposta": (
                f"Antes da substituição pelo {sku}, confira na etiqueta/datasheet: tensão, "
                f"corrente, potência, rotação, sentido de fluxo, grau IP e furação de fixação. "
                f"A Sell-Parts recomenda cruzar esses itens com o equipamento original; "
                f"diferenças dimensionais ou elétricas exigem adaptação ou outro modelo."
            ),
        },
        {
            "pergunta": f"Quais dados do {sku} estão no datasheet e quais devem ser pedidos à engenharia?",
            "resposta": (
                f"No datasheet oficial constam os parâmetros com confiança 100% listados na "
                f"tabela de especificações desta página. Se vazão (m³/h), curva, peso ou desenho "
                f"de furação não aparecerem na ficha, solicite o PDF atualizado à Sell-Parts — "
                f"não utilize valores estimados."
            ),
        },
    ]
    if "EC" in sku.upper() or "ec" in (p.get("slug") or ""):
        faq.append({
            "pergunta": f"O {sku} (EC) dispensa inversor de frequência externo?",
            "resposta": (
                f"A linha EC Sell-Parts traz eletrônica embarcada para configuração conforme a "
                f"aplicação e, em geral, opera alimentada em rede AC sem variador externo "
                f"dedicado. Confirme no datasheet do {sku} a tensão, o tipo de controle e o "
                f"esquema de ligação antes de projetar o painel."
            ),
        })
    elif "BT" in sku.upper():
        faq.append({
            "pergunta": f"O {sku} pode operar em câmaras de baixa temperatura?",
            "resposta": (
                f"A versão BT do {sku} declara faixa térmica {p.get('temperatura', 'conforme datasheet')} "
                f"com graxa adequada a frio negativo. Valide sempre a temperatura mínima do "
                f"ambiente real contra a ficha técnica antes da instalação."
            ),
        })
    else:
        ip = p.get("protecao_mecanica") or "conforme datasheet"
        faq.append({
            "pergunta": f"O {sku} é adequado a ambientes com poeira ou umidade?",
            "resposta": (
                f"O grau de proteção mecânica declarado para o {sku} é {ip}. Isso indica o nível "
                f"de proteção do conjunto elétrico; a seleção final deve considerar limpeza do "
                f"local, respingos e a necessidade de grades/filtros no equipamento."
            ),
        })
    return [
        {"pergunta": sanitizar_texto(x["pergunta"]), "resposta": sanitizar_texto(x["resposta"])}
        for x in faq
    ]


def validar_anti_repeticao_copy(produto_data):
    """
    REGRA 10 — Bloqueia frases-template repetidas em benefícios/diferenciais
    e FAQ que só ecoa specs do hero.
    """
    erros = []
    resumo = (produto_data.get("resumo_tecnico") or "").lower()
    if "construção declarada no datasheet" in resumo or "construcao declarada no datasheet" in resumo:
        erros.append(
            "BLOQUEADO: resumo_tecnico usa lista 'Construção declarada no datasheet'. "
            "Escreva 2 parágrafos de produto (identidade do SKU + construção em prosa)."
        )
    benefs = produto_data.get("beneficios") or []
    finais = []
    for b in benefs:
        desc = (b.get("descricao") if isinstance(b, dict) else str(b) or "").strip().lower()
        for frase in FRASES_TEMPLATE_BLOQUEADAS:
            if frase in desc:
                erros.append(
                    f"BLOQUEADO: benefício usa frase-template repetida ('{frase[:50]}...'). "
                    "Cada benefício deve ter conclusão específica."
                )
        # últimos ~60 chars como "conclusão"
        if len(desc) >= 40:
            finais.append(desc[-60:])
    if len(finais) >= 2 and len(set(finais)) == 1:
        erros.append(
            "BLOQUEADO: os 4 benefícios terminam com a mesma frase. "
            "Reescreva a conclusão de cada card de forma única."
        )

    difs = [str(d).lower() for d in (produto_data.get("diferenciais") or [])]
    blob_dif = "\n".join(difs)
    count_val = blob_dif.count("configuração validada") + blob_dif.count("configuracao validada")
    if count_val > 1:
        erros.append(
            "BLOQUEADO: 'Configuração validada...' aparece em mais de 1 diferencial. "
            "Mantenha no máximo em 1 item."
        )
    for frase in FRASES_TEMPLATE_BLOQUEADAS:
        if "validada" in frase and frase in blob_dif and count_val > 1:
            continue

    # FAQ: perguntas que só pedem tensão/potência/IP (eco de specs)
    faq_eco = 0
    for faq in produto_data.get("faq") or []:
        p = (faq.get("pergunta") or "").lower()
        if any(
            x in p
            for x in (
                "principais parâmetros elétricos",
                "principais parametros eletricos",
                "grau de proteção mecânica e nível de ruído",
                "grau de protecao mecanica e nivel de ruido",
                "qual é a tensão e potência",
                "qual e a tensao e potencia",
            )
        ):
            faq_eco += 1
    if faq_eco >= 2:
        erros.append(
            "BLOQUEADO: FAQ só repete dados já presentes na tabela/hero. "
            "Use perguntas de substituição, validação dimensional ou uso EC/BT."
        )

    # Nova Regra: S1 / Regime contínuo no máximo 2 vezes
    textos_blob = "\n".join(str(v) for k, v in produto_data.items() if k != "seo" and k != "especificacoes").lower()
    # Adding specifically specs if they exist:
    specs = "\n".join(str(s) for s in produto_data.get("especificacoes", []))
    textos_blob += "\n" + specs.lower()
    
    s1_count = len(re.findall(r'\b(s1|regime cont[ií]nuo)\b', textos_blob))
    if s1_count > 2:
        erros.append(
            f"BLOQUEADO: A palavra 'S1' ou 'Regime contínuo' foi citada {s1_count} vezes. "
            "REGRA ESTRITA: O limite máximo é de 2 menções por página."
        )

    return len(erros) == 0, erros


def validar_vocabulario_tecnico(produto_data):
    """
    REGRA 9 — Bloqueia marketing inventado, aplicações fora da planilha
    e menção pública a concorrentes (incl. SEO keywords).
    """
    erros = []
    textos = list(_textos_do_produto(produto_data))
    seo = produto_data.get("seo") or {}
    for kw in seo.get("keywords") or []:
        textos.append(str(kw))
    if seo.get("meta_description"):
        textos.append(str(seo["meta_description"]))
    blob = "\n".join(textos).lower()

    for frase in FRASES_MARKETING_INVENTADAS:
        if frase.lower() in blob:
            erros.append(
                f"BLOQUEADO: frase de marketing não comprovada ('{frase}'). "
                "Use apenas termos do datasheet ou planilha de SEO."
            )

    for marca in CONCORRENTES_PROIBIDOS_PUBLICO:
        if marca.lower() in blob:
            erros.append(
                f"BLOQUEADO: concorrente/marca citada em campo público ('{marca}'). "
                "Cross-reference é interno — proibido em schema, SEO, FAQ e copy."
            )

    for app in produto_data.get("aplicacoes") or []:
        titulo = (app.get("titulo") if isinstance(app, dict) else str(app) or "")
        desc = (app.get("descricao", "") if isinstance(app, dict) else "").lower()
        titulo_l = titulo.lower()

        # Título com lista inventada: "A, B e C" / "A, B, C"
        if titulo.count(",") >= 1 and (" e " in titulo_l or titulo.count(",") >= 2):
            erros.append(
                f"BLOQUEADO: título de aplicação lista vários equipamentos "
                f"('{titulo[:70]}'). Um card = um equipamento da planilha."
            )

        for sufixo in SUFIXOS_APLICACAO_INVENTADOS:
            if sufixo.lower() in titulo_l:
                erros.append(
                    f"BLOQUEADO: título de aplicação com sufixo inventado ('{sufixo.strip()}'). "
                    f"Use só o nome do equipamento da planilha: '{titulo[:50]}'."
                )
                break

        for inv in DESCRICOES_APLICACAO_INVENTADAS:
            if inv in desc:
                erros.append(
                    "BLOQUEADO: descrição de aplicação genérica/inventada. "
                    "Copie a linha técnica de aplicacoes_excel da planilha."
                )
                break

    fonte_eq = produto_data.get("_fonte_equipamentos") or []
    fonte_app = produto_data.get("_fonte_aplicacoes_excel") or []
    if fonte_eq and fonte_app:
        def _norm_planilha(s):
            return sanitizar_texto(s or "").lower().rstrip(".!?").strip()

        apps = produto_data.get("aplicacoes") or []
        for i, app in enumerate(apps[:4]):
            if not isinstance(app, dict):
                continue
            titulo = _norm_planilha(app.get("titulo", ""))
            desc = _norm_planilha(app.get("descricao", ""))
            if i < len(fonte_eq) and titulo != _norm_planilha(fonte_eq[i]):
                erros.append(
                    f"BLOQUEADO: aplicação {i+1} título diverge da planilha "
                    f"(esperado equipamento cadastrado)."
                )
            if i < len(fonte_app) and desc != _norm_planilha(fonte_app[i]):
                erros.append(
                    f"BLOQUEADO: aplicação {i+1} descrição diverge da planilha "
                    f"(esperado texto de aplicacoes_excel)."
                )

    return len(erros) == 0, erros


def corrigir_separacao_mercado_aplicacoes(produto_data):
    """Reconstrói mercado a partir de setores; não altera quantidade de aplicações."""
    sku = produto_data.get("sku", "")
    slug = produto_data.get("slug", "")
    eh_bt = "BT" in sku.upper() or "bt" in slug.lower() or "etbt" in slug.lower()

    setores = extrair_setores_do_mercado(produto_data.get("mercado", ""))
    if setores:
        produto_data["mercado"] = gerar_texto_mercado(sku, setores, eh_bt=eh_bt)
    return produto_data


def validar_estrutura_obrigatoria(produto_data):
    """Quantidades exigidas pela Regra de Ferro (AGENTS.md)."""
    erros = []
    resumo = produto_data.get("resumo_tecnico", "")
    paras = [p for p in resumo.split("\n\n") if p.strip()]
    if len(paras) != 2:
        erros.append(f"BLOQUEADO: resumo_tecnico com {len(paras)} parágrafos (esperado: 2).")
    else:
        for idx, p in enumerate(resumo.split("\n\n"), 1):
            if p.startswith(" ") or p.startswith("\t"):
                erros.append(f"BLOQUEADO: parágrafo {idx} de 'resumo_tecnico' possui recuo/espaços no início da linha.")

    for campo, qtd in (
        ("hero_checklist", 3),
        ("beneficios", 4),
        ("diferenciais", 4),
    ):
        n = len(produto_data.get(campo) or [])
        if n != qtd:
            erros.append(f"BLOQUEADO: {campo} com {n} itens (esperado: {qtd}).")

    # Aplicações (suporta formato novo em 2 níveis ou antigo de 4 itens)
    app_cat = produto_data.get("aplicacoes_categoria")
    app_eq = produto_data.get("aplicacoes_equipamento")
    apps_antigo = produto_data.get("aplicacoes")
    if app_cat and app_eq:
        n_cat = len(app_cat.get("cards") if isinstance(app_cat, dict) else app_cat)
        n_eq = len(app_eq.get("cards") if isinstance(app_eq, dict) else app_eq)
        if n_cat < 1:
            erros.append(f"BLOQUEADO: aplicacoes_categoria com {n_cat} cards (esperado mínimo: 1).")
        if n_eq < 1:
            erros.append(f"BLOQUEADO: aplicacoes_equipamento com {n_eq} cards (esperado mínimo: 1).")
    elif apps_antigo:
        if len(apps_antigo) != 4:
            erros.append(f"BLOQUEADO: aplicacoes com {len(apps_antigo)} itens (esperado: 4).")
    else:
        erros.append("BLOQUEADO: aplicacoes vazio (esperado aplicacoes_categoria e aplicacoes_equipamento ou aplicacoes).")

    # Mercado (suporta lista ou texto/dict)
    merc = produto_data.get("mercados") or produto_data.get("mercado") or produto_data.get("mercados_list")
    if not merc:
        erros.append("BLOQUEADO: mercado vazio.")

    # FAQ (suporta 3 ou 4 itens)
    faq_n = len(produto_data.get("faq") or [])
    if faq_n not in (3, 4):
        erros.append(f"BLOQUEADO: faq com {faq_n} itens (esperado: 3 ou 4).")

    specs = produto_data.get("especificacoes") or []
    if specs and not any(s.get("confianca") == "100%" for s in specs):
        erros.append("BLOQUEADO: nenhuma especificação com confiança 100%.")
    return len(erros) == 0, erros


def validar_cobertura_skus(skus_origem, skus_gerados):
    """Compara sets de SKUs da lista de origem vs páginas geradas."""
    faltando = set(skus_origem) - set(skus_gerados)
    if faltando:
        return False, [f"BLOQUEADO: SKUs sem página gerada: {sorted(faltando)}"]
    return True, []


def normalizar_mancais(valor):
    """Remove 'Com ' inicial para evitar 'Equipado com com ...'."""
    v = (valor or "").strip()
    return re.sub(r"^(com)\s+", "", v, flags=re.IGNORECASE)


# ========================================================================
# VALIDAÇÃO COMPLETA DO PRODUTO
# ========================================================================
def validar_produto_completo(produto_data, sanitizar=True):
    """
    Executa TODAS as validações no produto.
    Por padrão sanitiza textos (acentos/pontuação) e corrige mercado×aplicações.
    Retorna (is_valid, lista_de_erros).
    """
    if sanitizar:
        sanitizar_produto(produto_data)
        corrigir_separacao_mercado_aplicacoes(produto_data)
        sanitizar_produto(produto_data)

    erros = []

    # R1: Validar cada spec
    for spec in produto_data.get("especificacoes", []):
        ok, msg = validar_confianca(spec)
        if not ok:
            erros.append(msg)

    # R2: Validar termos proibidos em todos os textos
    for texto in _textos_do_produto(produto_data):
        ok, termos = validar_termos_proibidos(texto)
        if not ok:
            erros.append(f"BLOQUEADO: Termos proibidos encontrados: {termos}")

    # R3: Alerta trifásico
    ok, msg = validar_alerta_trifasico(produto_data)
    if not ok:
        erros.append(msg)

    # R4: Aviso de specs pendentes
    ok, msg = validar_aviso_pendentes(produto_data)
    if not ok:
        erros.append(msg)

    # R5: Campos obrigatórios
    obrigatorios = ["nome", "sku", "especificacoes", "faq"]
    for campo in obrigatorios:
        if not produto_data.get(campo):
            erros.append(f"BLOQUEADO: Campo obrigatório '{campo}' está vazio.")

    # R6: Estrutura obrigatória (Regra de Ferro)
    ok_est, msgs_est = validar_estrutura_obrigatoria(produto_data)
    if not ok_est:
        erros.extend(msgs_est)

    # R7: Densidade de conteúdo B2B
    ok_densidade, msgs_densidade = validar_densidade_conteudo(produto_data)
    if not ok_densidade:
        erros.extend(msgs_densidade)

    # Pós-geração (bloqueia publish)
    for validador in (
        validar_palavras_duplicadas,
        validar_typos_basicos,
        validar_pontuacao_basica,
        validar_imagens_unicas,
        validar_separacao_aplicacoes_mercado,
        validar_vocabulario_tecnico,
        validar_anti_repeticao_copy,
        validar_meta_description,
    ):
        ok_v, msgs_v = validador(produto_data)
        if not ok_v:
            erros.extend(msgs_v)

    return len(erros) == 0, erros


def validar_meta_description(produto_data):
    """
    REGRA DE SEO: Meta description deve ter 150-160 caracteres,
    terminar em ponto (.) e conter pelo menos 1 dado técnico numérico com unidade.
    """
    erros = []
    meta = (produto_data.get("meta_description") or produto_data.get("seo", {}).get("meta_description") or "").strip()
    if not meta:
        return False, ["BLOQUEADO: meta_description está vazia."]
    if len(meta) < 140 or len(meta) > 165:
        erros.append(
            f"BLOQUEADO: meta_description tem {len(meta)} caracteres (alvo: 150-160 caracteres)."
        )
    if not meta.endswith("."):
        erros.append("BLOQUEADO: meta_description deve ser uma frase completa terminando com ponto final (.).")

    padrao_num_tecnico = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:mm|cm|m|v|w|kw|hz|rpm|dba|a|kg|°c|c|ip\d{2})\b", re.IGNORECASE)
    if not padrao_num_tecnico.search(meta):
        erros.append("BLOQUEADO: meta_description deve conter pelo menos 1 dado técnico numérico com unidade (ex: 220 V, 69 dBA, IP54, 250 mm).")

    return len(erros) == 0, erros


# ========================================================================
# REGRA 7: DENSIDADE E RIQUEZA DE CONTEÚDO B2B
# ========================================================================
def validar_densidade_conteudo(produto_data):
    """
    Garante que os blocos de texto gerados sejam ricos e detalhados.
    - FAQ: Respostas com no mínimo 120 caracteres (2-3 sentenças técnicas explicativas).
    - Benefícios: Descrições dos cards com no mínimo 80 caracteres.
    - Diferenciais: Cada item deve ter no mínimo 50 caracteres de explicação.
    """
    erros = []

    # Validar FAQ
    for idx, faq in enumerate(produto_data.get("faq", [])):
        res = faq.get("resposta", "")
        if len(res) < 120:
            erros.append(
                f"REPROVADO POR DENSIDADE: FAQ {idx+1} ('{faq.get('pergunta')}') "
                f"tem resposta muito curta ({len(res)} caracteres). "
                f"Escreva uma resposta técnica detalhada explicando o 'como' ou 'por que'."
            )

    # Validar Benefícios
    for idx, ben in enumerate(produto_data.get("beneficios", [])):
        desc = ben.get("descricao", "")
        if len(desc) < 80:
            erros.append(
                f"REPROVADO POR DENSIDADE: Benefício {idx+1} ('{ben.get('titulo')}') "
                f"tem descrição muito curta ({len(desc)} caracteres). "
                f"Explique o valor real desse benefício para a operação industrial do cliente."
            )

    # Validar Diferenciais
    for idx, dif in enumerate(produto_data.get("diferenciais", [])):
        if len(dif) < 50:
            erros.append(
                f"REPROVADO POR DENSIDADE: Diferencial {idx+1} ('{dif[:20]}...') "
                f"é muito curto ({len(dif)} caracteres). "
                f"Seja mais específico e técnico sobre o diferencial oferecido."
            )

    return len(erros) == 0, erros



# ========================================================================
# REGRA 6: Geração obrigatória do arquivo acf-campos-prontos.md
# ========================================================================
# Para CADA produto gerado pelo script, é OBRIGATÓRIO produzir o arquivo
# acf-campos-prontos.md dentro da pasta do produto, contendo os 8 campos
# ACF formatados e prontos para colar no WordPress.
#
# Estrutura obrigatória do arquivo:
#
#   produtos/{slug}/
#   ├── landing-page-master.md      ← Pesquisa, SEO, mapeamento competitivo
#   ├── pesquisa-concorrentes.md    ← Análise factual de concorrentes
#   └── acf-campos-prontos.md       ← Campos ACF prontos para colar no WP
#
# Os 7 campos obrigatórios no acf-campos-prontos.md:
#
#   CAMPO 1 — sp_especificacoes     → HTML com classes .sp- (tabela + alerta)
#   CAMPO 2 — sp_aplicacoes         → HTML com classes .sp- (grid)
#   CAMPO 3 — sp_beneficios         → HTML com classes .sp- (cards)
#   CAMPO 4 — sp_diferenciais       → HTML com classes .sp- (lista)
#   CAMPO 5 — sp_downloads          → HTML com classes .sp- (placeholder)
#   CAMPO 6 — sp_faq                → HTML com classes .sp- (accordion)
#   CAMPO 7 — sp_alerta_tecnico     → Texto puro (sem HTML)
#
# Regras de formatação:
#   - Campos WYSIWYG (1-6): HTML dentro de bloco ```html``` para copiar
#   - Campo texto puro (7): Dentro de bloco ``` ``` simples
#   - Cada campo deve ter instrução clara de onde colar no WP
#   - Tabela de specs (campo 1): SOMENTE dados com confiança 100%
#   - Se há dados pendentes (0%): incluir div .sp-alerta-tecnico dentro do campo 1
#   - FAQ (campo 6): mínimo 3 perguntas por produto
#   - Alerta (campo 7): obrigatório para trifásicos e produtos com specs pendentes

CAMPOS_ACF_OBRIGATORIOS = [
    "sp_especificacoes",
    "sp_aplicacoes",
    "sp_beneficios",
    "sp_diferenciais",
    "sp_downloads",
    "sp_faq",
    "sp_alerta_tecnico",
]


TEMPLATE_HEADER_ACF = """# Campos ACF Prontos para Colar no WordPress
# Produto: {nome}
# Status: VALIDADO (Zero Inferência)
# Data: {data}

> **Instrução:** Abra o produto no WooCommerce, role até os campos ACF
> e cole o conteúdo de cada campo abaixo no respectivo accordion.
> Os campos WYSIWYG devem ser colados na aba "Texto" (não "Visual").

---
"""

