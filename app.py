
import streamlit as st

from modules.dados import carregar_bases, carregar_auditorias
from modules.componentes import (
    aplicar_estilo,
    cabecalho,
    menu_lateral
)
from modules.filtros import tela_consulta
from modules.indicadores import (
    tela_dashboard,
    tela_pendencias,
    tela_base_dados
)
from modules.validacoes import tela_validacoes
from modules.auditorias import tela_auditorias
from modules.rastreamento import tela_rastreamento


st.set_page_config(
    page_title="RASTRO",
    page_icon="🔎",
    layout="wide"
)

aplicar_estilo()

df, avisos = carregar_bases()

for aviso in avisos:
    st.warning(aviso)

cabecalho()
pagina = menu_lateral()


# ==========================================
# DEMANDAS DE AUDITORIA
# ==========================================

if pagina == "Demandas de Auditoria":

    df_auditorias, avisos_auditorias = carregar_auditorias()

    for aviso in avisos_auditorias:
        st.warning(aviso)

    tela_auditorias(df_auditorias)
    st.stop()


# ==========================================
# RASTREAMENTO DE MOVIMENTAÇÕES
# ==========================================

if pagina == "Rastreamento de Movimentações":

    tela_rastreamento()
    st.stop()


# ==========================================
# VERIFICAR BASES PRINCIPAIS
# ==========================================

if df.empty:

    st.error(
        "Nenhuma base foi carregada. "
        "Verifique os arquivos da pasta data."
    )

    st.stop()


# ==========================================
# DEMAIS TELAS
# ==========================================

if pagina == "Consulta":

    tela_consulta(df)

elif pagina == "Dashboard":

    tela_dashboard(df)

elif pagina == "Painel de Pendências":

    tela_pendencias(df)

elif pagina == "Base de Dados":

    tela_base_dados(df)

elif pagina == "Validações":

    tela_validacoes(df)

elif pagina in [
    "Relatórios",
    "Histórico",
    "Configurações"
]:

    st.title(pagina)
    st.info("Esta área está reservada para uma próxima etapa.")
