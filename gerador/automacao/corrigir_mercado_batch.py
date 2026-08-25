# -*- coding: utf-8 -*-
"""
LOTE 2 — Corrige o campo `mercado`:
- Remove frases de equipamento/uso técnico
- Aplica corrigir_separacao_mercado_aplicacoes() do regras.py
- Reconstrói o mercado com setores extraídos do próprio texto
- Remove frase-gatilho 'operam em regime contínuo' que aparece no lugar errado
"""
import sys, json, os, glob, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from regras import (
    sanitizar_produto,
    validar_produto_completo,
    corrigir_separacao_mercado_aplicacoes,
    gerar_texto_mercado,
    extrair_setores_do_mercado,
    PROIBIDO_EM_MERCADO,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DADOS_DIR = os.path.join(BASE_DIR, "gerador", "dados")

# Setores padrão por família de produto (fallback quando não consegue extrair do texto)
SETORES_FAMILIA = {
    "exaustor": [
        "refrigeração comercial e industrial",
        "câmaras frigoríficas e túneis",
        "manutenção industrial e reposição",
        "HVAC e climatização",
        "serviços de refrigeração",
    ],
    "soprador": [
        "armazenagem de grãos e cereais",
        "processos industriais de secagem",
        "manutenção industrial e reposição",
        "HVAC e climatização",
        "serviços técnicos de ventilação",
    ],
    "centrifugo": [
        "climatização e ar-condicionado central",
        "refrigeração comercial e HVAC",
        "manutenção industrial e reposição",
        "processamento e indústria de alimentos",
        "serviços técnicos de ventilação",
    ],
    "radial": [
        "secagem industrial e processos térmicos",
        "indústria de alimentos e cerâmicas",
        "manutenção industrial e reposição",
        "HVAC e climatização",
        "serviços técnicos industriais",
    ],
    "in-line": [
        "HVAC e climatização residencial e comercial",
        "ventilação de ambientes e dutos",
        "manutenção e reposição de ventilação",
        "construção civil e projetos de ar",
        "serviços técnicos de ventilação",
    ],
    "gabinete": [
        "automação industrial e painéis elétricos",
        "telecomunicações e data centers",
        "manutenção e reposição de painéis",
        "OEMs de equipamentos elétricos",
        "serviços técnicos industriais",
    ],
    "microventilador": [
        "OEMs de automação e painéis elétricos",
        "telecomunicações e TI",
        "manutenção industrial e reposição técnica",
        "fabricantes de inversores e nobreaks",
        "serviços técnicos de eletrônica industrial",
    ],
    "default": [
        "refrigeração comercial e industrial",
        "manutenção industrial e reposição",
        "HVAC e climatização",
        "OEMs e integradores industriais",
        "serviços de refrigeração",
    ],
}


def detectar_familia(slug):
    s = slug.lower()
    if "micro" in s or s.startswith("a1") or s.startswith("a2") or s.startswith("d1"):
        return "microventilador"
    if "gabinete" in s or "ffgb" in s or "fbgb" in s:
        return "gabinete"
    if "in-line" in s or "fb-100" in s or "fb-150" in s or "fb-200" in s or "fb-250" in s or "fb-315" in s:
        return "in-line"
    if "radial" in s or "fb-2-" in s or "fb-4-" in s or "rb2c" in s or "rb4c" in s or "fb1d" in s:
        return "radial"
    if "centrifugo" in s or "centrifugo" in s or "ff-2-" in s or "ff-4-" in s or "rf-" in s:
        return "centrifugo"
    if "soprador" in s or "-vm" in s or "-vt" in s or "-vmp" in s or "-vtp" in s or "fs3-" in s and "v-" in s:
        return "soprador"
    if "exaustor" in s or "-em" in s or "-et" in s or "-ecp" in s:
        return "exaustor"
    return "default"


def tem_erro_mercado(erros):
    return any("mercado" in e.lower() for e in erros)


def processar_arquivo(caminho):
    with open(caminho, encoding="utf-8") as f:
        produto = json.load(f)

    valido, erros_antes = validar_produto_completo(produto)
    if valido:
        return "ok", 0

    if not tem_erro_mercado(erros_antes):
        return "skip", 0

    slug = produto.get("slug", os.path.basename(caminho).replace(".json", ""))
    sku = produto.get("sku", "")
    eh_bt = "BT" in sku.upper() or "bt" in slug.lower() or "etbt" in slug or "vmbt" in slug or "vtbt" in slug

    # Tenta extrair setores já declarados no mercado
    setores = extrair_setores_do_mercado(produto.get("mercado", ""))

    # Se não conseguiu extrair, usa fallback da família
    if not setores or len(setores) < 3:
        familia = detectar_familia(slug)
        setores = SETORES_FAMILIA.get(familia, SETORES_FAMILIA["default"])

    # Reconstrói o mercado
    produto["mercado"] = gerar_texto_mercado(sku or slug, setores, eh_bt=eh_bt)
    produto = sanitizar_produto(produto)

    valido_depois, erros_depois = validar_produto_completo(produto)
    erros_resolvidos = len(erros_antes) - len(erros_depois)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(produto, f, ensure_ascii=False, indent=2)

    return "corrigido" if erros_resolvidos > 0 else "sem_melhora", erros_resolvidos


def main():
    arquivos = sorted(glob.glob(os.path.join(DADOS_DIR, "*.json")))
    print(f"Lote 2 — Correção do campo mercado")
    print(f"Arquivos: {len(arquivos)}")
    print("=" * 60)

    stats = {"ok": 0, "corrigido": 0, "sem_melhora": 0, "skip": 0}
    for arq in arquivos:
        slug = os.path.basename(arq).replace(".json", "")
        status, n = processar_arquivo(arq)
        stats[status] += 1
        if status == "corrigido":
            print(f"  [CORRIGIDO +{n}] {slug}")
        elif status == "sem_melhora":
            print(f"  [SEM_MELHORA] {slug}")

    print()
    print(f"Resultado: {stats['ok']} já OK | {stats['skip']} sem erro de mercado | {stats['corrigido']} corrigidos | {stats['sem_melhora']} sem melhora")


if __name__ == "__main__":
    main()
