
from datetime import date

import pandas as pd
import streamlit as st
import plotly.express as px

from modules.dados import carregar_vcra
from modules.rastreamento import identificar_movimentacoes
from modules.exportacao import gerar_excel


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def normalizar_status(valor):

    if pd.isna(valor):
        return ""

    return (
        str(valor)
        .strip()
        .upper()
        .replace("Í", "I")
        .replace("Ú", "U")
    )


def formatar_numero(valor):

    return f"{valor:,.0f}".replace(",", ".")


def obter_movimentacoes_vcra():

    df_vcra, avisos = carregar_vcra()

    if df_vcra.empty:
        return pd.DataFrame(), avisos

    datas = sorted(
        df_vcra["Data de Posição"]
        .dropna()
        .dt.date
        .unique()
    )

    if len(datas) < 2:
        return pd.DataFrame(), avisos

    resultados = []

    for indice in range(1, len(datas)):

        data_anterior = datas[indice - 1]
        data_atual = datas[indice]

        posicao_anterior = df_vcra[
            df_vcra["Data de Posição"].dt.date == data_anterior
        ].copy()

        posicao_atual = df_vcra[
            df_vcra["Data de Posição"].dt.date == data_atual
        ].copy()

        comparacao = identificar_movimentacoes(
            posicao_anterior,
            posicao_atual
        )

        if comparacao.empty:
            continue

        # Não contabilizar registros sem alteração
        comparacao = comparacao[
            comparacao["Movimentação"] != "Sem alteração"
        ].copy()

        if comparacao.empty:
            continue

        comparacao["Data da identificação"] = pd.Timestamp(
            data_atual
        )

        resultados.append(comparacao)

    if not resultados:
        return pd.DataFrame(), avisos

    return pd.concat(
        resultados,
        ignore_index=True
    ), avisos


def filtrar_movimentacoes(
    movimentacoes,
    carteira,
    sistema,
    tipo_ativo
):

    if movimentacoes.empty:
        return movimentacoes.copy()

    base = movimentacoes.copy()

    if carteira != "Todas":

        base = base[
            (base["Carteira de origem"] == carteira)
            | (base["Carteira de destino"] == carteira)
        ]

    if sistema != "Todos":

        base = base[
            (base["Sistema de origem"] == sistema)
            | (base["Sistema de destino"] == sistema)
        ]

    if tipo_ativo != "Todos":

        base = base[
            base["Tipo do Ativo"] == tipo_ativo
        ]

    return base


# ==========================================
# DASHBOARD
# ==========================================

