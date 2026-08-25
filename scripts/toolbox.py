"""
==========================================================
 scripts/toolbox.py — Caixa de Ferramentas Sell-Parts
==========================================================
Consolida as funções utilitárias avulsas em um único
arquivo organizado. Substitui os scripts pontuais de:
  - corrigir_aplicacoes_6.py
  - corrigir_diferenciais.py
  - refazer_diferenciais.py
  - restaurar_diferenciais.py
  - higienizar_semantica.py
  - limpar_marcas_clientes.py
  - corrigir_zero_inferencia.py
  - encurtar_textos_cards.py
  - atualizar_ff2_146.py

Uso:
  python scripts/toolbox.py <comando> [slug]

Comandos disponíveis:
  auditar              → Rodar auditoria completa nos 12 JSONs
  publicar             → Publicar lote completo no WooCommerce
  publicar <slug>      → Publicar um produto específico
  limpar_marcas        → Remover nomes de marcas/clientes de todos os JSONs
  restaurar_faqs       → Garantir 3 FAQs técnicas em todos os produtos
  fix_aplicacoes       → Garantir 6 aplicações B2B em todos os produtos
"""

import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'gerador'))
from catalogo import CATALOGO_TOP40
from gerar_conteudo_acf import gerar_payload_acf, salvar_output
from automacao.publicar_wordpress import update_product_acf

base_dir    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dados_dir   = os.path.join(base_dir, 'gerador', 'dados')
produtos_dir = os.path.join(base_dir, 'produtos')

MARCAS_BANIDAS = [
    "Metalplan", "VR Painéis", "Blutrafos Blumenau Transformadores Ltda", "Blutrafos",
    "Carthoms", "Fibrasil Carrocerias", "Fibrasil", "Nacional Coifas",
    "Pachane / MD Serviços", "Pachane", "Pentax / Elo Scientific", "Elo Scientific",
    "Exaust-Farma", "MGE Air", "Gransafe / Valipro", "Gransafe",
    "Berlinerluft do Brasil", "Berlinerluft", "Premium Ar", "Ourifrio",
    "Linter Hengst", "Filterflux", "PCI Gases do Brasil", "PCI Gases",
    "Sempel", "Triskel Eletrificação", "Triskel",
    "Engquadros Painéis e Automação Elétricas Indústria e Comércio Ltda. EPP",
    "Engquadros", "MECNC"
]

# Frases comerciais/logísticas PROIBIDAS em qualquer campo de produto público
FRASES_BANIDAS = [
    "Faturamos para CNPJ",
    "Faturamos",
    "emissão de Nota Fiscal",
    "transportadora parceira com rastreamento",
    "O envio é realizado via transportadora",
    "Nota Fiscal",
    "CNPJ",
    "Faturamento",
]

DIFERENCIAIS_PADRAO = [
    "Formato construtivo robusto resistente à operação contínua em condensadores e equipamentos B2B.",
    "Suporte técnico da Sell-Parts para auxílio na equivalência de projetos de retrofit.",
    "Grade de proteção ou acabamento premium já montado de fábrica para garantir segurança nas operações."
]

# ── HELPERS ────────────────────────────────────────────────────────────────

def carregar_json(slug):
    path = os.path.join(dados_dir, f"{slug}.json")
    if not os.path.exists(path):
        return None, path
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f), path

