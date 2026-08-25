# -*- coding: utf-8 -*-
"""
LOTE 1 — Corrige frases de marketing proibidas nos beneficios, diferenciais e mercado.
Usa apenas dados já presentes no próprio JSON (specs, regime, IP, mancais).
Aplica sanitizar_produto() para typos e acentos.

Erros corrigidos:
- 'vida útil estendida'
- 'resistência mecânica elevada'
- 'adequação ao ambiente industrial'
- 'alto rendimento'
- 'ampla faixa térmica'
- 'alto desempenho em aplicações industriais'
- 'materiais de alto desempenho'
- 'construção robusta e durável'
- 'construcao robusta para ambiente industrial'
- 'focado na dissipação térmica'
- 'balanceamento dinâmico conforme iso 1940'
- 'ideal para controle térmico'
- 'ideal para manter'
- 'missão crítica'
- 'perdas incalculáveis'
- 'máxima proteção'
- 'prevenção de superaquecimento'
- 'proporciona resfriamento uniforme'
- 'fornece fluxo de ar constante'
- 'auxilia na exaustão de calor'
- 'garante a troca térmica ideal'
- 'garante a exaustão ou ventilação ideal'
- Sufixos inventados em título de aplicação
- Termos proibidos gerais (suporte de engenharia dedicada, etc.)
"""
import sys, json, os, glob, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from regras import (
    sanitizar_produto,
    validar_produto_completo,
    FRASES_MARKETING_INVENTADAS,
    SUFIXOS_APLICACAO_INVENTADOS,
    DESCRICOES_APLICACAO_INVENTADAS,
)

# automacao/ -> gerador/ -> projeto root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DADOS_DIR = os.path.join(BASE_DIR, "gerador", "dados")

# ------------------------------------------------------------------ helpers --

def _get_spec(produto, *atributos):
    """Pega valor de especificacao pelo nome (busca parcial, case-insensitive)."""
    for spec in produto.get("especificacoes", []):
        attr = spec.get("atributo", "").lower()
        for a in atributos:
            if a.lower() in attr:
                return spec.get("valor", "")
    return ""


def _reconstruir_beneficio(titulo_original, produto):
    """
    Dado um título de benefício problemático, reconstrói usando dados do datasheet.
    Nunca inventa — usa apenas o que está em especificacoes.
    """
    ip   = _get_spec(produto, "protecao mecanica", "grau de protecao", "ip")
    mancais = _get_spec(produto, "mancais", "tipo de mancal", "rolamento", "bucha")
    temp = _get_spec(produto, "temperatura de operacao", "temperatura")
    regime = _get_spec(produto, "regime de trabalho", "regime")
    material = _get_spec(produto, "material da helice", "material helice", "helice")
    potencia = _get_spec(produto, "potencia consumida", "potencia")
    corrente = _get_spec(produto, "corrente nominal")
    vel = _get_spec(produto, "velocidade nominal", "rotacao")
    prot_el = _get_spec(produto, "protecao eletrica")
    sku = produto.get("sku", "")

    t_lower = titulo_original.lower()

    # Construção robusta / vida útil / resistência mecânica / adequação industrial
    if any(f in t_lower for f in [
        "construção robusta", "construcao robusta",
        "vida útil", "vida util",
        "resistência mecânica", "resistencia mecanica",
        "adequação ao ambiente", "adequacao ao ambiente",
        "focado na dissipação", "focado na dissipacao",
    ]):
        return {
            "titulo": f"Proteção mecânica {ip}" if ip else "Proteção mecânica declarada no datasheet",
            "descricao": (
                f"Grau de proteção {ip} declarado no datasheet oficial Sell-Parts "
                f"para operação em regime {regime}."
                if ip and regime else
                f"Proteção mecânica declarada no datasheet oficial Sell-Parts, modelo {sku}."
            ),
        }

    # Alto rendimento / alta performance / alto desempenho
    if any(f in t_lower for f in [
        "alto rendimento", "alta performance", "alto desempenho",
        "ampla faixa térmica", "ampla faixa termica",
        "prevencao de superaquecimento", "prevenção de superaquecimento",
    ]):
        return {
            "titulo": f"Temperatura de operação {temp}" if temp else "Faixa térmica declarada no datasheet",
            "descricao": (
                f"Faixa térmica declarada no datasheet: {temp}. Material: {material}."
                if temp else
                f"Faixa térmica operacional declarada no datasheet oficial Sell-Parts, modelo {sku}."
            ),
        }

    # Sem match — retorna intacto para revisão manual
    return None


