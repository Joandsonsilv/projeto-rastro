
import streamlit as st
import pandas as pd

from modules.dados import carregar_pendentes
from modules.exportacao import gerar_excel, resumo_texto


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def _normalizar_texto(serie):
    """
    Padroniza textos para comparação:
    - Remove espaços extras nas extremidades.
    - Converte para maiúsculas.
    - Trata valores vazios.
    """

    return (
        serie.astype("string")
        .str.strip()
        .str.upper()
        .fillna("")
    )


def _opcoes(df, coluna):
    """
    Retorna opções únicas padronizadas para os filtros.
    """

    if coluna not in df.columns:
        return []

    valores = _normalizar_texto(df[coluna])

    return sorted(
        valor
        for valor in valores.unique().tolist()
        if valor
    )


def _garantir_colunas(df, colunas):
    """
    Garante que as colunas utilizadas nos filtros existam.

    Evita erros quando alguma planilha não possui
    determinada coluna.
    """

    resultado = df.copy()

    for coluna in colunas:

        if coluna not in resultado.columns:
            resultado[coluna] = pd.NA

    return resultado


def _limpar_filtros():

    chaves = [
        "consulta_operacao",
        "consulta_carteira",
        "consulta_sistema",
        "consulta_quantidade",
        "consulta_aquisicao",
        "consulta_vencimento",
        "consulta_status",
        "consulta_lastro",
        "consulta_tipo",
        "consulta_indicador",
        "consulta_emitente",
        "consulta_pu_min",
        "consulta_pu_max"
    ]

    for chave in chaves:
        st.session_state.pop(chave, None)


def _formatar_datas(df, colunas):

    exibicao = df.copy()

    for coluna in colunas:

        if coluna in exibicao.columns:

            exibicao[coluna] = pd.to_datetime(
                exibicao[coluna],
                errors="coerce"
            ).dt.strftime("%d/%m/%Y")

    return exibicao


# ==========================================
# FILTRAR OPERAÇÕES CLASSIFICADAS
# ==========================================

def _filtrar_classificados(
    df,
    operacao,
    carteira,
    sistema,
    quantidade,
    aquisicao,
    vencimento,
    status,
    lastro,
    tipo,
    indicador,
    emitente,
    pu_min,
    pu_max
):

    colunas_necessarias = [
        "Operação",
        "Carteira",
        "Sistema",
        "Quantidade",
        "Data de Aquisição",
        "Data de Vencimento",
        "Status",
        "Lastro",
        "Tipo do Ativo",
        "Indicador",
        "Emitente",
        "PU Atual"
    ]

    filtrado = _garantir_colunas(
        df,
        colunas_necessarias
    )

    # Operação

    if operacao.strip():

        filtrado = filtrado[
            filtrado["Operação"].astype("string").str.contains(
                operacao.strip(),
                case=False,
                na=False,
                regex=False
            )
        ]

    # Carteira

    if carteira.strip():

        filtrado = filtrado[
            filtrado["Carteira"].astype("string").str.contains(
                carteira.strip(),
                case=False,
                na=False,
                regex=False
            )
        ]

    # Sistema

    if sistema != "Todos":

        filtrado = filtrado[
            _normalizar_texto(filtrado["Sistema"])
            == sistema.strip().upper()
        ]

    # Quantidade

    if quantidade > 0:

        filtrado = filtrado[
            pd.to_numeric(
                filtrado["Quantidade"],
                errors="coerce"
            ) == quantidade
        ]

    # Data de Aquisição

    if aquisicao:

        filtrado = filtrado[
            pd.to_datetime(
                filtrado["Data de Aquisição"],
                errors="coerce"
            ).dt.date == aquisicao
        ]

    # Data de Vencimento

    if vencimento:

        filtrado = filtrado[
            pd.to_datetime(
                filtrado["Data de Vencimento"],
                errors="coerce"
            ).dt.date == vencimento
        ]

    # Status

    if status:

        status_normalizados = [
            str(valor).strip().upper()
            for valor in status
        ]

        filtrado = filtrado[
            _normalizar_texto(filtrado["Status"]).isin(
                status_normalizados
            )
        ]

    # Lastro

    if lastro.strip():

        filtrado = filtrado[
            filtrado["Lastro"].astype("string").str.contains(
                lastro.strip(),
                case=False,
                na=False,
                regex=False
            )
        ]

    # Tipo do Ativo

    if tipo:

        tipos_normalizados = [
            str(valor).strip().upper()
            for valor in tipo
        ]

        filtrado = filtrado[
            _normalizar_texto(filtrado["Tipo do Ativo"]).isin(
                tipos_normalizados
            )
        ]

    # Indicador

    if indicador:

        indicadores_normalizados = [
            str(valor).strip().upper()
            for valor in indicador
        ]

        filtrado = filtrado[
            _normalizar_texto(filtrado["Indicador"]).isin(
                indicadores_normalizados
            )
        ]

    # Emitente

    if emitente.strip():

        filtrado = filtrado[
            filtrado["Emitente"].astype("string").str.contains(
                emitente.strip(),
                case=False,
                na=False,
                regex=False
            )
        ]

    # PU mínimo

    if pu_min > 0:

        filtrado = filtrado[
            pd.to_numeric(
                filtrado["PU Atual"],
                errors="coerce"
            ) >= pu_min
        ]

    # PU máximo

    if pu_max > 0:

        filtrado = filtrado[
            pd.to_numeric(
                filtrado["PU Atual"],
                errors="coerce"
            ) <= pu_max
        ]

    return filtrado


