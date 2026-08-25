# -*- coding: utf-8 -*-
"""
=====================================================
  Demo Store — DASHBOARD DE ORQUESTRAÇÃO B2B
  Painel de controle futurista para gestão dos 40 produtos
=====================================================
"""
import json
import os
import sys
import subprocess
import datetime

# Adiciona o diretório gerador ao path
PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
GERADOR_DIR = os.path.join(PROJ_DIR, "gerador")
sys.path.insert(0, GERADOR_DIR)

try:
    import streamlit as st
except ImportError:
    print("Streamlit não encontrado. Instale com: pip install streamlit")
    sys.exit(1)

from gerador.catalogo import CATALOGO_TOP40
from gerador import auth
from gerador import audit

# ================================================================
# CONSTANTES
# ================================================================
DB_PATH = os.path.join(PROJ_DIR, "gerador", "produtos_db.json")
DADOS_DIR = os.path.join(GERADOR_DIR, "dados")
OUTPUT_DIR = os.path.join(GERADOR_DIR, "output")

# ================================================================
# BANCO DE DADOS LOCAL (JSON)
# ================================================================
def load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    db = {}
    for p in CATALOGO_TOP40:
        db[p["slug"]] = {
            "pos": p["pos"],
            "nome": p["nome"],
            "slug": p["slug"],
            "cliques": p["cliques"],
            "impressoes": p["impressoes"],
            "status": p["status"],
            "tem_datasheet": False,
            "datasheet_info": "",
            "segmentos": "",
            "parceiros": "",
            "data_conclusao": None,
            "log_publicacao": "",
            "ativo_wp": True,
        }
    save_db(db)
    return db

