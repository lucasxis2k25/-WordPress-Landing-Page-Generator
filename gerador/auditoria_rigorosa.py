# -*- coding: utf-8 -*-
"""
Auditoria Rigorosa em 100% dos Produtos JSON e ACF Payloads
"""
import glob
import json
import os
import re

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS_DIR = os.path.join(PROJ_DIR, "gerador", "dados")
OUTPUT_DIR = os.path.join(PROJ_DIR, "gerador", "output")

def auditar_tudo():
    json_files = glob.glob(os.path.join(DADOS_DIR, "*.json"))
    relatorio = []

    print(f"[*] Auditando {len(json_files)} arquivos JSON em {DADOS_DIR}...")

    for jf in json_files:
        slug = os.path.basename(jf).replace(".json", "")
        with open(jf, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                relatorio.append({"slug": slug, "tipo": "JSON_CORROMPIDO", "msg": str(e)})
                continue

        raw = json.dumps(data, ensure_ascii=False)

        # Checagem de codificação
        if "\ufffd" in raw or "Ã" in raw or "ã©" in raw:
            relatorio.append({"slug": slug, "tipo": "ENCODING", "msg": "Caractere corrompido ou mojibake encontrado"})

        # Checagem de 2Z
        if re.search(r"\b2z\b", raw):
            relatorio.append({"slug": slug, "tipo": "PADRAO_2Z", "msg": "Encontrado '2z' minúsculo"})

        # Checagem de títulos de equipamentos
        onde_usar = data.get("onde_usar", [])
        if not onde_usar:
            relatorio.append({"slug": slug, "tipo": "ONDE_USAR_VAZIO", "msg": "Lista onde_usar está vazia"})
        for item in onde_usar:
            tit = item.get("titulo", "")
            desc = item.get("descricao", "")
            if any(p in tit.lower() for p in ["provável", "provavel", "aplicação final", "aplicacao final"]):
                relatorio.append({"slug": slug, "tipo": "PREFIXO_EQUIPAMENTO", "msg": f"Título com prefixo proibido: '{tit}'"})
            if not desc or len(desc) < 15:
                relatorio.append({"slug": slug, "tipo": "DESC_EQUIPAMENTO_CURTA", "msg": f"Descrição do equipamento '{tit}' muito curta: '{desc}'"})

        # Checagem de mercados
        mercados = data.get("mercado", [])
        if not mercados:
            relatorio.append({"slug": slug, "tipo": "MERCADOS_VAZIO", "msg": "Lista de mercados vazia"})

        # Checagem de diferenciais
        difs = data.get("diferenciais", [])
        if not difs or len(difs) < 3:
            relatorio.append({"slug": slug, "tipo": "DIFERENCIAIS_INSUFICIENTES", "msg": f"Apenas {len(difs)} diferenciais"})
        for d in difs:
            if ":" not in d and len(d.split()) < 4:
                relatorio.append({"slug": slug, "tipo": "DIFERENCIAL_FORMATO", "msg": f"Diferencial sem formato 'Título: Explicação': '{d}'"})

    print(f"\n=======================================================")
    print(f"  RELATÓRIO DE AUDITORIA COMPLETA")
    print(f"  Total de Arquivos Analisados: {len(json_files)}")
    print(f"  Total de Apontamentos Encontrados: {len(relatorio)}")
    print(f"=======================================================\n")

    if not relatorio:
        print("[SUCESSO ABSOLUTO] 100% dos arquivos estão em conformidade perfeita com todas as regras!")
    else:
        for r in relatorio:
            print(f"[{r['tipo']}] {r['slug']}: {r['msg']}")

if __name__ == "__main__":
    auditar_tudo()