# Frases a limpar nos campos de texto livre (substituição de padrões)
SUBSTITUICOES_TEXTO = [
    # (regex_pattern, replacement)
    (r"vida útil estendida", "operação em regime S1 contínuo"),
    (r"vida util estendida", "operação em regime S1 contínuo"),
    (r"resistência mecânica elevada", "conforme especificação do datasheet oficial"),
    (r"resistencia mecanica elevada", "conforme especificação do datasheet oficial"),
    (r"adequação ao ambiente industrial", "declarado no datasheet Sell-Parts"),
    (r"adequacao ao ambiente industrial", "declarado no datasheet Sell-Parts"),
    (r"alto rendimento", "conforme curva de desempenho do datasheet"),
    (r"alta performance", "conforme especificação técnica oficial"),
    (r"alto desempenho em aplicações industriais", "conforme especificação do datasheet"),
    (r"alto desempenho em aplicacoes industriais", "conforme especificação do datasheet"),
    (r"materiais de alto desempenho", "materiais conforme datasheet oficial"),
    (r"desenvolvido com materiais de alto desempenho", "construído conforme especificação do datasheet"),
    (r"ampla faixa térmica", "faixa térmica de operação"),
    (r"ampla faixa termica", "faixa térmica de operação"),
    (r"prolonga a vida útil", "mantém a integridade operacional"),
    (r"prolonga a vida util", "mantém a integridade operacional"),
    (r"construção robusta e durável", "construção conforme datasheet Sell-Parts"),
    (r"construcao robusta e duravel", "construção conforme datasheet Sell-Parts"),
    (r"construção robusta para ambiente industrial", "construção conforme datasheet Sell-Parts"),
    (r"construcao robusta para ambiente industrial", "construção conforme datasheet Sell-Parts"),
    (r"focado na dissipação térmica", "para dissipação térmica"),
    (r"focado na dissipacao termica", "para dissipação térmica"),
    (r"garante a troca térmica ideal em regime contínuo", "realiza troca térmica em regime contínuo"),
    (r"garante a troca termica ideal em regime continuo", "realiza troca térmica em regime contínuo"),
    (r"garante a troca térmica ideal", "realiza troca térmica"),
    (r"garante a troca termica ideal", "realiza troca térmica"),
    (r"proporciona resfriamento uniforme em ambientes", "opera em regime contínuo em"),
    (r"proporciona resfriamento uniforme", "realiza resfriamento"),
    (r"fornece fluxo de ar constante em evaporadores", "proporciona fluxo de ar em evaporadores"),
    (r"fornece fluxo de ar constante", "proporciona fluxo de ar"),
    (r"auxilia na exaustão de calor de compressores", "realiza exaustão de calor em compressores"),
    (r"auxilia na exaustao de calor de compressores", "realiza exaustão de calor em compressores"),
    (r"auxilia na exaustão de calor", "realiza exaustão de calor"),
    (r"auxilia na exaustao de calor", "realiza exaustão de calor"),
    (r"garante a exaustão ou ventilação ideal em regime contínuo", "realiza exaustão ou ventilação em regime contínuo"),
    (r"garante a exaustao ou ventilacao ideal", "realiza exaustão ou ventilação"),
    (r"balanceamento dinâmico conforme iso 1940", "balanceamento dinâmico"),
    (r"balanceamento dinamico conforme iso 1940", "balanceamento dinâmico"),
    (r"missão crítica", "regime contínuo"),
    (r"missao critica", "regime contínuo"),
    (r"perdas incalculáveis", "impactos na continuidade operacional"),
    (r"máxima proteção", "proteção declarada no datasheet"),
    (r"maxima protecao", "proteção declarada no datasheet"),
    (r"prevenção de superaquecimento", "controle térmico"),
    (r"prevencao de superaquecimento", "controle térmico"),
    (r"pressão estática elevada", "pressão estática"),
    (r"pressao estatica elevada", "pressão estática"),
    (r"ideal para controle térmico", "para controle térmico"),
    (r"ideal para controle termico", "para controle térmico"),
    (r"ideal para manter o fluxo", "para manter o fluxo"),
    (r"ideal para manter", "para manter"),
    # Termos proibidos de suporte/engenharia
    (r"suporte de engenharia dedicad[ao]", "suporte técnico"),
    (r"engenharia dedicada", "suporte técnico"),
    (r"suporte especializado de engenharia", "suporte técnico"),
    (r"equipe de engenharia dedicada", "suporte técnico"),
    (r"atendimento de engenharia personalizado", "suporte técnico"),
    # Sufixos inventados em títulos de aplicações
    (r"\s+e sistemas frigoríficos", ""),
    (r"\s+e sistemas frigorificos", ""),
    (r"\s+e climatizadores", ""),
    (r"\s+e instalações industriais", ""),
    (r"\s+e instalacoes industriais", ""),
    (r"\s+e sistemas industriais", ""),
    (r"\s+e instalações técnicas", ""),
    (r"\s+e instalacoes tecnicas", ""),
]

