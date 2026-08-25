# -*- coding: utf-8 -*-
"""
LOTES 3 & 4 — Preenche campo `aplicacoes` vazio (0 itens).
Usa blocos canônicos por família de produto.
Nunca inventa — usa nomenclatura técnica do setor.
"""
import sys, json, os, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from regras import sanitizar_produto, validar_produto_completo

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DADOS_DIR = os.path.join(BASE_DIR, "gerador", "dados")

# ------------------------------------------------------------------
# BLOCOS CANÔNICOS POR FAMÍLIA
# Cada item: {"titulo": "...", "descricao": "..."}
# Título = equipamento/uso técnico (nunca setor comprador)
# Descrição = uso técnico específico do equipamento
# ------------------------------------------------------------------

APLICACOES_FAMILIA = {

    "exaustor_fs": [
        {
            "titulo": "Evaporador de câmara frigorífica",
            "descricao": "Circulação forçada de ar sobre serpentinas do evaporador em câmaras frias positivas e negativas, mantendo temperatura e distribuição homogênea de frio.",
        },
        {
            "titulo": "Condensador de unidade condensadora",
            "descricao": "Exaustão do calor rejeito pelo condensador de unidades condensadoras monoblock e split em instalações de refrigeração comercial.",
        },
        {
            "titulo": "Coifa de exaustão industrial",
            "descricao": "Renovação e exaustão de ar em cozinhas industriais, lavanderias e ambientes com geração de calor e vapores.",
        },
        {
            "titulo": "Painel de ventilação forçada",
            "descricao": "Resfriamento de componentes elétricos e eletrônicos em painéis de controle, inversores e quadros de distribuição.",
        },
    ],

    "exaustor_hr": [
        {
            "titulo": "Evaporador de câmara fria",
            "descricao": "Circulação forçada de ar no evaporador de câmaras frigoríficas positivas, garantindo distribuição uniforme de temperatura.",
        },
        {
            "titulo": "Condensador de refrigeração comercial",
            "descricao": "Exaustão de calor no condensador de sistemas de refrigeração comercial, como expositores e display frigoríficos.",
        },
        {
            "titulo": "Dry cooler de rejeição de calor",
            "descricao": "Rejeição de calor em dry coolers de sistemas de refrigeração industrial e de processamento.",
        },
        {
            "titulo": "Painel de exaustão de ambiente industrial",
            "descricao": "Ventilação e exaustão de ar quente em ambientes industriais, armazéns e galpões de produção.",
        },
    ],

    "exaustor_nw": [
        {
            "titulo": "Evaporador de câmara fria",
            "descricao": "Circulação de ar sobre serpentinas de evaporadores em câmaras frigoríficas com montagem direta em suporte.",
        },
        {
            "titulo": "Display de supermercado",
            "descricao": "Circulação de ar em expositores e gôndolas refrigeradas de supermercados e padarias.",
        },
        {
            "titulo": "Dry cooler compacto",
            "descricao": "Rejeição de calor em módulos compactos de refrigeração com montagem em estrutura metálica.",
        },
        {
            "titulo": "Painel ou gabinete de automação",
            "descricao": "Ventilação de painéis elétricos e gabinetes de automação industrial com montagem em flangeamento.",
        },
    ],

    "soprador_fs": [
        {
            "titulo": "Evaporador de câmara frigorífica positiva",
            "descricao": "Insuflamento de ar frio nas serpentinas do evaporador de câmaras positivas, mantendo uniformidade de temperatura no ambiente.",
        },
        {
            "titulo": "Galeria de armazenagem refrigerada",
            "descricao": "Insuflamento de ar em galerias frigoríficas para armazenagem de frutas, hortaliças e produtos perecíveis.",
        },
        {
            "titulo": "Secador de grãos em silo",
            "descricao": "Insuflamento de ar para aeração e secagem de grãos em silos e armazéns graneleiros.",
        },
        {
            "titulo": "Unidade de tratamento de ar (UTA)",
            "descricao": "Insuflamento de ar tratado em sistemas de ventilação central e ar-condicionado de ambientes industriais e comerciais.",
        },
    ],

    "soprador_hr": [
        {
            "titulo": "Evaporador de câmara frigorífica",
            "descricao": "Insuflamento forçado de ar frio no evaporador de câmaras positivas e de resfriamento rápido.",
        },
        {
            "titulo": "Galeria de armazenagem fria",
            "descricao": "Insuflamento de ar frio em corredores e galerias de armazenagem frigorífica de grande porte.",
        },
        {
            "titulo": "Câmara de maturação de alimentos",
            "descricao": "Circulação de ar controlada em câmaras de maturação de queijos, embutidos e demais produtos que requerem circulação precisa.",
        },
        {
            "titulo": "Unidade de tratamento de ar (UTA)",
            "descricao": "Insuflamento de ar em UTAs de sistemas de climatização industrial e comercial.",
        },
    ],

    "soprador_nw": [
        {
            "titulo": "Evaporador de câmara fria compacta",
            "descricao": "Insuflamento de ar frio em evaporadores de câmaras de pequeno porte e expositores frigoríficos.",
        },
        {
            "titulo": "Display frigorífico de supermercado",
            "descricao": "Insuflamento de ar sobre serpentinas de displays e gôndolas de supermercados e lojas de conveniência.",
        },
        {
            "titulo": "Câmara de resfriamento rápido",
            "descricao": "Insuflamento de ar em câmaras de blast chilling para resfriamento rápido de alimentos.",
        },
        {
            "titulo": "Unidade de tratamento de ar (UTA) compacta",
            "descricao": "Insuflamento de ar tratado em UTAs compactas de climatização comercial.",
        },
    ],

    "centrifugo_ff": [
        {
            "titulo": "Fancoil de climatização de ambiente",
            "descricao": "Movimentação de ar sobre a serpentina do fancoil em sistemas de ar-condicionado central de ambientes comerciais e industriais.",
        },
        {
            "titulo": "Display de refrigeração de supermercado",
            "descricao": "Circulação de ar sobre a serpentina de evaporação em displays verticais e horizontais de supermercado.",
        },
        {
            "titulo": "Unidade de tratamento de ar (UTA)",
            "descricao": "Movimentação de ar em UTAs de sistemas de climatização central com controle de temperatura e umidade.",
        },
        {
            "titulo": "Evaporador de câmara frigorífica",
            "descricao": "Circulação de ar sobre o evaporador em câmaras frias positivas para distribuição uniforme de frio.",
        },
    ],

    "centrifugo_rf": [
        {
            "titulo": "Fancoil de climatização",
            "descricao": "Insuflamento de ar sobre serpentina de fancoil em sistemas de ar-condicionado central.",
        },
        {
            "titulo": "Evaporador de display frigorífico",
            "descricao": "Circulação de ar em displays frigoríficos verticais de supermercados e açougues.",
        },
        {
            "titulo": "Unidade de tratamento de ar (UTA)",
            "descricao": "Movimentação de ar processado em UTAs de climatização comercial e industrial.",
        },
        {
            "titulo": "Câmara fria de resfriamento",
            "descricao": "Circulação de ar no evaporador de câmaras frias positivas para manutenção de temperatura.",
        },
    ],

    "centrifugo_vs": [
        {
            "titulo": "Exaustão de ambiente confinado",
            "descricao": "Extração de ar viciado em ambientes confinados, galerias subterrâneas e túneis.",
        },
        {
            "titulo": "Ventilação de câmara industrial",
            "descricao": "Insuflamento ou exaustão de ar em câmaras de processamento industrial e estufa.",
        },
        {
            "titulo": "Extração de ar em duto industrial",
            "descricao": "Extração de ar com pressão estática elevada em dutos industriais de grande comprimento.",
        },
        {
            "titulo": "Exaustor de coifa industrial",
            "descricao": "Extração de vapores e ar quente em coifas e capelas de laboratório e cozinha industrial.",
        },
    ],

    "radial_fb": [
        {
            "titulo": "Exaustor de forno industrial",
            "descricao": "Extração de ar quente e vapores em fornos de padaria, panificação e processamento de alimentos.",
        },
        {
            "titulo": "Ventilação de câmara de secagem",
            "descricao": "Circulação de ar quente em câmaras de secagem de madeira, cerâmica e produtos industrializados.",
        },
        {
            "titulo": "Insuflamento em túnel de resfriamento",
            "descricao": "Insuflamento de ar em túneis de resfriamento de alimentos industrializados e produtos de confeitaria.",
        },
        {
            "titulo": "Extração de ar em silo graneleiro",
            "descricao": "Extração de ar em silos de armazenagem de grãos para controle de temperatura e umidade.",
        },
    ],

    "radial_rb": [
        {
            "titulo": "Fancoil de climatização",
            "descricao": "Movimentação de ar sobre serpentina de fancoil em sistemas de climatização.",
        },
        {
            "titulo": "Evaporador de display frigorífico",
            "descricao": "Circulação de ar sobre serpentina em displays de supermercado e açougues.",
        },
        {
            "titulo": "Câmara de secagem industrial",
            "descricao": "Circulação de ar quente em câmaras de secagem e processamento de alimentos.",
        },
        {
            "titulo": "Unidade de tratamento de ar (UTA)",
            "descricao": "Movimentação de ar em UTAs de climatização commercial e industrial.",
        },
    ],

    "radial_ec": [
        {
            "titulo": "Evaporador de câmara fria EC",
            "descricao": "Circulação de ar sobre serpentina de evaporação com controle eletrônico de velocidade (EC) em câmaras frias.",
        },
        {
            "titulo": "Fancoil com controle eletrônico de rotação",
            "descricao": "Movimentação de ar em fancoils com variação eletrônica de rotação para controle preciso de temperatura.",
        },
        {
            "titulo": "Display de refrigeração EC",
            "descricao": "Circulação de ar em displays frigoríficos com motor EC para redução de consumo energético.",
        },
        {
            "titulo": "Unidade de tratamento de ar (UTA) com inversor",
            "descricao": "Insuflamento de ar em UTAs com controle eletrônico de rotação para climatização eficiente.",
        },
    ],

    "inline_fb": [
        {
            "titulo": "Exaustão de banheiro e lavanderia",
            "descricao": "Extração de ar viciado em banheiros, lavanderias e vestiários por duto circular.",
        },
        {
            "titulo": "Extração de ar em cozinha residencial",
            "descricao": "Exaustão de vapores e ar quente em cozinhas residenciais e comerciais por duto embutido.",
        },
        {
            "titulo": "Ventilação de ambientes comerciais",
            "descricao": "Insuflamento ou exaustão de ar em lojas, salas e escritórios com dutos de pequeno diâmetro.",
        },
        {
            "titulo": "Duto de HVAC residencial e comercial",
            "descricao": "Extração ou insuflamento de ar em redes de dutos de sistemas de ventilação residencial e comercial.",
        },
    ],

    "gabinete_ffgb": [
        {
            "titulo": "Painel elétrico industrial",
            "descricao": "Ventilação forçada de painéis de controle, quadros de distribuição e painéis de automação industrial.",
        },
        {
            "titulo": "Gabinete de automação e CLP",
            "descricao": "Resfriamento de controladores lógicos programáveis e inversores em gabinetes de automação.",
        },
        {
            "titulo": "Rack de telecomunicações",
            "descricao": "Ventilação de racks de telecomunicações, servidores e equipamentos de rede em data centers e CPDs.",
        },
        {
            "titulo": "Quadro de distribuição elétrica",
            "descricao": "Ventilação de quadros de distribuição de energia elétrica em subestações e instalações industriais.",
        },
    ],

    "exaustor_ec_fs3": [
        {
            "titulo": "Câmara fria de congelados",
            "descricao": "Exaustão de ar com controle eletrônico de velocidade (EC) em câmaras negativas de congelados e tuneis de congelamento rápido.",
        },
        {
            "titulo": "Evaporador de refrigeração EC",
            "descricao": "Circulação de ar sobre serpentinas de evaporação com motor EC para redução de consumo em câmaras frias.",
        },
        {
            "titulo": "Display de supermercado EC",
            "descricao": "Exaustão de ar em displays frigoríficos com motor EC para maior eficiência energética.",
        },
        {
            "titulo": "Unidade condensadora EC",
            "descricao": "Exaustão do calor rejeito em unidades condensadoras com controle eletrônico de rotação.",
        },
    ],

    "soprador_ec_fs3": [
        {
            "titulo": "Evaporador de câmara fria EC positiva",
            "descricao": "Insuflamento de ar sobre serpentinas de evaporação com motor EC em câmaras frigoríficas positivas.",
        },
        {
            "titulo": "Galeria de armazenagem fria EC",
            "descricao": "Insuflamento de ar frio em galerias de armazenagem refrigerada com controle eletrônico de rotação.",
        },
        {
            "titulo": "Fancoil EC",
            "descricao": "Insuflamento de ar sobre serpentina de fancoil com motor EC para controle preciso e redução de consumo.",
        },
        {
            "titulo": "Câmara de resfriamento rápido EC",
            "descricao": "Insuflamento de ar em câmaras de blast chilling com motor EC para eficiência no resfriamento rápido.",
        },
    ],

    "microventilador": [
        {
            "titulo": "Painel elétrico e rack de automação",
            "descricao": "Ventilação forçada de painéis de controle e racks de automação com compacto volume e baixo consumo.",
        },
        {
            "titulo": "Gabinete de equipamentos eletrônicos",
            "descricao": "Resfriamento de fontes de alimentação, inversores e controladores em gabinetes fechados.",
        },
        {
            "titulo": "Inversor de frequência e nobreak",
            "descricao": "Resfriamento de componentes de potência em inversores de frequência e sistemas de nobreak industrial.",
        },
        {
            "titulo": "Rack de TI e equipamentos de rede",
            "descricao": "Extração de calor em racks de servidores, switches e roteadores em CPDs e salas técnicas.",
        },
    ],

    "motoventilador": [
        {
            "titulo": "Câmara frigorífica de grande porte",
            "descricao": "Circulação de ar em câmaras frigoríficas de grande volume com alta vazão e pressão estática.",
        },
        {
            "titulo": "Condensador de alta capacidade",
            "descricao": "Exaustão do calor rejeito em condensadores de sistemas de refrigeração industrial de grande porte.",
        },
        {
            "titulo": "Dry cooler industrial",
            "descricao": "Rejeição de calor em dry coolers de sistemas de refrigeração industrial e data centers.",
        },
        {
            "titulo": "Silo de armazenagem e secagem de grãos",
            "descricao": "Insuflamento de ar para aeração, secagem e conservação de grãos em silos graneleiros.",
        },
    ],

    "default": [
        {
            "titulo": "Evaporador de câmara frigorífica",
            "descricao": "Circulação forçada de ar sobre serpentinas de evaporação em câmaras frias.",
        },
        {
            "titulo": "Condensador de unidade condensadora",
            "descricao": "Exaustão do calor rejeito no condensador de unidades condensadoras.",
        },
        {
            "titulo": "Painel elétrico e gabinete industrial",
            "descricao": "Ventilação de painéis de controle e gabinetes de automação industrial.",
        },
        {
            "titulo": "Coifa e exaustão de ambiente industrial",
            "descricao": "Renovação e exaustão de ar em ambientes industriais com geração de calor.",
        },
    ],
}