def tela_dashboard(df, df_auditorias=None):

    st.title("Dashboard")

    st.caption(
        "Visão gerencial das operações, auditorias "
        "e movimentações identificadas pelo RASTRO."
    )

    if df_auditorias is None:
        df_auditorias = pd.DataFrame()

    base_original = df.copy()

    # ======================================
    # PREPARAR BASE DE OPERAÇÕES
    # ======================================

    base_original["Quantidade"] = pd.to_numeric(
        base_original["Quantidade"],
        errors="coerce"
    ).fillna(0)

    base_original["Data de Vencimento"] = pd.to_datetime(
        base_original["Data de Vencimento"],
        errors="coerce"
    )

    # ======================================
    # FILTROS GERAIS
    # ======================================

    st.subheader("Filtros do Dashboard")

    carteiras = sorted(
        base_original["Carteira"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    sistemas = sorted(
        base_original["Sistema"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    tipos = sorted(
        base_original["Tipo do Ativo"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    status_lista = sorted(
        base_original["Status"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        carteira = st.selectbox(
            "Carteira",
            ["Todas"] + carteiras,
            key="dashboard_carteira"
        )

    with f2:
        sistema = st.selectbox(
            "Sistema",
            ["Todos"] + sistemas,
            key="dashboard_sistema"
        )

    with f3:
        tipo_ativo = st.selectbox(
            "Tipo do ativo",
            ["Todos"] + tipos,
            key="dashboard_tipo"
        )

    with f4:
        status_operacao = st.selectbox(
            "Status da operação",
            ["Todos"] + status_lista,
            key="dashboard_status"
        )

    # ======================================
    # APLICAR FILTROS NAS OPERAÇÕES
    # ======================================

    base = base_original.copy()

    if carteira != "Todas":
        base = base[
            base["Carteira"].astype(str) == carteira
        ]

    if sistema != "Todos":
        base = base[
            base["Sistema"].astype(str) == sistema
        ]

    if tipo_ativo != "Todos":
        base = base[
            base["Tipo do Ativo"].astype(str) == tipo_ativo
        ]

    if status_operacao != "Todos":
        base = base[
            base["Status"].astype(str) == status_operacao
        ]

    st.divider()

    # ======================================
    # INDICADORES DAS OPERAÇÕES
    # ======================================

    st.subheader("Visão geral das operações")

    hoje = pd.Timestamp(date.today())

    vencidas = base[
        base["Data de Vencimento"] < hoje
    ]

    proximos_30 = base[
        base["Data de Vencimento"].between(
            hoje,
            hoje + pd.Timedelta(days=30)
        )
    ]

    total_operacoes = base["Operação"].nunique()

    quantidade_total = base["Quantidade"].sum()

    total_carteiras = base["Carteira"].nunique()

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Operações",
        formatar_numero(total_operacoes)
    )

    c2.metric(
        "Quantidade total",
        formatar_numero(quantidade_total)
    )

    c3.metric(
        "Carteiras",
        formatar_numero(total_carteiras)
    )

    c4.metric(
        "Vencidas",
        formatar_numero(len(vencidas))
    )

    c5.metric(
        "Vencimento em 30 dias",
        formatar_numero(len(proximos_30))
    )

    # ======================================
    # GRÁFICOS DAS OPERAÇÕES
    # ======================================

    st.divider()

    st.subheader("Análise das operações")

    col1, col2 = st.columns(2)

    with col1:

        if not base.empty:

            por_sistema = (
                base["Sistema"]
                .value_counts()
                .rename_axis("Sistema")
                .reset_index(name="Operações")
            )

            fig = px.pie(
                por_sistema,
                names="Sistema",
                values="Operações",
                title="Distribuição por sistema",
                hole=0.5
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:
            st.info("Não existem operações neste filtro.")

    with col2:

        if not base.empty:

            por_tipo = (
                base["Tipo do Ativo"]
                .value_counts()
                .rename_axis("Tipo")
                .reset_index(name="Operações")
            )

            fig = px.bar(
                por_tipo,
                x="Tipo",
                y="Operações",
                title="Operações por tipo de ativo",
                text="Operações"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:
            st.info("Não existem operações neste filtro.")

    col3, col4 = st.columns(2)

    with col3:

        if not base.empty:

            por_status = (
                base["Status"]
                .fillna("Não informado")
                .value_counts()
                .rename_axis("Status")
                .reset_index(name="Operações")
            )

            fig = px.pie(
                por_status,
                names="Status",
                values="Operações",
                title="Operações por status",
                hole=0.5
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:
            st.info("Não existem operações neste filtro.")

    with col4:

        if not base.empty:

            por_carteira = (
                base["Carteira"]
                .value_counts()
                .head(10)
                .rename_axis("Carteira")
                .reset_index(name="Operações")
            )

            fig = px.bar(
                por_carteira,
                x="Operações",
                y="Carteira",
                orientation="h",
                title="10 maiores carteiras"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:
            st.info("Não existem operações neste filtro.")

    # ======================================
    # AUDITORIAS
    # ======================================

    st.divider()

    st.subheader("Acompanhamento de auditorias")

    auditorias = df_auditorias.copy()

    if not auditorias.empty:

        auditorias["STATUS_NORMALIZADO"] = (
            auditorias["STATUS"]
            .apply(normalizar_status)
        )

        if carteira != "Todas":
            auditorias = auditorias[
                auditorias["CARTEIRA"].astype(str) == carteira
            ]

        total_auditorias = len(auditorias)

        pendentes = int(
            (
                auditorias["STATUS_NORMALIZADO"] == "PENDENTE"
            ).sum()
        )

        em_andamento = int(
            (
                auditorias["STATUS_NORMALIZADO"] == "EM ANDAMENTO"
            ).sum()
        )

        concluidas = int(
            auditorias["STATUS_NORMALIZADO"].isin([
                "CONCLUIDA"
            ]).sum()
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total de auditorias",
            total_auditorias
        )

        c2.metric(
            "Pendentes",
            pendentes
        )

        c3.metric(
            "Em andamento",
            em_andamento
        )

        c4.metric(
            "Concluídas",
            concluidas
        )

        status_auditorias = (
            auditorias["STATUS_NORMALIZADO"]
            .replace("", "NÃO INFORMADO")
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Auditorias")
        )

        if not status_auditorias.empty:

            fig = px.pie(
                status_auditorias,
                names="Status",
                values="Auditorias",
                title="Distribuição das auditorias",
                hole=0.5
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.caption(
            "As auditorias são filtradas pela carteira selecionada. "
            "Os filtros de sistema, tipo de ativo e status da operação "
            "não se aplicam à base de auditorias."
        )

    else:

        st.info(
            "Não foi possível carregar auditorias "
            "ou ainda não existem registros."
        )

    # ======================================
    # MOVIMENTAÇÕES
    # ======================================

    st.divider()

    st.subheader("Acompanhamento de movimentações")

    movimentacoes, avisos = obter_movimentacoes_vcra()

    for aviso in avisos:
        st.warning(aviso)

    if movimentacoes.empty:

        st.info(
            "Não existem movimentações identificadas "
            "entre as posições disponíveis no VCRA."
        )

    else:

        movimentacoes_filtradas = filtrar_movimentacoes(
            movimentacoes,
            carteira,
            sistema,
            tipo_ativo
        )

        # ----------------------------------
        # SELEÇÃO DO MÊS
        # ----------------------------------

        movimentacoes_filtradas["Mes"] = (
            movimentacoes_filtradas["Data da identificação"]
            .dt.to_period("M")
        )

        meses = sorted(
            movimentacoes_filtradas["Mes"]
            .dropna()
            .unique()
            .tolist()
        )

        if meses:

            opcoes_meses = {
                str(mes): mes
                for mes in meses
            }

            mes_selecionado = st.selectbox(
                "Mês de referência das movimentações",
                options=list(opcoes_meses.keys()),
                index=len(meses) - 1,
                format_func=lambda valor: (
                    opcoes_meses[valor]
                    .strftime("%m/%Y")
                ),
                key="dashboard_mes_movimentacao"
            )

            mes_escolhido = opcoes_meses[mes_selecionado]

            movimentos_mes = movimentacoes_filtradas[
                movimentacoes_filtradas["Mes"] == mes_escolhido
            ].copy()

            total_mes = len(movimentos_mes)

            transferencias = movimentos_mes[
                movimentos_mes["Movimentação"].str.contains(
                    "transferência",
                    case=False,
                    na=False
                )
            ]

            reducoes = movimentos_mes[
                movimentos_mes["Movimentação"].isin([
                    "Redução de quantidade",
                    "Possível saída/baixa"
                ])
            ]

            aumentos = movimentos_mes[
                movimentos_mes["Movimentação"].isin([
                    "Aumento de quantidade",
                    "Nova entrada sem origem identificada"
                ])
            ]

            conferencias = movimentos_mes[
                movimentos_mes["Movimentação"] == "Necessita conferência"
            ]

            st.markdown(
                f"**Resumo de {mes_escolhido.strftime('%m/%Y')}**"
            )

            c1, c2, c3, c4, c5 = st.columns(5)

            c1.metric(
                "Movimentações",
                total_mes
            )

            c2.metric(
                "Transferências",
                len(transferencias)
            )

            c3.metric(
                "Reduções / saídas",
                len(reducoes)
            )

            c4.metric(
                "Aumentos / entradas",
                len(aumentos)
            )

            c5.metric(
                "Necessita conferência",
                len(conferencias)
            )

            # ----------------------------------
            # GRÁFICOS DE MOVIMENTAÇÕES
            # ----------------------------------

            col1, col2 = st.columns(2)

            with col1:

                por_movimentacao = (
                    movimentacoes_filtradas

                    .groupby("Mes")
                    .size()
                    .reset_index(name="Movimentações")
                )

                por_movimentacao["Mês"] = (
                    por_movimentacao["Mes"]
                    .astype(str)
                )

                fig = px.line(
                    por_movimentacao,
                    x="Mês",
                    y="Movimentações",
                    markers=True,
                    title="Evolução mensal das movimentações"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            with col2:

                if not movimentos_mes.empty:

                    por_categoria = (
                        movimentos_mes["Movimentação"]
                        .value_counts()
                        .rename_axis("Movimentação")
                        .reset_index(name="Quantidade")
                    )

                    fig = px.bar(
                        por_categoria,
                        x="Movimentação",
                        y="Quantidade",
                        title="Movimentações por classificação",
                        text="Quantidade"
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                else:
                    st.info(
                        "Nenhuma movimentação encontrada neste mês."
                    )

            # ----------------------------------
            # TABELA DE MOVIMENTAÇÕES
            # ----------------------------------

            with st.expander(
                "Consultar registros de movimentação"
            ):

                st.dataframe(
                    movimentos_mes.drop(
                        columns=["Mes"],
                        errors="ignore"
                    ),
                    use_container_width=True,
                    hide_index=True
                )

        else:

            st.info(
                "Não existem movimentações para os filtros selecionados."
            )

        st.caption(
            "A contagem considera os registros gerados pela comparação "
            "entre posições consecutivas do VCRA. Uma transferência "
            "dividida em vários destinos pode gerar mais de um registro."
        )


# ==========================================
# PAINEL DE PENDÊNCIAS
# ==========================================

def tela_pendencias(df):

    st.title("Painel de Pendências")

    hoje = pd.Timestamp(date.today())

    base = df.copy()

    base["Data de Vencimento"] = pd.to_datetime(
        base["Data de Vencimento"],
        errors="coerce"
    )

    base["Dias até o vencimento"] = (
        base["Data de Vencimento"] - hoje
    ).dt.days

    prazo = st.selectbox(
        "Período",
        [
            "Vencidas",
            "Próximos 30 dias",
            "Próximos 60 dias",
            "Próximos 90 dias",
            "Todas"
        ]
    )

    carteira = st.selectbox(
        "Carteira",
        ["Todas"] + sorted(
            base["Carteira"].dropna().unique().tolist()
        )
    )

    sistema = st.selectbox(
        "Sistema",
        ["Todos", "LZ", "XZ"]
    )

    if prazo == "Vencidas":

        base = base[
            base["Dias até o vencimento"] < 0
        ]

    elif prazo != "Todas":

        dias = int(prazo.split()[1])

        base = base[
            base["Dias até o vencimento"].between(0, dias)
        ]

    if carteira != "Todas":

        base = base[
            base["Carteira"] == carteira
        ]

    if sistema != "Todos":

        base = base[
            base["Sistema"] == sistema
        ]

    base = base.sort_values(
        "Dias até o vencimento"
    )

    st.metric(
        "Operações no recorte",
        len(base)
    )

    st.dataframe(
        base[
            [
                "Operação",
                "Carteira",
                "Quantidade",
                "Sistema",
                "Tipo do Ativo",
                "Data de Vencimento",
                "Dias até o vencimento",
                "Status"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Exportar pendências",
        gerar_excel(base),
        "rastro_pendencias.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ==========================================
# BASE DE DADOS
# ==========================================

def tela_base_dados(df):

    st.title("Base de Dados")

    sistema = st.selectbox(
        "Visualizar base",
        ["Ambas", "LZ", "XZ"]
    )

    base = (
        df
        if sistema == "Ambas"
        else df[df["Sistema"] == sistema]
    )

    a, b, c = st.columns(3)

    a.metric("Registros", len(base))
    b.metric("Carteiras", base["Carteira"].nunique())
    c.metric("Operações", base["Operação"].nunique())

    st.dataframe(
        base,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Exportar base exibida",
        gerar_excel(base),
        f"rastro_base_{sistema.lower()}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.caption(
        "A aplicação lê os arquivos originais sem alterá-los."
    )