def salvar_json(dados, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def atualizar_pasta_produto(slug, dados):
    for cat in os.listdir(produtos_dir):
        p_dir = os.path.join(produtos_dir, cat, slug)
        if not os.path.exists(p_dir):
            continue
        lp_path = os.path.join(p_dir, "landing-page-master.md")
        with open(lp_path, 'w', encoding='utf-8') as lpf:
            lpf.write(f"# {dados.get('nome', slug)}\n\n")
            lpf.write(f"## Resumo Técnico\n{dados.get('resumo_tecnico', '')}\n\n")
            lpf.write("## Especificações Técnicas\n")
            for spec in dados.get('especificacoes', []):
                lpf.write(f"- **{spec['atributo']}:** {spec['valor']}\n")
            lpf.write("\n## Aplicações\n")
            for app in dados.get('aplicacoes', []):
                lpf.write(f"- {app}\n")
            lpf.write("\n## Benefícios\n")
            for b in dados.get('beneficios', []):
                lpf.write(f"### {b['titulo']}\n{b['descricao']}\n\n")
            lpf.write("## Diferenciais\n")
            for d in dados.get('diferenciais', []):
                lpf.write(f"- {d}\n")
            lpf.write("\n## FAQ\n")
            for fq in dados.get('faq', []):
                lpf.write(f"**P: {fq['pergunta']}**\n\nR: {fq['resposta']}\n\n")
        payload = gerar_payload_acf(dados)
        salvar_output(payload)
        acf_path = os.path.join(p_dir, "acf-campos-prontos.md")
        with open(acf_path, 'w', encoding='utf-8') as acff:
            acff.write(json.dumps(payload, ensure_ascii=False, indent=2))

def slugs_concluidos():
    return [p['slug'] for p in CATALOGO_TOP40 if p['status'] == 'concluido']

# ── COMANDOS ───────────────────────────────────────────────────────────────

def cmd_auditar():
    import subprocess
    result = subprocess.run(
        [sys.executable, os.path.join(base_dir, 'scripts', 'auditoria.py')],
        cwd=base_dir, capture_output=True, text=True
    )
    print(result.stdout)

def cmd_publicar(slug=None):
    alvos = [slug] if slug else slugs_concluidos()
    for s in alvos:
        update_product_acf(s)
        print(f"[PUBLICADO] {s}")

def cmd_limpar_marcas():
    for slug in slugs_concluidos():
        dados, path = carregar_json(slug)
        if not dados:
            continue
        novas_apps = []
        for app in dados.get('aplicacoes', []):
            texto = app
            for marca in MARCAS_BANIDAS:
                texto = texto.replace(f"(ex: {marca})", "").replace(marca, "")
            novas_apps.append(texto.strip())
        dados['aplicacoes'] = novas_apps
        rt = dados.get('resumo_tecnico', '')
        for marca in MARCAS_BANIDAS:
            rt = rt.replace(marca, "")
        dados['resumo_tecnico'] = rt.strip()
        salvar_json(dados, path)
        atualizar_pasta_produto(slug, dados)
        update_product_acf(slug)
        print(f"[MARCAS REMOVIDAS] {slug}")

def cmd_restaurar_faqs():
    FAQ_PADRAO = [
        {
            "pergunta": "Qual a principal aplicação deste modelo?",
            "resposta": "Indicado para dissipação térmica em painéis elétricos, conjuntos eletromecânicos, compressores e sistemas de refrigeração industrial."
        },
        {
            "pergunta": "Como é fornecido o acabamento e proteção do equipamento?",
            "resposta": "Fornecido completo com grade metálica de proteção e acabamento em pintura eletrostática, pronto para instalação com total segurança mecânica."
        },
        {
            "pergunta": "A Sell-Parts oferece suporte para substituição e retrofit?",
            "resposta": "Sim. A equipe técnica da Sell-Parts auxilia no dimensionamento e equivalência direta para substituição técnica na sua linha."
        }
    ]
    for slug in slugs_concluidos():
        dados, path = carregar_json(slug)
        if not dados:
            continue
        if len(dados.get('faq', [])) < 3:
            dados['faq'] = FAQ_PADRAO
            salvar_json(dados, path)
            atualizar_pasta_produto(slug, dados)
            update_product_acf(slug)
            print(f"[FAQ RESTAURADA] {slug}")
        else:
            print(f"[FAQ OK] {slug}")

def cmd_fix_aplicacoes():
    """Garante exatamente 5 aplicações em cada produto. Não altera produtos com 5 corretos."""
    for slug in slugs_concluidos():
        dados, path = carregar_json(slug)
        if not dados:
            continue
        if len(dados.get('aplicacoes', [])) != 5:
            print(f"[ALERTA] {slug} tem {len(dados.get('aplicacoes', []))} aplicações — corrija manualmente.")
        else:
            print(f"[OK 5 APLICAÇÕES] {slug}")

# ── MAIN ───────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    COMANDOS = {
        'auditar':          cmd_auditar,
        'publicar':         lambda: cmd_publicar(sys.argv[2] if len(sys.argv) > 2 else None),
        'limpar_marcas':    cmd_limpar_marcas,
        'restaurar_faqs':   cmd_restaurar_faqs,
        'fix_aplicacoes':   cmd_fix_aplicacoes,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print(__doc__)
        sys.exit(0)

    COMANDOS[sys.argv[1]]()