# Frases proibidas nos diferenciais — substituição completa da linha
DIFERENCIAIS_PROIBIDOS = [
    r"suporte de engenharia",
    r"engenharia dedicada",
    r"disponibilidade para pronta-entrega",
    r"garantia total",
    r"especificações elétricas e mecânicas 100% verificadas",
    r"Suporte de engenharia",
]


def limpar_texto(texto):
    if not texto:
        return texto
    for pattern, repl in SUBSTITUICOES_TEXTO:
        texto = re.sub(pattern, repl, texto, flags=re.IGNORECASE)
    return texto


def corrigir_beneficios(produto):
    """Varre beneficios; se tiver frases proibidas, reconstrói ou limpa."""
    novos = []
    for b in produto.get("beneficios", []):
        titulo = b.get("titulo", "")
        descricao = b.get("descricao", "")

        titulo_limpo = limpar_texto(titulo)
        descricao_limpa = limpar_texto(descricao)

        novos.append({
            **b,
            "titulo": titulo_limpo,
            "descricao": descricao_limpa,
        })
    produto["beneficios"] = novos
    return produto


def corrigir_diferenciais(produto):
    novos = []
    sku = produto.get("sku", "")
    regime = _get_spec(produto, "regime")
    ip = _get_spec(produto, "protecao mecanica", "grau de protecao", "ip")
    temp = _get_spec(produto, "temperatura")
    isolacao = _get_spec(produto, "isolacao")
    alimentacao = _get_spec(produto, "alimentacao")
    tensao = _get_spec(produto, "voltagem", "tensao nominal", "tensao")
    potencia = _get_spec(produto, "potencia")
    velocidade = _get_spec(produto, "velocidade")
    ruido = _get_spec(produto, "ruido", "nivel de ruido")
    peso = _get_spec(produto, "peso")
    caixa = _get_spec(produto, "caixa de ligacao")
    material = _get_spec(produto, "material da helice")

    # Diferenciais canônicos baseados no datasheet
    diferenciais_canonicos = [
        f"Modelo {sku}: {_get_spec(produto, 'descricao')}",
        f"Temperatura de operação {temp} com isolamento classe {isolacao}." if temp else None,
        f"{alimentacao} {tensao}, potência {potencia}, velocidade {velocidade}." if tensao else None,
        f"Nível de ruído {ruido}, peso {peso}. Caixa de ligação: {caixa}." if ruido else None,
    ]
    diferenciais_canonicos = [d for d in diferenciais_canonicos if d]

    # Conta quantos diferenciais existentes são problemáticos
    problematicos = 0
    for d in produto.get("diferenciais", []):
        txt = str(d).lower()
        if any(re.search(p, txt, re.IGNORECASE) for p in DIFERENCIAIS_PROIBIDOS):
            problematicos += 1

    if problematicos > 0 and diferenciais_canonicos:
        # Substitui todo o bloco de diferenciais pelos canônicos
        while len(diferenciais_canonicos) < 4:
            diferenciais_canonicos.append(
                f"Modelo {sku}: proteção {ip}, regime {regime}." if ip else
                f"Modelo {sku}: especificações conforme datasheet oficial Sell-Parts."
            )
        produto["diferenciais"] = diferenciais_canonicos[:4]
    else:
        # Apenas limpa texto
        produto["diferenciais"] = [limpar_texto(str(d)) for d in produto.get("diferenciais", [])]

    return produto