# ==========================================
# FILTRAR OPERAÇÕES PENDENTES
# ==========================================

def _filtrar_pendentes(
    df,
    operacao,
    carteira,
    sistema,
    quantidade,
    vencimento
):

    colunas_necessarias = [
        "OPERAÇÃO",
        "CARTEIRA",
        "QUANTIDADE",
        "DATA_VENCIMENTO",
        "Sistema"
    ]

    filtrado = _garantir_colunas(
        df,
        colunas_necessarias
    )

    # Operação

    if operacao.strip():

        filtrado = filtrado[
            filtrado["OPERAÇÃO"].astype("string").str.contains(
                operacao.strip(),
                case=False,
                na=False,
                regex=False
            )
        ]

    # Carteira

    if carteira.strip():

        filtrado = filtrado[
            filtrado["CARTEIRA"].astype("string").str.contains(
                carteira.strip(),
                case=False,
                na=False,
                regex=False
            )
        ]

    # Sistema

    if sistema != "Todos":

        filtrado = filtrado[
            _normalizar_texto(filtrado["Sistema"])
            == sistema.strip().upper()
        ]

    # Quantidade

    if quantidade > 0:

        filtrado = filtrado[
            pd.to_numeric(
                filtrado["QUANTIDADE"],
                errors="coerce"
            ) == quantidade
        ]

    # A base PENDENTES não possui DATA_AQUISIÇÃO.
    # Portanto, não aplicamos o filtro de aquisição aqui.

    # Data de Vencimento

    if vencimento:

        filtrado = filtrado[
            pd.to_datetime(
                filtrado["DATA_VENCIMENTO"],
                errors="coerce"
            ).dt.date == vencimento
        ]

    return filtrado


# ==========================================
# TELA DE CONSULTA
# ==========================================

