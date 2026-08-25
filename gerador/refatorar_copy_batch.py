# -*- coding: utf-8 -*-
import sys, json, os, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from regras import gerar_resumo_tecnico_datasheet, gerar_texto_mercado, sanitizar_produto, sanitizar_texto
from automacao.preencher_aplicacoes_batch import detectar_familia_aplicacoes, APLICACOES_FAMILIA

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados")

def main():
    arquivos = sorted(glob.glob(os.path.join(DADOS_DIR, "*.json")))
    arquivos = arquivos[:10]
    print(f"Refatorando Copy B2B em {len(arquivos)} arquivos...")
    
    for arq in arquivos:
        with open(arq, encoding="utf-8") as f:
            produto = json.load(f)
            
        slug = produto.get("slug", os.path.basename(arq).replace(".json", ""))
        sku = produto.get("sku", "")
        eh_bt = "BT" in sku.upper() or "bt" in slug.lower() or "etbt" in slug or "vmbt" in slug or "vtbt" in slug
        
        # Extrair dados do array de especificações
        specs = {s.get("atributo", "").lower(): s.get("valor", "") for s in produto.get("especificacoes", [])}
        
        # Preencher chaves no root para as funções do regras.py funcionarem
        def find_spec(keys):
            for k, v in specs.items():
                for key in keys:
                    if key in k:
                        return v
            return ""

        produto["descricao_ds"] = find_spec(["descricao", "descrição"])
        produto["regime"] = find_spec(["regime"]) or "S1"
        produto["protecao_mecanica"] = find_spec(["ip", "grau de prote", "grau"]) or "IP-54"
        produto["mancais"] = find_spec(["mancal", "rolamento"]) or "Rolamentos de esfera"
        produto["temperatura"] = find_spec(["temperatura", "temp"]) or "-30 °C a 60 °C"
        produto["ruido"] = find_spec(["ruído", "ruido", "dba"]) or "Não informado"
        
        # 1. Refatorar Resumo Técnico
        funcao = "exaustão" if "exaustor" in slug else "insuflação (sopramento)" if "soprador" in slug else "ventilação"
        
        def clean_val(v):
            if not v or not isinstance(v, str): return ""
            vl = v.strip().lower()
            if vl in ["", "não informado", "nao informado", "especificada em catálogo", "especificada no datasheet", "dba especificado", "nd"]: return ""
            return v.strip()

        desc_val = clean_val(produto.get("descricao_ds", ""))
        categoria_val = clean_val(produto.get("categoria", ""))
        if not desc_val:
            if categoria_val.lower().startswith("ventilador"):
                desc_limpa = categoria_val.capitalize()
            else:
                desc_limpa = f"Ventilador {categoria_val.lower() if categoria_val else 'industrial'}"
        else:
            desc_limpa = desc_val
        
        para1 = f"{desc_limpa}, projetado para {funcao} e movimentação de ar em equipamentos de refrigeração, climatização e processos industriais."
        
        ruido_val = clean_val(produto.get('ruido', ''))
        temp_val = clean_val(produto.get('temperatura', ''))
        
        para2 = f"Construído para operação contínua sob regime {produto['regime']}, o modelo {sku} oferece proteção mecânica {produto['protecao_mecanica']} e utiliza {produto['mancais'].lower()}."
        if temp_val:
            para2 += f" O conjunto suporta faixa térmica de {temp_val}."
        if ruido_val:
            para2 = para2[:-1] + f", com emissão de ruído de {ruido_val}."
            
        produto["resumo_tecnico"] = sanitizar_texto(para1 + "\n\n" + para2)
        
        # 1.5. Refatorar Checklist (remover falhas do LLM como 'especificada em catálogo')
        pot_val = clean_val(specs.get('potencia consumida', specs.get('potencia', '')))
        pot_txt = f" com potência de {pot_val}" if pot_val else ""
        
        rot_val = clean_val(specs.get('velocidade', specs.get('rotacao', '')))
        rot_txt = f" e rotação de {rot_val}" if rot_val else ""
        
        ruido_txt = f"Nível de ruído de {ruido_val}." if ruido_val else "Operação estável com materiais industriais de alta resistência."
        
        tensao_val = clean_val(specs.get('tensao nominal', specs.get('tensao', ''))) or "não especificada"
        
        produto["hero_checklist"] = [
            sanitizar_texto(f"Alimentação elétrica {tensao_val}{pot_txt}{rot_txt}."),
            sanitizar_texto(f"Proteção mecânica {produto['protecao_mecanica']} com {produto['mancais'].lower()} para operação em regime {produto['regime']}."),
            sanitizar_texto(ruido_txt)
        ]
        
        # 2. Refatorar Aplicações (Forçar canônicos longos)
        familia = detectar_familia_aplicacoes(slug, produto)
        blocos = APLICACOES_FAMILIA.get(familia, APLICACOES_FAMILIA["default"])
        produto["aplicacoes"] = blocos
        
        # 3. Refatorar Mercado (Neutro sem inferências)
        # Tenta pegar setores já mapeados ou usa fallback genérico baseado na família
        setores = []
        if produto.get("aplicacoes_excel"):
            setores = [a.get("equipamento", "") for a in produto.get("aplicacoes_excel") if a.get("equipamento")]
        if not setores or len(setores) < 4:
            setores = ["refrigeração comercial e industrial", "máquinas para alimentos", "laticínios", "agroindústria"]
        
        produto["mercado"] = gerar_texto_mercado(sku, setores, eh_bt=eh_bt)
        
        # Sanitiza e salva
        produto = sanitizar_produto(produto)
        
        with open(arq, "w", encoding="utf-8") as f:
            json.dump(produto, f, ensure_ascii=False, indent=2)
            
    print("Processo finalizado!")

if __name__ == "__main__":
    main()