def save_db(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def sync_db_from_dados(db):
    """
    Atualiza o painel a partir de gerador/dados/*.json (fonte de verdade de todos os produtos do catálogo).
    Retorna (db, n_novos, n_atualizados).
    """
    novos = 0
    atualizados = 0
    if not os.path.isdir(DADOS_DIR):
        return db, 0, 0

    for fname in os.listdir(DADOS_DIR):
        if not fname.endswith(".json"):
            continue
        slug = fname[:-5]
        path = os.path.join(DADOS_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                dados = json.load(f)
        except Exception:
            continue

        acf_ok = os.path.exists(os.path.join(OUTPUT_DIR, f"{slug}_acf.json"))
        nome = dados.get("nome") or slug
        sku = dados.get("sku") or ""
        pdf = dados.get("pdf_fonte") or ""

        cat_map = {p["slug"]: p for p in CATALOGO_TOP40}
        cat_info = cat_map.get(slug, {})
        req_cliques = int(dados.get("cliques") or cat_info.get("cliques") or 0)
        req_impressoes = int(dados.get("impressoes") or cat_info.get("impressoes") or 0)
        req_pos = int(cat_info.get("pos") or (len(db) + 1))

        if slug not in db:
            db[slug] = {
                "pos": req_pos,
                "nome": nome,
                "slug": slug,
                "cliques": req_cliques,
                "impressoes": req_impressoes,
                "status": "em_producao",
                "tem_datasheet": bool(pdf),
                "datasheet_info": pdf,
                "datasheet_file": pdf,
                "sku": sku,
                "ativo_wp": True,
                "data_conclusao": datetime.datetime.now().isoformat(),
                "aprovacao": False,
            }
            novos += 1
            continue

        changed = False
        entry = db[slug]
        if "slug" not in entry:
            entry["slug"] = slug
            changed = True
        if nome and entry.get("nome") != nome:
            entry["nome"] = nome
            changed = True
        if sku and entry.get("sku") != sku:
            entry["sku"] = sku
            changed = True
        if req_cliques > 0 and entry.get("cliques", 0) != req_cliques:
            entry["cliques"] = req_cliques
            changed = True
        if req_impressoes > 0 and entry.get("impressoes", 0) != req_impressoes:
            entry["impressoes"] = req_impressoes
            changed = True
        if pdf and entry.get("datasheet_file") != pdf:
            entry["datasheet_file"] = pdf
            entry["datasheet_info"] = pdf
            entry["tem_datasheet"] = True
            changed = True
        # marca ativo se tem JSON local (aparece no painel)
        if not entry.get("ativo_wp"):
            entry["ativo_wp"] = True
            changed = True
        # Mantém o status existente
        if "status" not in entry:
            entry["status"] = "em_producao"
            changed = True
        if changed:
            atualizados += 1

    return db, novos, atualizados


def refresh_painel():
    """Recarrega DB do disco + sincroniza com dados/ e limpa seleção stale."""
    db = load_db()
    db, novos, atualizados = sync_db_from_dados(db)
    save_db(db)
    # limpa seleção se o produto sumiu
    sel = st.session_state.get("selected_product")
    if sel and sel not in db:
        st.session_state["selected_product"] = None
    st.session_state["_last_refresh"] = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state["_refresh_stats"] = {"novos": novos, "atualizados": atualizados}
    return db

def get_status_icon(status):
    if status in ["publicado", "concluido"]:
        return "🚀 "
    elif status == "aprovado":
        return "🟢 "
    elif status == "aguardando_supervisor":
        return "🟠 "
    elif status == "em_revisao":
        return "🟣 "
    elif status == "em_producao":
        return "🔵 "
    elif status in ["em_pesquisa", "em_andamento"]:
        return "🟡 "
    return "🔴 "

def get_grupo_familia(nome, slug):
    """Classifica o produto na família técnica correta, incluindo variante técnica."""
    import re
    nome_up = nome.upper()

    # ── Variante técnica (sufixo) ─────────────────────────────────
    variante = ""
    if "BT" in nome_up.split():
        variante = " — Baixa Temperatura (BT)"
    elif any(x in nome_up for x in ["BTBT", "EMBT", "VMBT", "VTBT", "ETBT"]):
        variante = " — Baixa Temperatura (BT)"
    elif "7 PAS" in nome_up or "7PAS" in nome_up:
        variante = " — 7 Pás"
    elif "PW" in nome_up:
        variante = " — Alta Pressão (PW)"
    elif "440V" in nome_up or "440 V" in nome_up:
        variante = " — 440 V"
    elif "VTP" in nome_up or "ETP" in nome_up:
        variante = " — Grade Plana (P)"

    # ── Família principal ─────────────────────────────────────────
    if any(x in nome_up for x in ["CENTRIF", "FF/2", "FF/4", "RF/2"]):
        return f"Centrífugos{variante}"
    if any(x in nome_up for x in ["TANGENCIAL", "TGH"]):
        return f"Tangenciais{variante}"
    if any(x in nome_up for x in ["MICRO", "A12038", "A15051", "A18061", "A25089", "D4020"]):
        return f"Microventiladores{variante}"
    if any(x in nome_up for x in ["AXIAL", "FS/2", "FS/4", "FS/6", "FB/"]):
        m = re.search(r"(\d{3})\s*MM", nome_up)
        if m:
            d = int(m.group(1))
            if d <= 200:  base = "Axiais ≤ 200 mm"
            elif d <= 300: base = "Axiais 250–300 mm"
            elif d <= 400: base = "Axiais 350–400 mm"
            elif d <= 500: base = "Axiais 450–500 mm"
            else:          base = "Axiais ≥ 630 mm"
            return f"{base}{variante}"
        return f"Axiais{variante}"
    return f"Outros{variante}"


def get_status_label(status):
    mapping = {
        "pesquisa_pendente": "🔴 Pesquisa Pendente",
        "em_pesquisa": "🟡 Em Pesquisa",
        "em_producao": "🔵 Em Produção",
        "em_revisao": "🟣 Em Revisão",
        "aguardando_supervisor": "🟠 Aguardando Sup.",
        "aprovado": "🟢 Aprovado",
        "publicado": "🚀 Publicado",
        # Legacy mappings just in case
        "pendente": "🔴 Pendente",
        "em_andamento": "🟡 Em Andamento",
        "concluido": "🚀 Concluído"
    }
    return mapping.get(status, status)

# ================================================================
# STREAMLIT CONFIG
# ================================================================
st.set_page_config(
    page_title="Sell-Parts — Orquestrador B2B",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================================================================
# CORPORATE Demo Store CSS
# ================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* === GLOBAL === */
    .main {
        background-color: #0B1120 !important;
        color: #F3F4F6 !important;
    }
    
    /* Subtle grid background */
    .main::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image: 
            linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
        z-index: 0;
    }
    
    [data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1F2937 !important;
    }
    
    /* === CORPORATE TITLE === */
    .corporate-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.5em;
        font-weight: 700;
        color: #3B82F6;
        letter-spacing: -0.5px;
        margin-bottom: 0;
    }
    
    .corporate-subtitle {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75em;
        color: #9CA3AF;
        letter-spacing: 0px;
        text-transform: uppercase;
        opacity: 0.8;
    }
    
    /* === CORPORATE METRIC CARDS === */
    .corporate-card {
        background: #111827;
        border: 1px solid #1F2937;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
        position: relative;
    }
    .corporate-value {
        font-family: 'Inter', sans-serif;
        font-size: 2.2em;
        font-weight: 800;
        color: #3B82F6;
    }
    .corporate-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.75em;
        color: #9CA3AF;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    
    .corporate-card-green .corporate-value { color: #34D399; }
    .corporate-card-yellow .corporate-value { color: #FBBF24; }
    .corporate-card-purple .corporate-value { color: #A78BFA; }
    
    /* === STEP BOXES === */
    .step-box {
        background: #111827;
        border: 1px solid #1F2937;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }
    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        background: #3B82F6;
        border-radius: 4px;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 0.85em;
        color: #FFFFFF;
        margin-right: 10px;
    }
    .step-title {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.05em;
        color: #F3F4F6;
    }
    
    /* === STATUS BADGES === */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 4px;
        font-family: 'Inter', sans-serif;
        font-size: 0.75em;
        font-weight: 600;
        text-transform: uppercase;
    }
    .status-concluido { 
        background: rgba(16, 185, 129, 0.1); 
        color: #34D399; 
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .status-em_andamento { 
        background: rgba(245, 158, 11, 0.1); 
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    .status-pendente { 
        background: rgba(239, 68, 68, 0.1); 
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }
    
    /* === PREVIEW CARD === */
    .preview-container {
        background: #111827;
        border: 1px solid #1F2937;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    .preview-container iframe {
        border-radius: 6px;
        border: 1px solid #1F2937;
    }
    
    /* === DIVIDER === */
    .corporate-divider {
        height: 1px;
        background: #1F2937;
        margin: 20px 0;
        border: none;
    }
    
    /* === SIDEBAR BUTTONS === */
    [data-testid="stSidebar"] div[data-testid="stButton"] button {
        font-size: 0.8em;
        text-align: left;
        border: 1px solid #1F2937;
        background: #111827;
        color: #F3F4F6;
        transition: all 0.2s;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
        border-color: #3B82F6;
        background: rgba(59, 130, 246, 0.1);
        color: #3B82F6;
    }
    
    /* === MAIN BUTTONS === */
    div[data-testid="stButton"] button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #3B82F6 !important;
        border-color: #3B82F6 !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #2563EB !important;
        border-color: #2563EB !important;
    }
    
    /* === SIDEBAR TEXT COLOR FIXES === */
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #3B82F6 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: #9CA3AF !important;
    }
    [data-testid="stSidebar"] label {
        color: #F3F4F6 !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)


# ================================================================
# AUTENTICAÇÃO CENTRALIZADA (TELA DE LOGIN)
# ================================================================
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

if st.session_state["current_user"] is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 0.15, 1])
    with col_l2:
        if os.path.exists(os.path.join(PROJ_DIR, "logo.png")):
            st.image(os.path.join(PROJ_DIR, "logo.png"), use_container_width=True)
            
    st.markdown("<h1 style='text-align: center; color: #F3F4F6; margin-top: 15px;'>Gerenciador de Páginas de Produto</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9CA3AF; margin-bottom: 40px;'>Faça login para gerenciar o painel B2B</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container():
            
            login_input = st.text_input("Usuário:", key="login_field")
            pwd_input = st.text_input("Senha:", type="password", key="pwd_field")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("ENTRAR NO PAINEL", type="primary", use_container_width=True):
                user = auth.authenticate(login_input, pwd_input)
                if user:
                    st.session_state["current_user"] = user
                    st.success(f"Bem-vindo, {user['nome']}!")
                    import time; time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
            
    
    st.stop() # Interrompe a execução do resto do app se não estiver logado


user = st.session_state["current_user"]
role = user["role"]

# ================================================================
# LOAD DATA (refresh real sob demanda)


# ================================================================
if st.session_state.get("_force_refresh"):
    db = refresh_painel()
    st.session_state["_force_refresh"] = False
else:
    db = load_db()

# ================================================================
# SIDEBAR
# ================================================================
with st.sidebar:
    if os.path.exists(os.path.join(PROJ_DIR, "logo.png")):
        st.image(os.path.join(PROJ_DIR, "logo.png"), width=70)
    st.markdown('<p class="corporate-title">Demo Store</p>', unsafe_allow_html=True)
    st.markdown('<p class="corporate-subtitle">// Painel Operacional</p>', unsafe_allow_html=True)
    st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)

    if st.button(
        "🔄 Atualizar Painel",
        use_container_width=True,
        help="Recarrega produtos_db.json e sincroniza com gerador/dados",
    ):
        st.session_state["_force_refresh"] = True
        st.rerun()

    last_ref = st.session_state.get("_last_refresh")
    stats = st.session_state.get("_refresh_stats") or {}
    if last_ref:
        st.caption(f"Último refresh: {last_ref}")
        if stats.get("novos") or stats.get("atualizados"):
            st.caption(
                f"+{stats.get('novos', 0)} novos · {stats.get('atualizados', 0)} atualizados"
            )

    st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)

    # ================================================================
    # AUTENTICAÇÃO CENTRAL
    # ================================================================
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None

    if st.session_state["current_user"] is None:
        st.markdown("### 🔑 Acesso ao Sistema")
        login_input = st.text_input("Usuário:", key="login_field")
        pwd_input = st.text_input("Senha:", type="password", key="pwd_field")
        
        if st.button("🔓 Entrar", use_container_width=True):
            user = auth.authenticate(login_input, pwd_input)
            if user:
                st.session_state["current_user"] = user
                st.success(f"Bem-vindo, {user['nome']}!")
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
        
        role = "bloqueado"
    else:
        user = st.session_state["current_user"]
        role = user["role"]
        
        # User Badge
        st.markdown(f"""
        <div style="background: #1F2937; padding: 10px; border-radius: 6px; border-left: 4px solid #3B82F6; margin-bottom: 10px;">
            <div style="color: #9CA3AF; font-size: 0.75em; text-transform: uppercase;">Usuário Logado</div>
            <div style="color: #F3F4F6; font-weight: bold;">{user['nome']}</div>
            <div style="color: #3B82F6; font-size: 0.85em; font-family: monospace;">{role.upper()}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔒 Sair do Sistema", use_container_width=True):
            st.session_state["current_user"] = None
            st.rerun()
            
    st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)

    # Filtra banco: só produtos ativos no site / syncados
    filtered_db = {k: v for k, v in db.items() if v.get("ativo_wp", True)}
    sorted_products = sorted(filtered_db.values(), key=lambda x: x.get("pos", 999))

    if role in ["operador", "revisor"]:
        total = len(filtered_db)
        concluidos = sum(
            1 for v in filtered_db.values()
            if v.get("status") in ["concluido", "publicado", "aprovado"]
        )
        em_andamento = sum(
            1 for v in filtered_db.values()
            if v.get("status") in [
                "em_andamento", "em_pesquisa", "em_producao",
                "em_revisao", "aguardando_supervisor",
            ]
        )
        pendentes = sum(
            1 for v in filtered_db.values()
            if v.get("status") in ["pendente", "pesquisa_pendente", ""]
        )

        cols = st.columns(3)
        cols[0].metric("Concluidos", concluidos)
        cols[1].metric("Em Andamento", em_andamento)
        cols[2].metric("Pendentes", pendentes)
        st.caption(f"{total} produtos ativos no painel")
        st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)
    
    if role in ["supervisor", "admin"]:
        st.markdown("### 🔍 Filtros & Fila de Auditoria")
        
        # Filtro por busca rápida
        busca_daniel = st.text_input("🔍 Buscar nome ou SKU:", placeholder="Ex: FS/4-500 ou 146mm...", key="daniel_busca")
        
        # Filtro por grupo/família
        grupos_disponiveis = sorted(set(
            get_grupo_familia(p['nome'], p['slug'])
            for p in sorted_products
            if p.get('ativo_wp')
        ))
        grupo_sel = st.selectbox(
            "Família / Grupo:",
            ["Todos os Grupos"] + grupos_disponiveis,
            key="daniel_grupo"
        )
        
        st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)
        
        # Separar produtos em 3 listas por status real
        lista_audit = []
        lista_aprov = []
        lista_prod = []
        
        for p in sorted_products:
            if not p.get('ativo_wp'):
                continue
                
            # Aplicação dos Filtros
            if busca_daniel and (busca_daniel.lower() not in p['nome'].lower() and busca_daniel.lower() not in p.get('sku', '').lower()):
                continue
            if grupo_sel != "Todos os Grupos" and get_grupo_familia(p['nome'], p['slug']) != grupo_sel:
                continue
                
            status = p.get('status', '')
            aprovado = p.get('aprovacao', False)
            
            if aprovado or status in ['aprovado', 'publicado', 'concluido']:
                lista_aprov.append(p)
            elif status in ['aguardando_supervisor', 'em_revisao']:
                lista_audit.append(p)
            else:
                lista_prod.append(p)

        # Renderizar as 3 seções organizadas em abas (Tabs)
        t_aud, t_apr, t_prd = st.tabs([
            f"🟡 Auditoria ({len(lista_audit)})",
            f"🟢 Aprovados ({len(lista_aprov)})",
            f"⚙️ Produção ({len(lista_prod)})"
        ])
        
        def render_product_group(product_list, tab_key_prefix):
            if not product_list:
                st.caption("Nenhum produto nesta categoria.")
                return
            import collections
            grupos = collections.defaultdict(list)
            for p in product_list:
                g = get_grupo_familia(p['nome'], p['slug'])
                grupos[g].append(p)
            for grupo_nome in sorted(grupos.keys()):
                prods_g = grupos[grupo_nome]
                st.markdown(f"**{grupo_nome}** ({len(prods_g)})")
                for p in prods_g:
                    ap = p.get('aprovacao', False)
                    icon = "🟢" if ap else ("🟡" if p.get('status') in ['aguardando_supervisor', 'em_revisao'] else "🔵")
                    label = f"{icon} {p['nome']}"
                    if st.button(label, key=f"{tab_key_prefix}_{p['slug']}", use_container_width=True):
                        st.session_state['selected_product'] = p['slug']
                        st.rerun()
                st.markdown("")

        with t_aud:
            render_product_group(lista_audit, "aud")
            
        with t_apr:
            render_product_group(lista_aprov, "apr")
            
        with t_prd:
            render_product_group(lista_prod, "prd")
    elif role == "operador":
        st.markdown("### 📋 Fila de Produção")
        for prod in sorted_products:
            if not prod.get("ativo_wp", True):
                continue
            icon = get_status_icon(prod.get("status", "pendente"))
            label = f"{icon} #{prod.get('pos', 999):02d} — {prod['nome']}"
            if st.button(label, key=f"btn_op_{prod['slug']}", use_container_width=True):
                st.session_state["selected_product"] = prod["slug"]
                st.rerun()

# ================================================================
# MAIN AREA
# ================================================================
if role == "bloqueado":
    st.warning("🔒 Acesso Restrito ao Modo Operador")
    st.info("Insira a senha de operador no menu lateral para liberar o painel.")
    st.stop()

# Dropdown de Navegação Rápida por Seções / Produtos (Produção)
filtered_db = {k: v for k, v in db.items() if v.get("ativo_wp", True)}
sorted_products = sorted(filtered_db.values(), key=lambda x: x.get("pos", 999))

slug_to_idx = {"HOME": 0}
idx_to_slug = {0: None}
for idx, p in enumerate(sorted_products, start=1):
    slug_to_idx[p["slug"]] = idx
    idx_to_slug[idx] = p["slug"]

cur_slug = st.session_state.get("selected_product", None)
# ================================================================
# VISTAS ESPECIAIS & CURVA ABC
# ================================================================
def render_curva_abc_section(filtered_db, sorted_products):
    import pandas as pd
    import altair as alt

    st.markdown("## 📈 Curva ABC & Inteligência de Mercado B2B")
    st.caption("Classificação estratégica do catálogo Sell-Parts em Classe A, B e C baseada no engajamento de tráfego, pesquisas no Google (Search Console) e relevância técnica.")
    st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)

    abc_data = []
    total_cliques = 0
    total_impressoes = 0
    total_vendas = 0
    total_fat = 0.0

    for p in sorted_products:
        slug = p["slug"]
        nome = p["nome"]
        sku = p.get("sku") or slug
        cliques = int(p.get("cliques", 0) or 0)
        impressoes = int(p.get("impressoes", 0) or 0)
        vendas_un = int(p.get("vendas_unidades", 0) or 0)
        fat = float(p.get("faturamento_rs", 0) or 0)
        cli_b2b = int(p.get("clientes_b2b", 0) or 0)
        pos = int(p.get("pos", 999))
        grupo = get_grupo_familia(nome, slug)

        total_cliques += cliques
        total_impressoes += impressoes
        total_vendas += vendas_un
        total_fat += fat

        # Cruzamento exato: Unidades Vendidas B2B * Engajamento Real (Impressões + Cliques Google)
        # SKUs sem cliques/impressões não entram no Top 10 para garantir relevância real de mercado
        mult_vendas = 1.0 if (cliques > 0 or impressoes > 0) else 0.001
        score = (vendas_un * mult_vendas) + (impressoes * 2.0) + (cliques * 20.0)

        abc_data.append({
            "slug": slug,
            "nome": nome,
            "sku": sku,
            "pos": pos,
            "grupo": grupo,
            "cliques": cliques,
            "impressoes": impressoes,
            "vendas_unidades": vendas_un,
            "faturamento_rs": fat,
            "clientes_b2b": cli_b2b,
            "score": score,
            "status": p.get("status", "em_producao"),
            "aprovacao": p.get("aprovacao", False),
        })

    abc_data.sort(key=lambda x: x["score"], reverse=True)

    n_total = len(abc_data)
    n_a = max(1, int(n_total * 0.20))
    n_b = max(1, int(n_total * 0.30))

    for idx, item in enumerate(abc_data):
        if idx < n_a:
            item["classe_abc"] = "Classe A (Carro-Chefe)"
            item["badge_abc"] = "🟢 Classe A"
        elif idx < (n_a + n_b):
            item["classe_abc"] = "Classe B (Alto Potencial)"
            item["badge_abc"] = "🟡 Classe B"
        else:
            item["classe_abc"] = "Classe C (Nicho / Especial)"
            item["badge_abc"] = "⚪ Classe C"

    # KPIs de Topo
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    count_a = sum(1 for x in abc_data if "Classe A" in x["classe_abc"])
    count_b = sum(1 for x in abc_data if "Classe B" in x["classe_abc"])
    count_c = sum(1 for x in abc_data if "Classe C" in x["classe_abc"])
    total_cli_b2b = sum(x["clientes_b2b"] for x in abc_data)

    k1.metric("SKUs Analisados", f"{n_total} produtos")
    k2.metric("Classe A (Carros-Chefe)", f"{count_a} SKUs")
    k3.metric("Vendas (Unidades)", f"{total_vendas:,}".replace(",", "."))
    k4.metric("Clientes B2B", f"{total_cli_b2b:,}".replace(",", "."))
    k5.metric("Tráfego Google (Cliques)", f"{total_cliques:,}".replace(",", "."))
    k6.metric("Demanda Google (Impressões)", f"{total_impressoes:,}".replace(",", "."))

    st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)

    # Gráficos Visuais
    col_g1, col_g2 = st.columns([1, 1])

    with col_g1:
        st.markdown("#### 🍩 Distribuição da Curva ABC")
        df_pie = pd.DataFrame([
            {"Classe": "Classe A (Carro-Chefe)", "Quantidade": count_a},
            {"Classe": "Classe B (Alto Potencial)", "Quantidade": count_b},
            {"Classe": "Classe C (Nicho / Especial)", "Quantidade": count_c},
        ])
        chart_donut = alt.Chart(df_pie).mark_arc(innerRadius=55).encode(
            theta=alt.Theta(field="Quantidade", type="quantitative"),
            color=alt.Color(
                field="Classe",
                type="nominal",
                scale=alt.Scale(
                    domain=["Classe A (Carro-Chefe)", "Classe B (Alto Potencial)", "Classe C (Nicho / Especial)"],
                    range=["#10B981", "#F59E0B", "#6B7280"]
                )
            ),
            tooltip=["Classe", "Quantidade"]
        ).properties(height=280)
        st.altair_chart(chart_donut, use_container_width=True)

    with col_g2:
        st.markdown("#### 🏆 Top 10 Produtos pela Curva ABC (Vendas + SEO)")
        top10_gsc = sorted(abc_data, key=lambda x: x["score"], reverse=True)[:10]
        
        chart_data = []
        for x in top10_gsc:
            p_label = x["sku"] or x["nome"][:22]
            chart_data.append({"Produto": p_label, "Métrica": "Vendas (Unidades)", "Valor": x["vendas_unidades"]})
            chart_data.append({"Produto": p_label, "Métrica": "Cliques Google (SEO)", "Valor": x["cliques"]})
            chart_data.append({"Produto": p_label, "Métrica": "Impressões Google", "Valor": x["impressoes"]})

        df_bar = pd.DataFrame(chart_data)
        chart_bar = alt.Chart(df_bar).mark_bar(cornerRadiusEnd=4).encode(
            x=alt.X("Valor:Q", title="Vendas (Un) vs Cliques vs Impressões", axis=alt.Axis(format="d")),
            y=alt.Y("Produto:N", sort="-x", title=None),
            color=alt.Color("Métrica:N", scale=alt.Scale(
                domain=["Vendas (Unidades)", "Cliques Google (SEO)", "Impressões Google"],
                range=["#10B981", "#3B82F6", "#F59E0B"]
            )),
            tooltip=["Produto", "Métrica", "Valor"]
        ).properties(height=280)
        st.altair_chart(chart_bar, use_container_width=True)

    st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)

    # Tabela Interativa ABC
    st.markdown("### 📋 Tabela de Inteligência & Ranking Curva ABC")
    filtro_grupo = st.selectbox(
        "Filtrar Família Técnica:",
        ["Todas as Famílias"] + sorted(list(set(x["grupo"] for x in abc_data))),
        key="abc_grupo_filter"
    )

    table_rows = []
    for rank_i, item in enumerate(abc_data, start=1):
        if filtro_grupo != "Todas as Famílias" and item["grupo"] != filtro_grupo:
            continue
        table_rows.append({
            "Rank": f"#{rank_i:02d}",
            "Curva ABC": item["badge_abc"],
            "Produto": item["nome"],
            "SKU": item["sku"],
            "Família Técnica": item["grupo"],
            "Vendas (Un)": item["vendas_unidades"],
            "Clientes B2B": item["clientes_b2b"],
            "Cliques Google": item["cliques"],
            "Impressões Google": item["impressoes"],
            "Status WP": get_status_label(item["status"]),
            "slug": item["slug"]
        })

    df_table = pd.DataFrame(table_rows)
    if not df_table.empty:
        st.dataframe(
            df_table.drop(columns=["slug"]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.caption("Nenhum produto encontrado.")


def clear_product_edit_cache(selected):
    """Limpa todo o cache de edição e dynamic lists do session_state para o produto selecionado."""
    if not selected:
        return
    st.session_state.pop(f"edit_data_{selected}", None)
    st.session_state.pop(f"mtime_{selected}", None)
    for lk in ["merc", "chk", "ben", "dif", "app", "eq", "faq"]:
        sk = f"dyn_{lk}_{selected}"
        trash_k = f"trash_{lk}_{selected}"
        if sk in st.session_state:
            for item in st.session_state.get(sk, []):
                uid = item.get("id") if isinstance(item, dict) else None
                if uid:
                    st.session_state.pop(f"{lk}_val_{uid}", None)
                    st.session_state.pop(f"{lk}_tit_{uid}", None)
                    st.session_state.pop(f"{lk}_desc_{uid}", None)
            st.session_state.pop(sk, None)
        st.session_state.pop(trash_k, None)


def render_ficha_360_produto(selected_slug, db):
    import pandas as pd

    json_path = os.path.join(DADOS_DIR, f"{selected_slug}.json")
    if not os.path.exists(json_path):
        st.warning(f"O arquivo de dados locais ({selected_slug}.json) não foi localizado em gerador/dados.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    p_db = db.get(selected_slug, {})
    st.markdown(f"## 🔍 Ficha 360° — {dados.get('nome', selected_slug)}")
    st.caption(f"SKU / Código: {dados.get('sku', selected_slug)} | Slug: {selected_slug} | Status: {get_status_label(p_db.get('status'))}")

    link_wp = f"https://DemoStore.com.br/produto/{selected_slug}/"
    st.markdown(f'<a href="{link_wp}" target="_blank" style="display: inline-block; padding: 8px 16px; background: #1250B2; color: white; border-radius: 6px; text-decoration: none; font-weight: 600;">🌐 Abrir Produto no Site Oficial</a>', unsafe_allow_html=True)
    st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)

    t_f1, t_f2, t_f3, t_f4, t_f5 = st.tabs([
        "📑 1. Resumo & Specs",
        "🔧 2. Aplicações & Onde Usar",
        "🧠 3. Mercados Atendidos",
        "🚀 4. Benefícios & Diferenciais",
        "❓ 5. FAQ & Alertas"
    ])

    with t_f1:
        st.markdown("#### Resumo Técnico (Descrição Principal)")
        st.write(dados.get("resumo_tecnico", "Não informado."))
        st.markdown("")
        st.markdown("#### Badges do Topo (Hero Checklist)")
        for chk in dados.get("hero_checklist", []):
            st.markdown(f"- ✓ {chk}")
        st.markdown("")
        st.markdown("#### Especificações Técnicas (100% Datasheet)")
        specs = dados.get("especificacoes", [])
        if specs:
            df_specs = pd.DataFrame([{"Atributo": s.get("atributo"), "Valor": s.get("valor"), "Confiança": s.get("confianca"), "Fonte": s.get("fonte", "Datasheet")} for s in specs])
            st.dataframe(df_specs, use_container_width=True, hide_index=True)
        else:
            st.caption("Especificações não cadastradas.")

    with t_f2:
        st.markdown("#### Bloco 1 — Aplicações (O que o produto faz)")
        app_cat = dados.get("aplicacoes_categoria", {})
        cards_cat = app_cat.get("cards") if isinstance(app_cat, dict) and app_cat.get("cards") else dados.get("aplicacoes", [])
        st.caption(app_cat.get("intro", "") if isinstance(app_cat, dict) else "")
        for card in cards_cat:
            if isinstance(card, dict):
                st.markdown(f"• **{card.get('titulo')}**: {card.get('descricao')}")
            else:
                st.markdown(f"• {card}")
        st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)
        st.markdown("#### Bloco 2 — Onde Usar (Equipamentos Físicos)")
        app_eq = dados.get("aplicacoes_equipamento", {})
        cards_eq = app_eq.get("cards") if isinstance(app_eq, dict) and app_eq.get("cards") else (dados.get("onde_usar") or dados.get("equipamentos") or [])
        st.caption(app_eq.get("intro", "") if isinstance(app_eq, dict) else "")
        for card in cards_eq:
            if isinstance(card, dict):
                st.markdown(f"• **{card.get('titulo')}**: {card.get('descricao')}")
            else:
                st.markdown(f"• {card}")

    with t_f3:
        st.markdown("#### Bloco 3 — Mercados Atendidos (Perfil do Comprador B2B)")
        mercado_txt = dados.get("mercado") or ""
        if isinstance(mercado_txt, list):
            mercado_txt = "\n".join(str(x) for x in mercado_txt)
        st.write(mercado_txt if mercado_txt else "Mercados não informados.")

    with t_f4:
        st.markdown("#### Benefícios (Proposta de Valor)")
        for b in dados.get("beneficios", []):
            st.markdown(f"• **{b.get('titulo')}**: {b.get('descricao')}")
        st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)
        st.markdown("#### Diferenciais Competitivos")
        for d in dados.get("diferenciais", []):
            st.markdown(f"- {d}")

    with t_f5:
        st.markdown("#### FAQ (Perguntas e Respostas)")
        faqs = dados.get("faq", [])
        if faqs:
            for faq in faqs:
                st.markdown(f"**Q: {faq.get('pergunta')}**")
                st.markdown(f"A: {faq.get('resposta')}")
                st.markdown("")
        else:
            st.caption("FAQ não cadastrado.")
            
        if dados.get("alerta_tecnico"):
            st.warning(f"⚠️ Alerta Técnico: {dados.get('alerta_tecnico')}")


selected = st.session_state.get("selected_product", None)

if selected is None:
    # ============================================================
    # HOME — HEADER PRINCIPAL DO PAINEL (ACIMA DAS ABAS)
    # ============================================================
    col_logo, col_h = st.columns([1, 8])
    with col_logo:
        if os.path.exists(os.path.join(PROJ_DIR, "logo.png")):
            st.image(os.path.join(PROJ_DIR, "logo.png"), width=65)
    with col_h:
        if role in ["supervisor", "admin"]:
            st.markdown('<p class="corporate-title">Painel de Auditoria de Conteúdo B2B</p>', unsafe_allow_html=True)
            st.markdown('<p class="corporate-subtitle">// Modo Supervisor — Homologação & Validação de Páginas de Produto</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="corporate-title">Dashboard de Orquestração B2B</p>', unsafe_allow_html=True)
            st.markdown('<p class="corporate-subtitle">// Sell-Parts Brasil — Automação & Alta Performance</p>', unsafe_allow_html=True)
    st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)

    # ============================================================
    # HOME — ABAS PRINCIPAIS DO PAINEL
    # ============================================================
    tab_status, tab_abc_graph, tab_busca_360 = st.tabs([
        "🏠 Status Geral & Produção",
        "📈 Curva ABC & Inteligência de Mercado",
        "🔍 Ficha 360° do Produto"
    ])

    with tab_abc_graph:
        render_curva_abc_section(filtered_db, sorted_products)

    with tab_busca_360:
        st.markdown("### 🔍 Busca Rápida 360° por Produto")
        sel_360_slug = st.selectbox(
            "Selecione um produto para buscar e visualizar o dossiê completo (360°):",
            options=[p["slug"] for p in sorted_products],
            format_func=lambda s: f"#{filtered_db[s].get('pos', 999):02d} — {filtered_db[s]['nome']} ({filtered_db[s].get('sku', s)})",
            key="sel_360_dropdown"
        )
        if sel_360_slug:
            render_ficha_360_produto(sel_360_slug, db)

    with tab_status:
        if role in ["supervisor", "admin"]:
            # Métricas de Auditoria
            total_produtos = len(filtered_db)
            
            # Filtra os que aguardam aprovação
            aguardando_auditoria = [
                p for p in sorted_products
                if p.get("ativo_wp") and p.get("status") in ["em_revisao", "aguardando_supervisor"]
            ]
            
            aprovados_e_publicados = [
                p for p in sorted_products
                if p.get("ativo_wp") and (p.get("aprovacao") or p.get("status") in ["aprovado", "publicado", "concluido"])
            ]
            
            em_producao_list = [
                p for p in sorted_products
                if p.get("ativo_wp") and p.get("status") in ["em_producao", "pendente", "pesquisa_pendente", ""]
            ]

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="corporate-card corporate-card-yellow">
                    <div class="corporate-value">{len(aguardando_auditoria)}</div>
                    <div class="corporate-label">Aguardando Auditoria</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="corporate-card corporate-card-green">
                    <div class="corporate-value">{len(aprovados_e_publicados)}</div>
                    <div class="corporate-label">Aprovados / No Ar</div>
                </div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="corporate-card">
                    <div class="corporate-value">{len(em_producao_list)}</div>
                    <div class="corporate-label">Em Produção / Pendentes</div>
                </div>""", unsafe_allow_html=True)
            with col4:
                pct_audited = round((len(aprovados_e_publicados) / total_produtos) * 100) if total_produtos > 0 else 0
                st.markdown(f"""
                <div class="corporate-card corporate-card-purple">
                    <div class="corporate-value">{pct_audited}%</div>
                    <div class="corporate-label">Taxa Homologada</div>
                </div>""", unsafe_allow_html=True)



        else:
            # ============================================================
            # HOME — VISÃO GERAL (OPERADOR)
            # ============================================================
            
            total = len(filtered_db)
            concluidos = sum(
                1 for v in filtered_db.values()
                if v.get("status") in ["concluido", "publicado", "aprovado"]
            )
            em_andamento = sum(
                1 for v in filtered_db.values()
                if v.get("status") in [
                    "em_andamento", "em_pesquisa", "em_producao",
                    "em_revisao", "aguardando_supervisor",
                ]
            )
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="corporate-card">
                    <div class="corporate-value">{total}</div>
                    <div class="corporate-label">Total Produtos</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="corporate-card corporate-card-green">
                    <div class="corporate-value">{concluidos}</div>
                    <div class="corporate-label">Concluidos</div>
                </div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="corporate-card corporate-card-yellow">
                    <div class="corporate-value">{em_andamento}</div>
                    <div class="corporate-label">Em Andamento</div>
                </div>""", unsafe_allow_html=True)
            with col4:
                pct = round((concluidos / total) * 100) if total > 0 else 0
                st.markdown(f"""
                <div class="corporate-card corporate-card-purple">
                    <div class="corporate-value">{pct}%</div>
                    <div class="corporate-label">Progresso</div>
                </div>""", unsafe_allow_html=True)
            
            st.markdown("")
            st.progress(concluidos / total if total > 0 else 0, text=f"Progresso geral: {concluidos}/{total} produtos")
            
            st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)
            
            # === PRODUTOS CONCLUÍDOS — PREVIEW ===
            prods_concluidos = [p for p in sorted_products if p.get("status") in ["concluido", "publicado", "aprovado"]]
            
            if prods_concluidos:
                st.markdown("### Produtos Concluidos — Preview")
                st.caption("Clique para abrir a landing page diretamente no site.")
                
                cols_preview = st.columns(3)
                for i, prod in enumerate(prods_concluidos):
                    with cols_preview[i % 3]:
                        link = f"https://DemoStore.com.br/produto/{prod['slug']}/"
                        st.markdown(f"""
                        <div class="preview-container">
                            <p style="font-family: 'Inter'; font-weight: 700; color: #F3F4F6; margin-bottom: 8px;">
                                #{prod.get('pos', 999):02d} — {prod['nome']}
                            </p>
                            <p style="font-family: 'JetBrains Mono'; font-size: 0.75em; color: #9CA3AF; margin-bottom: 12px;">
                                {prod.get('cliques', 0)} cliques / {prod.get('impressoes', 0)} impressoes
                            </p>
                            <a href="{link}" target="_blank" style="
                                display: inline-block;
                                padding: 8px 20px;
                                background: #3B82F6;
                                color: white;
                                border-radius: 6px;
                                text-decoration: none;
                                font-family: 'Inter';
                                font-weight: 600;
                                font-size: 0.85em;
                            ">Ver Landing Page</a>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown("")
            
            st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)
            
            # === TABELA GERAL ===
            st.markdown("### Visao Geral Completa")
            table_data = []
            for prod in sorted_products:
                if not prod.get("ativo_wp", False):
                    continue
                table_data.append({
                    "#": prod.get("pos", 999),
                    "Produto": prod["nome"],
                    "Status": get_status_label(prod.get("status", "pendente")),
                    "Última Edição": prod.get("updated_by", "—"),
                    "Aprovado por": prod.get("approved_by_name", "—"),
                    "Cliques": prod.get("cliques", 0),
                    "Impressões": prod.get("impressoes", 0)
                })
            st.dataframe(table_data, width='stretch', hide_index=True)
 