def detectar_familia_aplicacoes(slug, produto):
    s = slug.lower()
    categoria = produto.get("categoria", "").lower()

    # Microventiladores
    if "micro" in s or "micro" in categoria:
        return "microventilador"

    # Gabinetes
    if "gabinete" in s or "ffgb" in s or "fbgb" in s:
        return "gabinete_ffgb"

    # In-line
    if "in-line" in s or "fb-100" in s or "fb-150" in s or "fb-200" in s or "fb-250" in s or "fb-315" in s:
        return "inline_fb"

    # Radial EC
    if "radial" in s and "ec" in s:
        return "radial_ec"

    # Radial RB
    if "rb2c" in s or "rb4c" in s:
        return "radial_rb"

    # Radial FB
    if "radial" in s or ("fb-2-" in s and "mcd" in s) or ("fb-4-" in s and "mcd" in s) or "fb1d" in s or "fb-2-" in s or "fb-4-" in s:
        return "radial_fb"

    # Centrífugo simples aspiração VS
    if "vs" in s and ("ff" in s or "centrifugo" in s or "centrifugo" in s):
        return "centrifugo_vs"

    # Centrífugo RF
    if "rf-" in s or ("centrifugo" in s and "rf" in s):
        return "centrifugo_rf"

    # Centrífugo FF
    if "centrifugo" in s or ("ff-2-" in s and "mm" in s) or ("ff-4-" in s and "mm" in s):
        return "centrifugo_ff"

    # Soprador EC FS3
    if "fs3-" in s and ("-v-" in s or "v-ecp" in s or "soprador" in s):
        return "soprador_ec_fs3"

    # Exaustor EC FS3
    if "fs3-" in s and ("-e-" in s or "e-ecp" in s or "exaustor" in s):
        return "exaustor_ec_fs3"

    # Moto-ventilador
    if "moto" in s or "710" in s or "hr-2-" in s or "hr-6-" in s or "hr-8-" in s:
        return "motoventilador"

    # Soprador NW/HR
    if ("soprador" in s or "vm" in s or "vt" in s) and ("nw" in s or "hr" in s):
        return "soprador_nw" if "nw" in s else "soprador_hr"

    # Soprador FS
    if "soprador" in s or ("-vm" in s) or ("-vt" in s) or ("-vmp" in s) or ("-vtp" in s):
        return "soprador_fs"

    # Exaustor NW
    if ("exaustor" in s or "-em" in s or "-et" in s) and "nw" in s:
        return "exaustor_nw"

    # Exaustor HR
    if ("exaustor" in s or "-em" in s or "-et" in s) and "hr" in s:
        return "exaustor_hr"

    # Exaustor FS (padrão)
    if "exaustor" in s or "-em" in s or "-et" in s:
        return "exaustor_fs"

    return "default"