def tela_consulta(df):

    st.title("Consulta de operações")

    st.caption(
        "Pesquise operações nas bases classificadas e nas pendências LZ e XZ."
    )

    # ======================================
    # CARREGAR PENDÊNCIAS
    # ======================================

    df_pendentes, avisos = carregar_pendentes()

    for aviso in avisos:
        st.warning(aviso)

    # ======================================
    # FILTROS
    # ======================================

    with st.container(border=True):

        c1, c2, c3 = st.columns(3)

        operacao = c1.text_input(
            "Operação",
            placeholder="Ex.: LZ1234567",
            key="consulta_operacao"
        )

        carteira = c2.text_input(
            "Carteira",
            placeholder="Digite parte do nome",
            key="consulta_carteira"
        )

        sistema = c3.selectbox(
            "Sistema",
            ["Todos", "LZ", "XZ"],
            key="consulta_sistema"
        )

        c4, c5, c6 = st.columns(3)

        quantidade = c4.number_input(
            "Quantidade",
            min_value=0,
            step=1,
            value=0,
            help="Use 0 para não aplicar este filtro.",
            key="consulta_quantidade"
        )

        aquisicao = c5.date_input(
            "Data de Aquisição",
            value=None,
            key="consulta_aquisicao"
        )

        vencimento = c6.date_input(
            "Data de Vencimento",
            value=None,
            key="consulta_vencimento"
        )

        with st.expander("Mais filtros"):

            a, b, c = st.columns(3)

            status = a.multiselect(
                "Status",
                _opcoes(df, "Status"),
                key="consulta_status"
            )

            lastro = b.text_input(
                "Lastro",
                key="consulta_lastro"
            )

            tipo = c.multiselect(
                "Tipo do Ativo",
                _opcoes(df, "Tipo do Ativo"),
                key="consulta_tipo"
            )

            d, e, f = st.columns(3)

            indicador = d.multiselect(
                "Indicador",
                _opcoes(df, "Indicador"),
                key="consulta_indicador"
            )

            emitente = e.text_input(
                "Emitente",
                key="consulta_emitente"
            )

            pu_min = f.number_input(
                "PU Atual mínimo",
                min_value=0.0,
                value=0.0,
                step=100.0,
                key="consulta_pu_min"
            )

            pu_max = st.number_input(
                "PU Atual máximo (0 = sem limite)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                key="consulta_pu_max"
            )

        b1, b2 = st.columns([1, 5])

        pesquisar = b1.button(
            "Pesquisar",
            type="primary",
            use_container_width=True
        )

        b2.button(
            "Limpar filtros",
            use_container_width=True,
            on_click=_limpar_filtros
        )

    # ======================================
    # EXECUTAR PESQUISA
    # ======================================

    filtrado = _filtrar_classificados(
        df,
        operacao,
        carteira,
        sistema,
        quantidade,
        aquisicao,
        vencimento,
        status,
        lastro,
        tipo,
        indicador,
        emitente,
        pu_min,
        pu_max
    )

    # A data de aquisição é aplicada somente
    # às operações classificadas.

    pendentes_filtrados = _filtrar_pendentes(
        df_pendentes,
        operacao,
        carteira,
        sistema,
        quantidade,
        vencimento
    )

    if pesquisar:
        st.toast("Pesquisa atualizada.", icon="🔎")

    # ======================================
    # RESUMO DA PESQUISA
    # ======================================

    total_classificados = len(filtrado)
    total_pendentes = len(pendentes_filtrados)
    total_encontrado = total_classificados + total_pendentes

    st.divider()

    st.subheader("Resultado da pesquisa")

    st.write(
        f"**{total_encontrado}** registro(s) encontrado(s) no total."
    )

    k1, k2, k3 = st.columns(3)

    k1.metric(
        "Classificadas",
        total_classificados
    )

    k2.metric(
        "Pendentes",
        total_pendentes
    )

    k3.metric(
        "Total encontrado",
        total_encontrado
    )

    # ======================================
    # OPERAÇÕES CLASSIFICADAS
    # ======================================

    st.divider()

    st.subheader("1. Operações classificadas")

    st.caption(
        "Operações localizadas nas abas BASE dos sistemas LZ e XZ."
    )

    if filtrado.empty:

        st.info("Nenhuma operação classificada encontrada.")

    else:

        st.success(
            f"{len(filtrado)} operação(ões) classificada(s) localizada(s)."
        )

        exibicao = _formatar_datas(
            filtrado,
            ["Data de Aquisição", "Data de Vencimento"]
        )

        st.dataframe(
            exibicao,
            use_container_width=True,
            hide_index=True
        )

        x1, x2 = st.columns(2)

        x1.download_button(
            "📥 Gerar Excel - Classificadas",
            data=gerar_excel(filtrado),
            file_name="rastro_operacoes_classificadas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        resumo = resumo_texto(filtrado)

        x2.text_area(
            "Resumo para copiar",
            value=resumo,
            height=100,
            help="Selecione o texto e copie."
        )

        # ==================================
        # DETALHAMENTO
        # ==================================

        st.subheader("Detalhamento da operação")

        escolha = st.selectbox(
            "Selecione uma operação para ver os detalhes",
            filtrado.index.tolist(),
            format_func=lambda i: (
                f'{filtrado.loc[i, "Operação"]} | '
                f'{filtrado.loc[i, "Carteira"]} | '
                f'{filtrado.loc[i, "Sistema"]}'
            )
        )

        registro = filtrado.loc[escolha]

        tab1, tab2, tab3, tab4 = st.tabs([
            "Detalhes da Operação",
            "Dados da Carta",
            "Histórico na Carteira",
            "Observações"
        ])

        with tab1:

            detalhes = registro.to_frame("Valor")

            st.dataframe(
                detalhes,
                use_container_width=True
            )

        with tab2:

            st.info(
                "Sem dados de cartas na base original. "
                "Área reservada para integração futura."
            )

        with tab3:

            st.info(
                "A planilha atual não contém histórico "
                "de movimentações por carteira."
            )

        with tab4:

            st.info(
                "Nenhuma observação operacional foi fornecida "
                "para esta operação."
            )

    # ======================================
    # OPERAÇÕES PENDENTES
    # ======================================

    st.divider()

    st.subheader("2. Operações pendentes")

    st.caption(
        "Operações encontradas na aba PENDENTES."
    )

    if pendentes_filtrados.empty:

        st.info("Nenhuma operação pendente encontrada.")

    else:

        st.warning(
            f"{len(pendentes_filtrados)} operação(ões) pendente(s) localizada(s)."
        )

        exibicao_pendentes = _formatar_datas(
            pendentes_filtrados,
            ["DATA_AQUISIÇÃO", "DATA_VENCIMENTO"]
        )

        st.dataframe(
            exibicao_pendentes,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "📥 Gerar Excel - Pendentes",
            data=gerar_excel(pendentes_filtrados),
            file_name="rastro_operacoes_pendentes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