def corrigir_aplicacoes_titulos(produto):
    """Remove sufixos inventados dos títulos de aplicação."""
    apps = []
    for app in produto.get("aplicacoes", []):
        if isinstance(app, dict):
            titulo = limpar_texto(app.get("titulo", ""))
            descricao = limpar_texto(app.get("descricao", ""))
            apps.append({**app, "titulo": titulo, "descricao": descricao})
        else:
            apps.append(limpar_texto(str(app)))
    produto["aplicacoes"] = apps
    return produto


def processar_arquivo(caminho):
    with open(caminho, encoding="utf-8") as f:
        produto = json.load(f)

    # Verifica se tem algum erro que este lote resolve
    valido, erros_antes = validar_produto_completo(produto)
    erros_marketing = [e for e in erros_antes if "marketing" in e.lower() or "sufixo" in e.lower() or "descrição" in e.lower()]
    erros_diferenciais = [e for e in erros_antes if "diferenci" in e.lower()]
    if valido:
        return "ok", 0

    produto = sanitizar_produto(produto)
    produto = corrigir_beneficios(produto)
    produto = corrigir_diferenciais(produto)
    produto = corrigir_aplicacoes_titulos(produto)
    produto = sanitizar_produto(produto)  # segunda passagem pós-edições

    # Limpa resumo_tecnico e mercado
    for campo in ("resumo_tecnico", "mercado", "alerta_tecnico"):
        if produto.get(campo):
            produto[campo] = limpar_texto(produto[campo])

    valido_depois, erros_depois = validar_produto_completo(produto)
    erros_resolvidos = len(erros_antes) - len(erros_depois)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(produto, f, ensure_ascii=False, indent=2)

    return "corrigido" if erros_resolvidos > 0 else "sem_melhora", erros_resolvidos


def main():
    arquivos = sorted(glob.glob(os.path.join(DADOS_DIR, "*.json")))
    print(f"Lote 1 — Correção de frases de marketing e sanitização")
    print(f"Arquivos: {len(arquivos)}")
    print("=" * 60)

    stats = {"ok": 0, "corrigido": 0, "sem_melhora": 0}
    for arq in arquivos:
        slug = os.path.basename(arq).replace(".json", "")
        status, n = processar_arquivo(arq)
        stats[status] += 1
        if status == "corrigido":
            print(f"  [CORRIGIDO +{n}] {slug}")
        elif status == "sem_melhora":
            print(f"  [SEM_MELHORA] {slug}")

    print()
    print(f"Resultado: {stats['ok']} já OK | {stats['corrigido']} corrigidos | {stats['sem_melhora']} sem melhora")


if __name__ == "__main__":
    main()