def tem_aplicacoes_vazias(erros):
    return any("aplicacoes com 0 itens" in e.lower() for e in erros)


def processar_arquivo(caminho):
    with open(caminho, encoding="utf-8") as f:
        produto = json.load(f)

    valido, erros_antes = validar_produto_completo(produto)
    if valido:
        return "ok", 0

    if not tem_aplicacoes_vazias(erros_antes):
        return "skip", 0

    slug = produto.get("slug", os.path.basename(caminho).replace(".json", ""))
    familia = detectar_familia_aplicacoes(slug, produto)
    aplicacoes_bloco = APLICACOES_FAMILIA.get(familia, APLICACOES_FAMILIA["default"])

    produto["aplicacoes"] = aplicacoes_bloco[:4]
    produto = sanitizar_produto(produto)  # sanitiza após preencher

    valido_depois, erros_depois = validar_produto_completo(produto)
    erros_resolvidos = len(erros_antes) - len(erros_depois)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(produto, f, ensure_ascii=False, indent=2)

    return ("corrigido", familia, erros_resolvidos) if erros_resolvidos > 0 else ("sem_melhora", familia, 0)


def main():
    arquivos = sorted(glob.glob(os.path.join(DADOS_DIR, "*.json")))
    print(f"Lotes 3 & 4 — Preenchimento de aplicações vazias por família")
    print(f"Arquivos: {len(arquivos)}")
    print("=" * 60)

    stats = {"ok": 0, "corrigido": 0, "sem_melhora": 0, "skip": 0}
    for arq in arquivos:
        slug = os.path.basename(arq).replace(".json", "")
        resultado = processar_arquivo(arq)
        if len(resultado) == 3:
            status, familia, n = resultado
        else:
            status, n = resultado
            familia = ""
        stats[status] += 1
        if status == "corrigido":
            print(f"  [CORRIGIDO +{n} | {familia}] {slug}")
        elif status == "sem_melhora":
            print(f"  [SEM_MELHORA | {familia}] {slug}")

    print()
    print(f"Resultado: {stats['ok']} já OK | {stats['skip']} sem aplicacoes vazias | {stats['corrigido']} corrigidos | {stats['sem_melhora']} sem melhora")


if __name__ == "__main__":
    main()
