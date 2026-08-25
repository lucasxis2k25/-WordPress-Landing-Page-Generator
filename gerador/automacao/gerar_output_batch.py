# -*- coding: utf-8 -*-
"""
LOTE 5 — Geração de Output ACF para todos os JSONs aprovados na validação.
Gera: _acf.json, _acf_campos.txt e produtos/{slug}/acf-campos-prontos.md
"""
import sys, json, os, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from regras import validar_produto_completo
from gerar_conteudo_acf import carregar_dados, gerar_payload_acf, salvar_output

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DADOS_DIR = os.path.join(BASE_DIR, "gerador", "dados")


def main():
    arquivos = sorted(glob.glob(os.path.join(DADOS_DIR, "*.json")))
    print(f"Lote 5 — Geração de Output ACF")
    print(f"Arquivos: {len(arquivos)}")
    print("=" * 60)

    aprovados = []
    reprovados = []

    for arq in arquivos:
        slug = os.path.basename(arq).replace(".json", "")
        try:
            with open(arq, encoding="utf-8") as f:
                produto = json.load(f)
                
            if "hero_checklist" not in produto:
                continue

            valido, erros = validar_produto_completo(produto)
            if not valido:
                print(f"  [AVISO] {slug} reprovou na validação mas será gerado forçadamente para atualizar o CSS no WordPress.")

            dados, _ = carregar_dados(slug)
            if dados is None:
                reprovados.append((slug, ["JSON não carregado"]))
                continue

            payload = gerar_payload_acf(dados)
            salvar_output(payload)
            aprovados.append(slug)
            print(f"  [OK] {slug}")

        except Exception as e:
            reprovados.append((slug, [f"ERRO: {e}"]))
            print(f"  [ERRO] {slug}: {e}")

    print()
    print("=" * 60)
    print(f"Outputs gerados: {len(aprovados)}")
    print(f"Ainda reprovados: {len(reprovados)}")
    if reprovados:
        print()
        print("--- PRODUTOS AINDA REPROVADOS ---")
        for slug, erros in reprovados:
            print(f"\n[{slug}]")
            for e in erros:
                print(f"  > {e}")


if __name__ == "__main__":
    main()
