
import streamlit as st


# ==========================================
# ESTILO VISUAL
# ==========================================

def aplicar_estilo():

    st.markdown("""
    <style>
    .stApp {
        background: #f5f7fb;
        color: #17243a;
    }

    [data-testid="stSidebar"] {
        background: #102b4e;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    .rastro-header {
        background: linear-gradient(110deg,#102b4e,#174a78);
        padding: 22px 26px;
        border-radius: 13px;
        color: white;
        margin-bottom: 22px;
    }

    .rastro-header h1 {
        color: white;
        margin: 0;
        font-size: 30px;
        letter-spacing: 1px;
    }

    .rastro-header p {
        color: #dce8f5;
        margin: 5px 0 0 0;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e3e9f1;
        padding: 14px 16px;
        border-radius: 11px;
    }

    div.stButton > button {
        border-radius: 8px;
    }

    /* Espaçamento do menu lateral */
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
        gap: 12px;
    }

    /* Opções do menu */
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 9px 10px;
        border-radius: 8px;
        transition: background 0.2s ease;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: #1b4168;
    }

    </style>
    """, unsafe_allow_html=True)


# ==========================================
# CABEÇALHO
# ==========================================

def cabecalho():

    st.markdown("""
    <div class="rastro-header">
      <h1>RASTRO</h1>
      <p>Rastreamento de Ativos, Saldos, Termos e Registros Operacionais</p>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# ATUALIZAR PÁGINA NA URL
# ==========================================

def atualizar_pagina():

    st.query_params["pagina"] = st.session_state.menu_pagina


# ==========================================
# MENU LATERAL
# ==========================================

def menu_lateral():

    st.sidebar.markdown("## RASTRO")
    st.sidebar.caption("NAVEGAÇÃO")

    # Nomes internos utilizados pelo app.py
    paginas = [
        "Consulta",
        "Dashboard",
        "Painel de Pendências",
        "Rastreamento de Movimentações",
        "Demandas de Auditoria",
        "Relatórios",
        "Base de Dados",
        "Histórico",
        "Validações",
        "Configurações"
    ]

    # Nomes e ícones exibidos visualmente
    icones = {
        "Consulta": "🔎 Consulta",
        "Dashboard": "📊 Dashboard",
        "Painel de Pendências": "📌 Painel de Pendências",
        "Rastreamento de Movimentações": "🔄 Movimentações",
        "Demandas de Auditoria": "📋 Demandas de Auditoria",
        "Relatórios": "📑 Relatórios",
        "Base de Dados": "🗄️ Base de Dados",
        "Histórico": "🕒 Histórico",
        "Validações": "✅ Validações",
        "Configurações": "⚙️ Configurações"
    }

    # Recupera a página salva na URL
    pagina_salva = st.query_params.get("pagina", "Consulta")

    # Verifica se a página existe
    if pagina_salva not in paginas:
        pagina_salva = "Consulta"

    # Sincroniza o menu com a página salva na URL
    if (
        "menu_pagina" not in st.session_state
        or st.session_state.menu_pagina != pagina_salva
    ):
        st.session_state.menu_pagina = pagina_salva

    # Exibe o menu
    pagina_selecionada = st.sidebar.radio(
        "Menu",
        paginas,
        format_func=lambda pagina: icones[pagina],
        key="menu_pagina",
        label_visibility="collapsed",
        on_change=atualizar_pagina
    )

    return pagina_selecionada