else:
    # ============================================================
    # FLUXO DE TRABALHO DO PRODUTO SELECIONADO
    # ============================================================
    col_nav1, col_nav2 = st.columns([4, 1])
    with col_nav1:
        prod_slugs = [p["slug"] for p in sorted_products]
        cur_i = prod_slugs.index(selected) if selected in prod_slugs else 0
        chosen_s = st.selectbox(
            "📌 Alternar Produto:",
            options=prod_slugs,
            format_func=lambda s: f"#{filtered_db[s].get('pos', 999):02d} — {filtered_db[s]['nome']}",
            index=cur_i
        )
        if chosen_s != selected:
            st.session_state["selected_product"] = chosen_s
            st.rerun()
    with col_nav2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("⬅️ Voltar para a Lista", use_container_width=True, key="btn_back_home_detail"):
            st.session_state["selected_product"] = None
            st.rerun()

    st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)
    prod = db[selected]
    # FONTE DE VERDADE ÚNICA: is_approved depends apenas do campo booleano 'aprovacao'
    is_approved = bool(prod.get("aprovacao", False))
    
    # Se perfil for Supervisor, renderiza a área simplificada de aprovação de Supervisor
    if role in ["supervisor", "admin"]:
        st.markdown("## 🛡️ Avaliação e Aprovação de Supervisor")
        st.markdown(f'<p class="corporate-title">#{prod.get("pos", 999):02d} — {prod["nome"]}</p>', unsafe_allow_html=True)
        
        link_prod = f"https://DemoStore.com.br/produto/{prod['slug']}/"
       
        # Header Informativo de Status e Acesso Rápido (link único aqui)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; background: #111827; border: 1px solid #1F2937; padding: 14px 20px; border-radius: 8px; margin-bottom: 20px;">
            <div>
                <span style="font-size: 13px; color: #94a3b8;">Status Atual:</span> 
                <strong style="color: #38bdf8; font-size: 15px;">{get_status_label(prod.get('status'))}</strong>
                {' · <span style="color: #4ade80; font-weight: bold;">✅ APROVADO</span>' if is_approved else ' · <span style="color: #facc15; font-weight: bold;">⏳ AGUARDANDO AUDITORIA</span>'}
            </div>
            <div>
                <a href="{link_prod}" target="_blank" style="padding: 7px 14px; background: #1250B2; color: white; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600;">🌐 Abrir Página no Site</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
       
        # Histórico Rápido
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            st.markdown(f"**Responsável / Última Edição:**<br>{prod.get('updated_by', '—')}", unsafe_allow_html=True)
        with col_h2:
            if prod.get('aprovacao'):
                aprovador = prod.get('approved_by_name', '—')
                if not aprovador: aprovador = '—'
            else:
                aprovador = '—'
            st.markdown(f"**Aprovado por:**<br>{aprovador}", unsafe_allow_html=True)
        with col_h3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📜 Ver Histórico Completo", use_container_width=True, key=f"btn_hist_{selected}"):
                st.session_state["show_history"] = selected
                st.rerun()

        if st.session_state.get("show_history") == selected:
            st.markdown("### 📜 Histórico de Ações")
            history = audit.get_product_history(selected)
            if history:
                for h in reversed(history):
                    st.markdown(f"**{h['timestamp'][:16].replace('T', ' ')}** — {h['user_name']} ({h['action']})")
            else:
                st.caption("Nenhum histórico registrado para este produto.")
            if st.button("Fechar Histórico", key=f"close_hist_{selected}"):
                st.session_state["show_history"] = None
                st.rerun()
        st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)
        # Exibe os textos do JSON local se existir para ele analisar a LPP
        json_path = os.path.join(DADOS_DIR, f"{prod['slug']}.json")
        if os.path.exists(json_path):
            state_key = f"edit_data_{selected}"
           
            # Validação de cache via data de modificação do arquivo (mtime)
            current_mtime = os.path.getmtime(json_path)
            mtime_key = f"mtime_{selected}"
            if state_key in st.session_state and st.session_state.get(mtime_key) != current_mtime:
                st.session_state.pop(state_key, None)

            if state_key not in st.session_state or st.session_state.get("_force_refresh", False):
                with open(json_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                   
                # Compatibilidade e auto-conversão para o campo 'mercado' (padrão string B2B)
                mercado_raw = json_data.get("mercados") or json_data.get("mercado") or []
                if isinstance(mercado_raw, list):
                    if all(isinstance(x, dict) for x in mercado_raw):
                        json_data["mercados"] = [f"{x.get('titulo')}: {x.get('descricao')}" for x in mercado_raw]
                        json_data["mercado"] = "\n\n".join(json_data["mercados"])
                    else:
                        json_data["mercados"] = [str(x) for x in mercado_raw]
                        json_data["mercado"] = "\n".join(json_data["mercados"])
                elif isinstance(mercado_raw, str):
                    json_data["mercados"] = [line.strip() for line in mercado_raw.split("\n") if line.strip()]
                    json_data["mercado"] = mercado_raw
                           
                # Inicializa lixeira se não existir
                if "lixeira" not in json_data:
                    json_data["lixeira"] = {}
                for k in ["hero_checklist", "beneficios", "diferenciais", "aplicacoes_categoria", "aplicacoes_equipamento", "faq", "mercados"]:
                    if k not in json_data["lixeira"]:
                        json_data["lixeira"][k] = []
                       
                st.session_state[state_key] = json_data
                st.session_state[mtime_key] = current_mtime
                if st.session_state.get("_force_refresh", False):
                    st.session_state["_force_refresh"] = False
                   
            json_data = st.session_state[state_key]

            # --------------------------------------------------------
            # PAINEL UNIFICADO DE AÇÕES E PUBLICAÇÃO (PARTE DE CIMA)
            # is_approved já calculado no topo a partir de prod = db[selected]
            # --------------------------------------------------------


            st.markdown("### 📝 Editor de Conteúdo")
            st.caption("Navegue pelas abas abaixo para editar o conteúdo. Você pode adicionar, excluir itens específicos e até desfazer exclusões (lixeira). Ao clicar em 'SALVAR REVISÃO', tudo será sincronizado.")
           
            tab_e1, tab_e2, tab_e3, tab_e4, tab_e5, tab_e6, tab_e7, tab_e8 = st.tabs([
                "📄 Resumo", 
                "🛒 Mercados",
                "⭐ Badges", 
                "🚀 Benefícios", 
                "🏆 Diferenciais", 
                "⚙️ Aplicações", 
                "🏭 Onde Usar", 
                "❓ FAQ"
            ])
           
            import uuid
           
            def init_dynamic_list(list_key, json_list, is_single=False):
                state_key = f"dyn_{list_key}_{selected}"
                if state_key not in st.session_state:
                    items = []
                    for item in json_list:
                        uid = str(uuid.uuid4())
                        if is_single:
                            st.session_state[f"{list_key}_val_{uid}"] = item if isinstance(item, str) else ""
                        else:
                            tit = item.get("titulo", item.get("pergunta", "")) if isinstance(item, dict) else (item if isinstance(item, str) else "")
                            desc = item.get("descricao", item.get("resposta", "")) if isinstance(item, dict) else ""
                            st.session_state[f"{list_key}_tit_{uid}"] = tit
                            st.session_state[f"{list_key}_desc_{uid}"] = desc
                        items.append({"id": uid})
                    # Garantir pelo menos 1 item se a lista for vazia
                    if not items:
                        uid = str(uuid.uuid4())
                        items.append({"id": uid})
                    st.session_state[state_key] = items
                    st.session_state[f"trash_{list_key}_{selected}"] = []

            def render_dynamic_list(list_key, title_label="Título", desc_label="Descrição", is_single=False):
                state_key = f"dyn_{list_key}_{selected}"
                trash_key = f"trash_{list_key}_{selected}"
                items = st.session_state[state_key]
               
                for i, item in enumerate(items):
                    uid = item["id"]
                    col1, col2 = st.columns([11, 1])
                    with col1:
                        if is_single:
                            st.text_area(title_label, key=f"{list_key}_val_{uid}", height=80, label_visibility="collapsed", placeholder=title_label)
                        else:
                            st.text_input(title_label, key=f"{list_key}_tit_{uid}", placeholder=title_label)
                            st.text_area(desc_label, key=f"{list_key}_desc_{uid}", height=80, placeholder=desc_label)
                    with col2:
                        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_{list_key}_{uid}", help="Excluir este item especificamente"):
                            if is_single:
                                val = st.session_state.get(f"{list_key}_val_{uid}", "")
                                st.session_state[trash_key].append({"id": uid, "val": val, "index": i})
                            else:
                                tit = st.session_state.get(f"{list_key}_tit_{uid}", "")
                                desc = st.session_state.get(f"{list_key}_desc_{uid}", "")
                                st.session_state[trash_key].append({"id": uid, "tit": tit, "desc": desc, "index": i})
                            st.session_state[state_key].pop(i)
                            st.rerun()
                    st.markdown("---")
                   
                colA, colB, _ = st.columns([2, 2, 4])
                if colA.button("➕ Adicionar Novo", key=f"add_{list_key}_{selected}", use_container_width=True):
                    uid = str(uuid.uuid4())
                    st.session_state[state_key].append({"id": uid})
                    st.rerun()
                   
                if st.session_state[trash_key]:
                    if colB.button("↩️ Desfazer Exclusão", key=f"undo_{list_key}_{selected}", use_container_width=True):
                        restored = st.session_state[trash_key].pop()
                        uid = restored["id"]
                        if is_single:
                            st.session_state[f"{list_key}_val_{uid}"] = restored["val"]
                        else:
                            st.session_state[f"{list_key}_tit_{uid}"] = restored["tit"]
                            st.session_state[f"{list_key}_desc_{uid}"] = restored["desc"]
                        idx = min(restored["index"], len(st.session_state[state_key]))
                        st.session_state[state_key].insert(idx, {"id": uid})
                        st.rerun()

            def extract_dynamic_list(list_key, is_single=False):
                result = []
                for item in st.session_state[f"dyn_{list_key}_{selected}"]:
                    uid = item["id"]
                    if is_single:
                        val = st.session_state.get(f"{list_key}_val_{uid}", "").strip()
                        if val: result.append(val)
                    else:
                        tit = st.session_state.get(f"{list_key}_tit_{uid}", "").strip()
                        desc = st.session_state.get(f"{list_key}_desc_{uid}", "").strip()
                        if tit or desc:
                            if list_key == "faq":
                                result.append({"pergunta": tit, "resposta": desc})
                            else:
                                result.append({"titulo": tit, "descricao": desc})
                return result


           
            # INITIALIZATION
            def force_reinit_if_corrupted():
                for lk in ["chk", "ben", "dif", "app", "eq", "faq", "merc"]:
                    sk = f"dyn_{lk}_{selected}"
                    if sk in st.session_state and len(st.session_state[sk]) > 0:
                        first_uid = st.session_state[sk][0]["id"]
                        test_key = f"{lk}_val_{first_uid}" if lk in ["chk", "dif"] else f"{lk}_tit_{first_uid}"
                        if test_key not in st.session_state:
                            del st.session_state[sk]
                if f"dyn_faq_{selected}" in st.session_state:
                    if len(st.session_state[f"dyn_faq_{selected}"]) > 0:
                        first_uid = st.session_state[f"dyn_faq_{selected}"][0]["id"]
                        if not st.session_state.get(f"faq_tit_{first_uid}", ""):
                            # If the FAQ is completely empty because of the previous bug, force reinit
                            del st.session_state[f"dyn_faq_{selected}"]
            force_reinit_if_corrupted()

            init_dynamic_list("merc", json_data.get("mercados", []), is_single=True)
            init_dynamic_list("chk", json_data.get("hero_checklist", []), is_single=True)
            init_dynamic_list("ben", json_data.get("beneficios", []), is_single=False)
            init_dynamic_list("dif", json_data.get("diferenciais", []), is_single=True)
           
            app_cat = json_data.get("aplicacoes_categoria", {})
            cards_app = app_cat.get("cards", []) if isinstance(app_cat.get("cards"), list) else json_data.get("aplicacoes", [])
            init_dynamic_list("app", cards_app, is_single=False)
           
            app_eq = json_data.get("aplicacoes_equipamento", {})
            cards_eq = app_eq.get("cards", []) if isinstance(app_eq.get("cards"), list) else (json_data.get("onde_usar") or json_data.get("equipamentos") or [])
            init_dynamic_list("eq", cards_eq, is_single=False)
           
            init_dynamic_list("faq", json_data.get("faq", []), is_single=False)


            # RENDERING UI
            with tab_e1:
                st.info("💡 Dica: O resumo deve focar no aspecto técnico e benefícios. Não use formatação markdown.")
                st.text_area("Resumo Técnico (Copy B2B)", value=json_data.get("resumo_tecnico", ""), height=200, key=f"rt_edit_{selected}")
           
            with tab_e2:
                st.info("💡 Dica: Adicione os mercados atendidos neste componente (ex: Refrigeração comercial, Agronegócio).")
                render_dynamic_list("merc", title_label="Mercado", is_single=True)

            with tab_e3:
                st.info("💡 Dica: Adicione selos curtos (ex: 'Pronta Entrega', 'Bi-Tensão 110/220V').")
                render_dynamic_list("chk", title_label="Badge", is_single=True)
           
            with tab_e4:
                st.info("💡 Dica: Destaque os maiores benefícios operacionais do produto. (Regra: 4 cards recomendados)")
                render_dynamic_list("ben", title_label="Título do Benefício", desc_label="Descrição")
           
            with tab_e5:
                st.info("💡 Dica: Por que comprar de nós? (Ex: Garantia, Estoque local, Qualidade).")
                render_dynamic_list("dif", title_label="Diferencial", is_single=True)
           
            with tab_e6:
                st.info("💡 Dica: O que o produto faz. Ex: Exaustão, Resfriamento.")
                st.text_input("Título da Seção", value=app_cat.get("titulo", ""), key=f"app_cat_t_{selected}")
                st.text_area("Introdução", value=app_cat.get("intro", ""), height=80, key=f"app_cat_i_{selected}")
                st.markdown("##### Cards de Aplicação")
                render_dynamic_list("app", title_label="Nome da Aplicação", desc_label="Descrição da Aplicação")
           
            with tab_e7:
                st.info("💡 Dica: Onde o produto é fisicamente instalado. Ex: Painel Elétrico, Evaporador.")
                st.text_input("Título da Seção (Onde Usar)", value=app_eq.get("titulo", ""), key=f"app_eq_t_{selected}")
                st.text_area("Introdução (Onde Usar)", value=app_eq.get("intro", ""), height=80, key=f"app_eq_i_{selected}")
                st.markdown("##### Cards de Equipamentos")
                render_dynamic_list("eq", title_label="Nome do Equipamento", desc_label="Descrição")
                   
            with tab_e8:
                st.info("💡 Dica: Dúvidas reais do comprador.")
                render_dynamic_list("faq", title_label="Pergunta", desc_label="Resposta Técnica")
           
            st.markdown("---")


            # SYNC & SAVE
            def _sincronizar_e_salvar_inputs():
                # Resumo
                if f"rt_edit_{selected}" in st.session_state:
                    json_data["resumo_tecnico"] = st.session_state[f"rt_edit_{selected}"]
               
                # Dynamic Lists
                mercados_list = extract_dynamic_list("merc", True)
                json_data["mercados"] = mercados_list
                json_data["mercado"] = "\n".join(mercados_list)
                
                json_data["hero_checklist"] = extract_dynamic_list("chk", True)
                json_data["beneficios"] = extract_dynamic_list("ben", False)
                json_data["diferenciais"] = extract_dynamic_list("dif", True)
               
                app_cat = json_data.get("aplicacoes_categoria", {})
                app_cat["titulo"] = st.session_state.get(f"app_cat_t_{selected}", "").strip()
                app_cat["intro"] = st.session_state.get(f"app_cat_i_{selected}", "").strip()
                app_list = extract_dynamic_list("app", False)
                app_cat["cards"] = app_list
                json_data["aplicacoes_categoria"] = app_cat
                json_data["aplicacoes"] = app_list
               
                app_eq = json_data.get("aplicacoes_equipamento", {})
                app_eq["titulo"] = st.session_state.get(f"app_eq_t_{selected}", "").strip()
                app_eq["intro"] = st.session_state.get(f"app_eq_i_{selected}", "").strip()
                eq_list = extract_dynamic_list("eq", False)
                app_eq["cards"] = eq_list
                json_data["aplicacoes_equipamento"] = app_eq
                json_data["onde_usar"] = eq_list
                json_data["equipamentos"] = eq_list
               
                json_data["faq"] = extract_dynamic_list("faq", False)
               
                # Save
                with open(json_path, "w", encoding="utf-8") as f:
                    import json
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
               
                # Generate ACF
                from gerar_conteudo_acf import gerar_payload_acf, salvar_output
                payload = gerar_payload_acf(json_data)
                salvar_output(payload)

                # ── FIX: Em vez de limpar o cache completo (o que faz o Streamlit re-inicializar
                # as listas dinâmicas com UIDs novos enquanto os widgets antigos ainda existem em
                # memória), atualizamos o edit_data_ com o json_data recém-salvo E limpamos
                # explicitamente os estados dinâmicos das listas para que no próximo render
                # o init_dynamic_list reinicialize a partir dos dados corretos salvos em disco.
                # Isso evita que o session_state dos widgets antigos (com UIDs obsoletos) interfira.
                
                # 1. Atualiza o edit_data_ com os dados salvos corretamente
                st.session_state[f"edit_data_{selected}"] = dict(json_data)
                
                # 2. Limpa apenas os estados das listas dinâmicas (dyn_* e seus widgets uid)
                #    para forçar re-inicialização limpa no próximo render
                for lk in ["merc", "chk", "ben", "dif", "app", "eq", "faq"]:
                    sk = f"dyn_{lk}_{selected}"
                    trash_k = f"trash_{lk}_{selected}"
                    if sk in st.session_state:
                        for item in st.session_state.get(sk, []):
                            uid = item.get("id") if isinstance(item, dict) else None
                            if uid:
                                st.session_state.pop(f"{lk}_val_{uid}", None)
                                st.session_state.pop(f"{lk}_tit_{uid}", None)
                                st.session_state.pop(f"{lk}_desc_{uid}", None)
                        st.session_state.pop(sk, None)
                    st.session_state.pop(trash_k, None)
                
                # 3. Atualiza o mtime para o arquivo recém-salvo (evita double-reload)
                st.session_state[f"mtime_{selected}"] = os.path.getmtime(json_path)


            st.markdown('<div style="background: #111827; border: 1px solid #1F2937; padding: 18px 20px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">', unsafe_allow_html=True)
            st.markdown("#### 🎯 Centro de Ações")

            # ── ESTADO: APROVADO ─────────────────────────────────────────────
            if is_approved:
                st.caption("Este produto já foi aprovado. Você pode atualizar o conteúdo diretamente (mantendo a aprovação) ou Revogar para despublicar.")
                col_save_appr, col_ap, col_rev = st.columns([2, 1, 1])
                
                with col_save_appr:
                    if st.button("🔄 ATUALIZAR CONTEÚDO", type="primary", use_container_width=True,
                                 key=f"top_update_approved_{selected}",
                                 help="Salva as alterações feitas nas abas mantendo o status de aprovado. Se publicado, sincroniza diretamente com o site."):
                        _sincronizar_e_salvar_inputs()
                        db[selected]["updated_by"] = user["nome"]
                        db[selected]["current_assignee"] = user["nome"]
                        save_db(db)
                        
                        # Se já estiver publicado no WooCommerce, atualiza no site em tempo real
                        if db[selected].get("status") == "publicado":
                            with st.spinner("Atualizando landing page no WordPress..."):
                                import subprocess
                                res = subprocess.run(
                                    [sys.executable, os.path.join(GERADOR_DIR, "automacao", "publicar_wordpress.py"), selected, "--skip-validation"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace"
                                )
                            if res.returncode == 0:
                                st.success("✅ Conteúdo atualizado com sucesso no site (aprovação mantida)!")
                                audit.log_action(selected, user["id"], user["nome"], "🔄 Conteúdo atualizado no produto publicado")
                            else:
                                st.warning("⚠️ Dados locais salvos com aprovação mantida, mas houve alerta ao sincronizar com o site.")
                                st.code(res.stdout + "\n" + res.stderr)
                        else:
                            st.success("✅ Conteúdo local atualizado com sucesso (aprovação mantida)!")
                            audit.log_action(selected, user["id"], user["nome"], "✏️ Conteúdo atualizado no produto aprovado")
                        
                        st.session_state.pop(f"edit_data_{selected}", None)
                        st.session_state["_force_refresh"] = True
                        st.session_state["selected_product"] = selected
                        import time; time.sleep(1.2)
                        st.rerun()

                with col_ap:
                    st.button("✅ APROVADO", type="secondary", use_container_width=True,
                              key=f"top_aprov_badge_{selected}", disabled=True,
                              help="Produto homologado.")
                with col_rev:
                    if auth.can_approve(role):
                        if st.button("🔴 REVOGAR", type="secondary", use_container_width=True,
                                     key=f"top_dev_{selected}",
                                     help="Remove o selo de aprovação, retorna o produto para Auditoria e despublica (rascunho) do site."):
                            db[selected]["aprovacao"] = False
                            db[selected]["status"] = "em_revisao"
                            db[selected].pop("approved_by_user_id", None)
                            db[selected].pop("approved_by_name", None)
                            db[selected].pop("approved_at", None)
                            save_db(db)
                            audit.log_action(selected, user["id"], user["nome"], "🔴 Aprovação revogada e produto despublicado")
                           
                            with st.spinner("Despublicando produto do WordPress..."):
                                import subprocess
                                res = subprocess.run(
                                    [sys.executable, os.path.join(GERADOR_DIR, "automacao", "publicar_wordpress.py"), selected, "--draft"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace"
                                )
                               
                            if res.returncode != 0:
                                st.error(f"Erro ao despublicar no WP:\n{res.stdout}\n{res.stderr}")
                            else:
                                st.warning("Aprovação revogada e produto despublicado do site.")
                               
                            # Invalida cache de edição para forçar releitura limpa do DB
                            st.session_state.pop(f"edit_data_{selected}", None)
                            st.session_state["_force_refresh"] = True
                            st.session_state["selected_product"] = selected
                            st.rerun()
                    else:
                        st.button("🚫 Revogar", disabled=True, use_container_width=True,
                                  key=f"top_dev_block_{selected}")

            # ── ESTADO: NÃO APROVADO ─────────────────────────────────────────
            else:
                st.caption("Execute qualquer ação abaixo. As alterações feitas nas abas serão sincronizadas automaticamente.")
                col_btn1, col_btn2, col_btn3 = st.columns(3)

                # BOTÃO 1: SALVAR REVISÃO
                with col_btn1:
                    if st.button("💾 SALVAR REVISÃO", type="secondary", use_container_width=True,
                                 key=f"top_save_{selected}",
                                 help="Salva todas as edições nos arquivos locais (JSON/ACF) mantendo o status atual."):
                        _sincronizar_e_salvar_inputs()
                        db[selected]["updated_by"] = user["nome"]
                        db[selected]["current_assignee"] = user["nome"]
                        save_db(db)
                        audit.log_action(selected, user["id"], user["nome"], "✎ Salvou revisão do produto")
                        st.success("✅ Revisão salva localmente com sucesso!")
                        st.session_state["_force_refresh"] = True
                        st.session_state["selected_product"] = selected
                        import time; time.sleep(1.2)
                        st.rerun()

                # BOTÃO 2: APROVAR
                with col_btn2:
                    if auth.can_approve(role):
                        if st.button("✅ APROVAR", type="primary", use_container_width=True,
                                     key=f"top_aprov_{selected}",
                                     help="Homologa o produto como aprovado tecnicamente."):
                            _sincronizar_e_salvar_inputs()
                            db[selected]["aprovacao"] = True
                            db[selected]["status"] = "aprovado"
                            db[selected]["approved_by_user_id"] = user["id"]
                            db[selected]["approved_by_name"] = user["nome"]
                            db[selected]["approved_at"] = datetime.datetime.now().isoformat()
                            save_db(db)
                            audit.log_action(selected, user["id"], user["nome"], "✓ Produto aprovado")
                            st.success("✅ Produto homologado e aprovado com sucesso!")
                            # Invalida cache de edição para forçar releitura limpa do DB
                            st.session_state.pop(f"edit_data_{selected}", None)
                            st.session_state["_force_refresh"] = True
                            st.session_state["selected_product"] = selected
                            import time; time.sleep(1.2)
                            st.rerun()
                    else:
                        st.button("🚫 Aprovar (Apenas Supervisor)", disabled=True,
                                  use_container_width=True, key=f"top_aprov_block_{selected}")

                # BOTÃO 3: PUBLICAR
                with col_btn3:
                    if auth.can_approve(role):
                        if st.button("🚀 PUBLICAR", type="primary", use_container_width=True,
                                     key=f"top_pub_{selected}",
                                     help="Salva, aprova e publica diretamente no WordPress."):
                            _sincronizar_e_salvar_inputs()
                            db[selected]["aprovacao"] = True
                            db[selected]["status"] = "publicado"
                            if not db[selected].get("approved_by_user_id"):
                                db[selected]["approved_by_user_id"] = user["id"]
                                db[selected]["approved_by_name"] = user["nome"]
                                db[selected]["approved_at"] = datetime.datetime.now().isoformat()
                            save_db(db)
                            audit.log_action(selected, user["id"], user["nome"], "🚀 Produto publicado no site")
                            with st.spinner("Publicando landing page no WordPress..."):
                                import subprocess
                                res = subprocess.run(
                                    [sys.executable, os.path.join(GERADOR_DIR, "automacao", "publicar_wordpress.py"), selected, "--skip-validation"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace"
                                )
                            if res.returncode == 0:
                                st.success("🚀 Landing Page publicada com sucesso no WordPress!")
                                st.balloons()
                                st.session_state.pop(f"edit_data_{selected}", None)
                                st.session_state["_force_refresh"] = True
                                st.session_state["selected_product"] = selected
                                import time; time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("❌ Falha ao publicar no WordPress. Os dados locais foram salvos.")
                                st.code(res.stdout + "\n" + res.stderr)
                    else:
                        st.button("🚫 Publicar", disabled=True, use_container_width=True,
                                  key=f"top_pub_block_{selected}")

                st.markdown("---")
                st.markdown("#### ❌ Reprovar e Devolver para Edição")
                col_motivo, col_rep_btn = st.columns([3, 1])
                with col_motivo:
                    motivo_reprovacao = st.selectbox(
                        "Selecione o motivo da reprovação:",
                        ["Datasheet errado / não corresponde", "Produto com inferências incorretas", "Faltam informações obrigatórias", "Erro de formatação/ortografia", "Outro"],
                        key=f"motivo_{selected}"
                    )
                with col_rep_btn:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("❌ REPROVAR", type="secondary", use_container_width=True, key=f"btn_reprovar_{selected}", help="Devolve o produto para a fila de produção."):
                        db[selected]["status"] = "em_producao"
                        db[selected]["aprovacao"] = False
                        save_db(db)
                        audit.log_action(selected, user["id"], user["nome"], f"❌ Produto reprovado e devolvido: {motivo_reprovacao}")
                        st.warning(f"Produto reprovado pelo motivo: {motivo_reprovacao}")
                        st.session_state.pop(f"edit_data_{selected}", None)
                        st.session_state["_force_refresh"] = True
                        st.session_state["selected_product"] = selected
                        import time; time.sleep(1.2)
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
               
            # Exibe Schema JSON-LD para referência técnica durante auditoria
            acf_path = os.path.join(OUTPUT_DIR, f"{prod['slug']}_acf.json")
            if os.path.exists(acf_path):
                with open(acf_path, "r", encoding="utf-8") as f:
                    acf_data = json.load(f)
                if "schema_jsonld" in acf_data:
                    st.markdown("---")
                    st.markdown("### 🔍 Schema JSON-LD (SEO Integrado)")
                    with st.expander("Ver Schema JSON-LD Gerado"):
                        st.json(acf_data["schema_jsonld"])


        st.stop() # Interrompe a execução para não renderizar as abas do Operador

    # Header
    col_title, col_status = st.columns([4, 1])
    with col_title:
        st.markdown(f'<p class="corporate-title">#{prod.get("pos", 999):02d} — {prod["nome"]}</p>', unsafe_allow_html=True)
    with col_status:
        status_class = f"status-{prod['status']}"
        st.markdown(
            f'<span class="status-badge {status_class}">{get_status_label(prod["status"])}</span>',
            unsafe_allow_html=True
        )
   
    link_prod = f"https://DemoStore.com.br/produto/{prod['slug']}/"
   
    col_v1, col_v2 = st.columns([1, 3])
    with col_v1:
        if st.button("⬅️ Voltar para a lista"):
            st.session_state["selected_product"] = None
            st.rerun()
    with col_v2:
        st.markdown(f'<a href="{link_prod}" target="_blank" style="display: inline-block; padding: 8px 16px; background: #1250B2; color: white; border-radius: 6px; text-decoration: none; font-family: Inter, sans-serif; font-size: 13px; font-weight: 600;">🌐 Abrir no Site</a>', unsafe_allow_html=True)
        json_file_path = os.path.join(DADOS_DIR, f"{prod['slug']}.json")
        if os.path.exists(json_file_path):
            st.markdown(f"📄 **JSON:** `gerador/dados/{prod['slug']}.json` | 📝 **ACF:** `produtos/{prod['slug']}/acf-campos-prontos.md`")

    st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)
   
    # === PREVIEW PARA CONCLUÍDOS ===
    if prod["status"] == "concluido":
        st.markdown("### Preview da Landing Page")
        st.markdown(f"""
        <div class="preview-container">
            <iframe src="{link_prod}" width="100%" height="600" style="border: none;"></iframe>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)
   
    # ============================================================
    # ============================================================
    tab_info, tab_market, tab_lpp, tab_schema = st.tabs([
        "📑 Info & Técnico", 
        "🧠 Mercado & Intel", 
        "🚀 LPP & Workflow",
        "🔍 Schema JSON-LD"
    ])
   
    # ------------------------------------------------------------
    # TAB 1: INFORMAÇÕES E TÉCNICO
    # ------------------------------------------------------------
    with tab_info:
        st.markdown("### Resumo Técnico e Documentação")
        st.markdown("##### Datasheet Oficial")
        pdf_dir = os.path.join(PROJ_DIR, "gerador", "datasheets")
        available_pdfs = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")] if os.path.exists(pdf_dir) else []
       
        saved_pdf = prod.get("datasheet_file", "")
        default_idx = 0
       
        # Exact match only: avoid any automatic incorrect associations
        exact_match = f"{prod['slug']}.pdf"
        if saved_pdf in available_pdfs:
            default_idx = available_pdfs.index(saved_pdf) + 1
        elif exact_match in available_pdfs:
            default_idx = available_pdfs.index(exact_match) + 1
           
        options = ["Nenhum selecionado"] + available_pdfs
        selected_pdf = st.selectbox("Datasheet Associado", options=options, index=default_idx)
       
        if selected_pdf != "Nenhum selecionado":
            st.success(f"✅ Arquivo vinculado: {selected_pdf}")
            db[selected]["tem_datasheet"] = True
            db[selected]["datasheet_file"] = selected_pdf
        else:
            st.warning("⚠️ Selecione um datasheet da pasta para habilitar a geração técnica.")
            db[selected]["tem_datasheet"] = False
            db[selected]["datasheet_file"] = ""
           
        # Salva imediatamente qualquer alteração no dropdown
        if db[selected].get("datasheet_file", "") != saved_pdf:
            save_db(db)
           
        st.markdown("Ou envie um novo Datasheet:")
        uploaded_pdf = st.file_uploader("Fazer Upload de novo Datasheet", type=["pdf"])
        if uploaded_pdf is not None:
            new_pdf_path = os.path.join(pdf_dir, uploaded_pdf.name)
            if not os.path.exists(new_pdf_path):
                with open(new_pdf_path, "wb") as f:
                    f.write(uploaded_pdf.getbuffer())
                st.success(f"Upload concluído: {uploaded_pdf.name}. Recarregue a página para selecionar.")
               
        if st.button("Salvar Info", key="btn_save_info"):
            save_db(db)
            st.toast("Informações salvas!")

    # ------------------------------------------------------------
    # TAB 2: MERCADO & INTELIGÊNCIA
    # ------------------------------------------------------------
    with tab_market:
        st.markdown("### Cadeia de Aplicação e Mercados")
        mercado = st.text_area("Mercado Alvo (Texto extenso p/ SEO, focado no setor)", value=prod.get("mercado", ""), height=100, key=f"mercado_{selected}")
       
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            aplicacoes = st.text_area("Aplicações / Segmentos", value="\n".join(prod.get("aplicacoes", [])) if isinstance(prod.get("aplicacoes"), list) else prod.get("aplicacoes", ""), height=150, key=f"aplic_{selected}")
        with col_m2:
            clientes = st.text_area("Clientes/Parceiros Alvo", value="\n".join(prod.get("clientes_alvo", [])) if isinstance(prod.get("clientes_alvo"), list) else prod.get("clientes_alvo", ""), height=150, key=f"cli_{selected}")
           
        if st.button("Salvar Inteligência", key="btn_save_market"):
            db[selected]["mercado"] = mercado
            # Keep both synced in DB if needed, or just write to aplicacoes
            db[selected]["aplicacoes"] = [s.strip() for s in aplicacoes.split('\\n') if s.strip()]
            db[selected]["segmentos"] = db[selected]["aplicacoes"] 
            db[selected]["clientes_alvo"] = [s.strip() for s in clientes.split('\\n') if s.strip()]
            save_db(db)
            st.toast("Inteligência salva!")



    # ------------------------------------------------------------
    # TAB 4: LPP & WORKFLOW
    # ------------------------------------------------------------
    with tab_lpp:
        st.markdown("### Publicação, ABC e Aprovação")
       
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.markdown("##### Tráfego e Priorização (SEO/Google)")
           
            c_clicks, c_impr = st.columns(2)
            c_clicks.metric("Cliques", prod.get("cliques", 0))
            c_impr.metric("Impressões", prod.get("impressoes", 0))
           
            c_ctr, c_pos = st.columns(2)
            seo_data = prod.get("seo", {})
            c_ctr.metric("CTR (Clique/Impr)", seo_data.get("ctr", "-"))
            c_pos.metric("Posição Média", seo_data.get("posicao_media", "-"))
           
            st.markdown("<br>", unsafe_allow_html=True)
           
            # Converte A, B, C para P1, P2, P3 se vier do script automático
            pri_val = prod.get("prioridade_abc", "P3")
            if pri_val == "A": pri_val = "P1"
            elif pri_val == "B": pri_val = "P2"
            elif pri_val == "C": pri_val = "P3"
           
            idx = 2
            if "P" in pri_val:
                try: idx = int(pri_val.replace("P","")) - 1
                except: pass
               
            prioridade = st.selectbox("Classe de Prioridade (ABC)", ["⭐ P1 - Prioridade máxima (A)", "🟢 P2 - Alta prioridade (B)", "🟡 P3 - Oportunidade (C)", "⚪ P4 - Baixa prioridade"], index=idx)
           
            if st.button("Salvar Prioridade", type="secondary"):
                db[selected]["prioridade_abc"] = prioridade[:2]
                save_db(db)
                st.toast("Prioridade salva!")
               
        with col_w2:
            st.markdown("##### Mudar Status Rápido")
           
            def set_status(s):
                db[selected]["status"] = s
                save_db(db)
                st.rerun()

            col_s1, col_s2, col_s3 = st.columns(3)
            if col_s1.button("🛠️ Produção"):
                set_status("em_producao")
            if col_s2.button("👀 Revisão"):
                set_status("em_revisao")
            if col_s3.button("✅ Aprovado"):
                set_status("aprovado")
       
        st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)
        st.markdown("##### Geração da LPP via Inteligência Artificial")
        st.caption("A IA processa o datasheet PDF e os dados raspados para estruturar a página LPP B2B conforme a Regra de Ferro.")

        if not prod.get("tem_datasheet"):
            st.warning("⚠️ Atenção: Nenhum datasheet PDF associado na aba 'Info & Técnico'. A IA usará apenas os dados brutos da página atual e pode falhar na extração de novas especificações técnicas.")

        col_gen1, col_gen2 = st.columns([1, 1])
        with col_gen1:
            if st.button("⚡ Gerar LPP via Gemini API", type="primary", use_container_width=True):
                with st.spinner("Conectando ao Gemini, enviando PDF e gerando conteúdo técnico..."):
                    import time
                    gen_result = subprocess.run(
                        [sys.executable, os.path.join(GERADOR_DIR, "gerar_lpp_ia.py"), prod["slug"]],
                        capture_output=True, cwd=PROJ_DIR
                    )
                    stdout = gen_result.stdout.decode('utf-8', errors='replace') if gen_result.stdout else ""
                    stderr = gen_result.stderr.decode('utf-8', errors='replace') if gen_result.stderr else ""
                   
                    if gen_result.returncode == 0:
                        st.success("✅ Geração concluída com 100% de sucesso! Produto validado e pronto para revisão.")
                        st.balloons()
                        time.sleep(2)
                        st.session_state["_force_refresh"] = True
                        st.rerun()
                    elif gen_result.returncode == 2:
                        st.warning("⚠️ LPP gerada, mas com inconsistências nas Regras de Ferro:")
                        st.code(stdout)
                        st.session_state["_force_refresh"] = True
                    elif gen_result.returncode == 3:
                        st.error("🔑 **Chave API do Gemini Inválida ou Ausente**")
                        st.markdown("""
                        Para utilizar a geração automática diretamente pelo painel, você precisa configurar uma chave de API válida do Gemini.
                       
                        **Como resolver:**
                        1. Obtenha uma chave gratuita no [Google AI Studio](https://aistudio.google.com/).
                        2. Abra o arquivo `.env` localizado na raiz do projeto (`c:/Users/comercial/Desktop/Projeto landing pages/.env`).
                        3. Altere a linha do Gemini para:
                           `GEMINI_API_KEY=sua_nova_chave_aqui`
                           *(Certifique-se de substituir pela chave real, que sempre começa com **AIzaSy**)*
                        4. Salve o arquivo `.env` e clique no botão novamente!
                        """)
                    else:
                        st.error("❌ Erro catastrófico ao gerar LPP:")
                        st.code(stdout + "\n" + stderr)
                       
        with col_gen2:
            with st.expander("Ver Super-Prompt Clássico (Manual)"):
                prompt = f"""MODELAGEM DE PÁGINA — SELL-PARTS

 Produto: {prod['nome']}
 Código: {prod.get('sku', '[Não utilizado no painel]')}
 Nome comercial: {prod['nome']}
 Categoria: [Não utilizado no painel]
 Linha de produtos: [Não utilizado no painel]

 Página atual:
 https://DemoStore.com.br/produto/{prod['slug']}/

 Datasheet:
 {'Arquivo: ' + prod.get('datasheet_file', prod['slug']+'.pdf') if prod.get('tem_datasheet') else '[Não anexado]'}

 Outros documentos:
 [Nenhum documento extra]

 Clientes que compraram este produto ou esta linha:
 {", ".join(prod.get('clientes_alvo', [])) if prod.get('clientes_alvo') else 'Nenhum cliente específico registrado.'}

 Mercados identificados:
 - {prod.get('mercado', 'Mercado não informado.')}

 Máquinas ou equipamentos onde sei que é utilizado:
 - {", ".join(prod.get('aplicacoes', [])) if prod.get('aplicacoes') else 'Nenhum equipamento registrado.'}

 Concorrentes já conhecidos:
 [Extrair da pesquisa paralela de concorrentes e SEO]

 Evidências Comprovadas (Regra de Diamante):
 [Pesquisar e listar as evidências cruzadas com fonte e confiabilidade (🔴, 🟡, 🟢)]

 Informações que não podem ser publicadas:
 Proibido: "Faturamento", "CNPJ", "Revendas", "Nota Fiscal", "transportadora parceira com rastreamento".

 Faça a pesquisa completa e entregue:
 1. Validação técnica do produto.
 2. Divergências entre datasheet, página e documentos.
 3. Pesquisa de mercado e Google.
 4. Principais concorrentes e códigos.
 5. Comparação técnica.
 6. Clientes, mercados e aplicações.
 7. Máquinas e equipamentos relacionados.
 8. Diferenciais reais.
 9. Limitações de aplicação.
 10. Perguntas e objeções do comprador.
 11. Modelo completo da página em estilo report.
 12. SEO, CTA e estrutura de conversão.
 13. Pendências antes da publicação.

 Regras:
 - Não inventar dados.
 - Não tratar hipótese como fato.
 - Informar a fonte das informações externas.
 - Separar fato confirmado, análise comercial e validação pendente.
 - Não afirmar equivalência sem comparação técnica.
 - Não afirmar que um cliente usa o produto sem comprovação.
 - Priorizar conversão B2B, OEM, manutenção, revendas e aplicações industriais.
 - Manter o padrão das páginas anteriores da Sell-Parts.
 - Seguir quantidades estritas de itens ACF: hero_checklist (3), beneficios (4), diferenciais (4), aplicacoes (4), faq (3).

 Gere tudo em JSON no formato `gerador/dados/{prod['slug']}.json` pronto para ser salvo e lido pelos scripts ACF.
 """
                st.code(prompt, language="markdown")
                st.info("Caso prefira, você pode copiar o prompt e gerar no chat manualmente.")

        st.markdown('<div class="corporate-divider"></div>', unsafe_allow_html=True)

        json_exists = os.path.exists(os.path.join(DADOS_DIR, f"{prod['slug']}.json"))
       
        if not json_exists:
            st.warning(f"O JSON base não existe. Vá para o terminal ou rode o script gerador.")
        else:
            st.success("JSON pronto.")
            if st.button("Publicar no WordPress", type="primary"):
                with st.spinner("Gerando Schemas e Publicando..."):
                    # Passo 1: Converter JSON simples para Payload ACF com Schemas JSON-LD
                    acf_result = subprocess.run(
                        [sys.executable, os.path.join(GERADOR_DIR, "gerar_conteudo_acf.py"), prod["slug"]],
                        capture_output=True, cwd=PROJ_DIR
                    )
                   
                    if acf_result.returncode != 0:
                        st.error("Erro na validação ou geração do ACF/Schemas.")
                        st.code(acf_result.stdout.decode('utf-8', errors='replace'))
                    else:
                        # Passo 2: Publicar
                        result = subprocess.run(
                            [sys.executable, os.path.join(GERADOR_DIR, "automacao", "publicar_wordpress.py"), prod["slug"]],
                            capture_output=True, cwd=PROJ_DIR
                        )
                        stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ""
                        if result.returncode == 0 and "SUCESSO TOTAL" in stdout:
                            st.success("PUBLICADO COM SUCESSO! Schemas e campos ACF atualizados.")
                            db[selected]["status"] = "publicado"
                            save_db(db)
                        else:
                            st.error("Erro na publicação no WordPress.")
                            st.code(stdout)
                           
    # ------------------------------------------------------------
    # TAB 5: SCHEMA JSON-LD
    # ------------------------------------------------------------
    with tab_schema:
        st.markdown("### Schema JSON-LD Gerado")
        st.caption("Esta é a estrutura de SEO técnico (Schema.org) que é injetada na página para o Google.")
        acf_path = os.path.join(OUTPUT_DIR, f"{prod['slug']}_acf.json")
        if os.path.exists(acf_path):
            with open(acf_path, "r", encoding="utf-8") as f:
                acf_data = json.load(f)
            if "schema_jsonld" in acf_data:
                st.json(acf_data["schema_jsonld"])
            else:
                st.warning("⚠️ O schema JSON-LD não foi estruturado nesse ACF JSON.")
        else:
            st.info("ℹ️ Nenhum arquivo ACF JSON gerado ainda. Publique ou gere o conteúdo para visualizar o Schema.")
