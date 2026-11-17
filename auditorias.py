
from datetime import date, datetime

import pandas as pd
import streamlit as st

from modules.dados import (
    DATA_DIR,
    COLUNAS_AUDITORIAS,
    carregar_operacoes_auditoria
)
from modules.exportacao import gerar_excel


# ==========================================
# SALVAR AUDITORIAS
# ==========================================

def salvar_auditorias(base):

    caminho = DATA_DIR / "Base_Auditorias.xlsx"

    base = base[COLUNAS_AUDITORIAS]

    base.to_excel(
        caminho,
        index=False,
        engine="openpyxl"
    )


# ==========================================
# HISTÓRICO DE ALTERAÇÕES DE STATUS
# ==========================================

COLUNAS_HISTORICO = [
    "ID_AUDITORIA",
    "DATA_HORA",
    "STATUS_ANTERIOR",
    "NOVO_STATUS",
    "RESPONSAVEL_ALTERACAO"
]


def garantir_base_historico():
    """
    Garante que a planilha de histórico exista.
    Se não existir, cria automaticamente.
    Se já existir, preserva os registros.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho = DATA_DIR / "Base_Historico_Auditorias.xlsx"

    if not caminho.exists():

        historico = pd.DataFrame(
            columns=COLUNAS_HISTORICO
        )

        historico.to_excel(
            caminho,
            index=False,
            engine="openpyxl"
        )


def registrar_historico_status(
    id_auditoria,
    status_anterior,
    novo_status,
    responsavel_alteracao
):
    """Registra uma alteração na planilha de histórico."""

    caminho = DATA_DIR / "Base_Historico_Auditorias.xlsx"

    if caminho.exists():

        historico = pd.read_excel(
            caminho,
            engine="openpyxl"
        )

        historico = historico.reindex(
            columns=COLUNAS_HISTORICO
        )

    else:

        historico = pd.DataFrame(
            columns=COLUNAS_HISTORICO
        )

    novo_registro = pd.DataFrame([{
        "ID_AUDITORIA": id_auditoria,
        "DATA_HORA": datetime.now(),
        "STATUS_ANTERIOR": status_anterior,
        "NOVO_STATUS": novo_status,
        "RESPONSAVEL_ALTERACAO": (
            responsavel_alteracao.strip()
            if responsavel_alteracao and responsavel_alteracao.strip()
            else "Não informado"
        )
    }])

    historico = pd.concat(
        [historico, novo_registro],
        ignore_index=True
    )

    historico.to_excel(
        caminho,
        index=False,
        engine="openpyxl"
    )


def normalizar_status(status):

    status = str(status).strip().upper()

    return (
        "CONCLUÍDA"
        if status == "CONCLUIDA"
        else status
    )


# ==========================================
# INDICADORES
# ==========================================

def exibir_indicadores(base):

    if base.empty:

        total = em_aberto = alta_urgencia = atrasadas = 0

    else:

        status_normalizado = (
            base["STATUS"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        concluidas = status_normalizado.isin([
            "CONCLUÍDA",
            "CONCLUIDA"
        ])

        hoje = pd.Timestamp(date.today())

        prazos = pd.to_datetime(
            base["PRAZO"],
            errors="coerce"
        )

        urgencias = pd.to_numeric(
            base["URGÊNCIA"],
            errors="coerce"
        )

        total = len(base)

        em_aberto = int(
            (~concluidas).sum()
        )

        alta_urgencia = int(
            (urgencias == 3).sum()
        )

        atrasadas = int(
            (
                ~concluidas
                & prazos.notna()
                & (prazos < hoje)
            ).sum()
        )

    st.markdown(
        """
        <style>
        div[data-testid="stMetric"] {
            background: linear-gradient(
                145deg,
                #102A43,
                #173F5F
            );
            border: 1px solid #285477;
            border-left: 5px solid #3498DB;
            padding: 18px;
            border-radius: 10px;
            min-height: 110px;
        }

        div[data-testid="stMetric"] label {
            color: #D6E5F2 !important;
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-size: 30px;
            font-weight: 700;
        }

        div[data-testid="stMetric"]:nth-child(3) {
            border-left-color: #F39C12;
        }

        div[data-testid="stMetric"]:nth-child(4) {
            border-left-color: #E74C3C;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("TOTAL DE AUDITORIAS", total)
    c2.metric("EM ABERTO", em_aberto)
    c3.metric("ALTA URGÊNCIA", alta_urgencia)
    c4.metric("ATRASADAS", atrasadas)


# ==========================================
# FORMATAÇÃO DAS AUDITORIAS
# ==========================================

def formatar_auditoria(id_auditoria, base):

    carteira = base.loc[
        base["ID"] == id_auditoria,
        "CARTEIRA"
    ].iloc[0]

    return f"ID {id_auditoria} - {carteira}"


# ==========================================
# OPERAÇÕES VINCULADAS ÀS AUDITORIAS
# ==========================================

def exibir_operacoes_auditoria(df):

    st.divider()

    st.subheader("Operações da Auditoria")

    if df.empty:

        st.info(
            "Cadastre uma auditoria para consultar suas operações."
        )

        return

    operacoes, avisos = carregar_operacoes_auditoria()

    for aviso in avisos:
        st.warning(aviso)

    auditorias_validas = df.copy()

    auditorias_validas["ID"] = pd.to_numeric(
        auditorias_validas["ID"],
        errors="coerce"
    )

    auditorias_validas = auditorias_validas.dropna(
        subset=["ID"]
    )

    auditorias_validas["ID"] = (
        auditorias_validas["ID"].astype(int)
    )

    if auditorias_validas.empty:

        st.info("Não existem auditorias com ID válido.")

        return

    ids = sorted(
        auditorias_validas["ID"].unique().tolist()
    )

    id_selecionado = st.selectbox(
        "Selecione a auditoria para consultar as operações",
        ids,
        format_func=lambda x: formatar_auditoria(
            x,
            auditorias_validas
        ),
        key="selecao_operacoes_auditoria"
    )

    if operacoes.empty:

        st.info(
            "Ainda não existem operações cadastradas na base."
        )

        return

    operacoes["ID_AUDITORIA"] = pd.to_numeric(
        operacoes["ID_AUDITORIA"],
        errors="coerce"
    )

    operacoes_da_auditoria = operacoes[
        operacoes["ID_AUDITORIA"] == id_selecionado
    ].copy()

    st.divider()

    c1, c2 = st.columns(2)

    c1.metric(
        "OPERAÇÕES VINCULADAS",
        len(operacoes_da_auditoria)
    )

    c2.metric(
        "AUDITORIA SELECIONADA",
        f"ID {id_selecionado}"
    )

    if operacoes_da_auditoria.empty:

        st.info(
            "Nenhuma operação vinculada a esta auditoria ainda."
        )

        st.caption(
            "Para adicionar operações, abra "
            "Base_Operacoes_Auditoria.xlsx na pasta data."
        )

        return

    st.dataframe(
        operacoes_da_auditoria,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "As operações são carregadas diretamente da "
        "Base_Operacoes_Auditoria.xlsx."
    )


# ==========================================
# TELA DE DEMANDAS DE AUDITORIA
# ==========================================

def tela_auditorias(df):

    # Garante a existência da planilha de histórico.
    garantir_base_historico()

    st.title("Demandas de Auditoria")

    st.caption(
        "Acompanhamento das solicitações de auditoria recebidas."
    )

    base = df.copy()

    # INDICADORES
    exibir_indicadores(base)

    st.divider()

    # ==========================================
    # CADASTRAR NOVA AUDITORIA
    # ==========================================

    with st.expander("➕ Cadastrar nova auditoria"):

        with st.form("form_nova_auditoria"):

            c1, c2 = st.columns(2)

            with c1:

                data_recebimento = st.date_input(
                    "Data de recebimento",
                    value=date.today()
                )

                carteira_nova = st.text_input(
                    "Carteira"
                )

                urgencia_nova = st.selectbox(
                    "Urgência",
                    [1, 2, 3],
                    format_func=lambda x: {
                        1: "1 - Baixa",
                        2: "2 - Média",
                        3: "3 - Alta"
                    }[x]
                )

                prazo_novo = st.date_input(
                    "Prazo",
                    value=date.today()
                )

                responsavel_novo = st.text_input(
                    "Responsável"
                )

            with c2:

                status_novo = st.selectbox(
                    "Status",
                    [
                        "PENDENTE",
                        "EM ANDAMENTO",
                        "CONCLUÍDA"
                    ]
                )

                origem_nova = st.selectbox(
                    "Origem",
                    [
                        "EMAIL",
                        "SISTEMA",
                        "OUTRO"
                    ]
                )

                descricao_nova = st.text_area(
                    "Descrição"
                )

                observacoes_novas = st.text_area(
                    "Observações"
                )

            cadastrar = st.form_submit_button(
                "Salvar auditoria",
                use_container_width=True
            )

            if cadastrar:

                if not carteira_nova.strip():

                    st.error("Informe a carteira.")

                elif not responsavel_novo.strip():

                    st.error("Informe o responsável.")

                else:

                    try:

                        caminho = DATA_DIR / "Base_Auditorias.xlsx"

                        if caminho.exists():

                            base_atualizada = pd.read_excel(
                                caminho,
                                engine="openpyxl"
                            )

                            if not base_atualizada.empty:

                                ids_existentes = pd.to_numeric(
                                    base_atualizada["ID"],
                                    errors="coerce"
                                )

                                novo_id = (
                                    int(ids_existentes.max()) + 1
                                    if ids_existentes.notna().any()
                                    else 1
                                )

                            else:

                                novo_id = 1

                        else:

                            base_atualizada = pd.DataFrame(
                                columns=COLUNAS_AUDITORIAS
                            )

                            novo_id = 1

                        nova_auditoria = {
                            "ID": novo_id,
                            "DATA DE RECEBIMENTO": data_recebimento,
                            "CARTEIRA": carteira_nova.strip(),
                            "URGÊNCIA": urgencia_nova,
                            "PRAZO": prazo_novo,
                            "RESPONSAVEL": responsavel_novo.strip(),
                            "STATUS": status_novo,
                            "ORIGEM": origem_nova,
                            "DESCRIÇÃO": descricao_nova,
                            "OBSERVAÇÕES": observacoes_novas
                        }

                        nova_linha = pd.DataFrame(
                            [nova_auditoria],
                            columns=COLUNAS_AUDITORIAS
                        )

                        base_atualizada = pd.concat(
                            [
                                base_atualizada,
                                nova_linha
                            ],
                            ignore_index=True
                        )

                        salvar_auditorias(
                            base_atualizada
                        )

                        st.success(
                            f"Auditoria {novo_id} cadastrada com sucesso!"
                        )

                        st.rerun()

                    except Exception as erro:

                        st.error(
                            f"Erro ao cadastrar auditoria: {erro}"
                        )

    # ==========================================
    # ATUALIZAR STATUS
    # ==========================================

    st.divider()

    st.subheader(
        "Atualizar status de auditoria"
    )

    if not df.empty:

        with st.form("form_atualizar_status"):

            auditorias_disponiveis = df[
                ["ID", "CARTEIRA", "STATUS"]
            ].dropna(
                subset=["ID"]
            ).copy()

            auditorias_disponiveis["ID"] = (
                auditorias_disponiveis["ID"].astype(int)
            )

            opcoes = auditorias_disponiveis["ID"].tolist()

            id_selecionado = st.selectbox(
                "Selecione a auditoria",
                opcoes,
                format_func=lambda x: formatar_auditoria(
                    x,
                    auditorias_disponiveis
                ),
                key="selecao_atualizar_status"
            )

            status_atual_original = str(
                auditorias_disponiveis.loc[
                    auditorias_disponiveis["ID"] == id_selecionado,
                    "STATUS"
                ].iloc[0]
            ).strip().upper()

            status_atual = normalizar_status(
                status_atual_original
            )

            status_opcoes = [
                "PENDENTE",
                "EM ANDAMENTO",
                "CONCLUÍDA"
            ]

            status_index = (
                status_opcoes.index(status_atual)
                if status_atual in status_opcoes
                else 0
            )

            novo_status = st.selectbox(
                "Novo status",
                status_opcoes,
                index=status_index
            )

            responsavel_alteracao = st.text_input(
                "Quem está realizando a alteração?",
                placeholder="Informe seu nome (opcional)"
            )

            atualizar = st.form_submit_button(
                "Atualizar status",
                use_container_width=True
            )

            if atualizar:

                if novo_status == status_atual:

                    st.info(
                        "O status selecionado é igual ao status atual. "
                        "Nenhuma alteração foi realizada."
                    )

                else:

                    try:

                        caminho = DATA_DIR / "Base_Auditorias.xlsx"

                        base_atualizada = pd.read_excel(
                            caminho,
                            engine="openpyxl"
                        )

                        mascara_auditoria = (
                            pd.to_numeric(
                                base_atualizada["ID"],
                                errors="coerce"
                            ) == id_selecionado
                        )

                        if not mascara_auditoria.any():

                            st.error(
                                "A auditoria selecionada não foi encontrada "
                                "na Base_Auditorias.xlsx."
                            )

                        else:

                            base_atualizada.loc[
                                mascara_auditoria,
                                "STATUS"
                            ] = novo_status

                            # Salva primeiro a base principal.
                            salvar_auditorias(
                                base_atualizada
                            )

                            # Atualiza os dados locais da tela.
                            df = base_atualizada.copy()
                            base = df.copy()

                            # Tenta registrar o histórico.
                            try:

                                registrar_historico_status(
                                    id_auditoria=id_selecionado,
                                    status_anterior=status_atual,
                                    novo_status=novo_status,
                                    responsavel_alteracao=responsavel_alteracao
                                )

                                st.success(
                                    f"Status da auditoria {id_selecionado} "
                                    f"atualizado com sucesso! "
                                    f"{status_atual} → {novo_status}"
                                )

                            except Exception as erro_historico:

                                st.success(
                                    f"Status da auditoria {id_selecionado} "
                                    f"atualizado com sucesso!"
                                )

                                st.warning(
                                    "O status foi atualizado, mas não foi "
                                    "possível registrar o histórico: "
                                    f"{erro_historico}"
                                )

                    except PermissionError:

                        st.error(
                            "Não foi possível salvar a auditoria. "
                            "Feche a Base_Auditorias.xlsx no Excel e tente novamente."
                        )

                    except Exception as erro:

                        st.error(
                            f"Erro ao atualizar status: {erro}"
                        )

    else:

        st.info(
            "Cadastre uma auditoria para habilitar a atualização de status."
        )

    # ==========================================
    # OPERAÇÕES VINCULADAS
    # ==========================================

    exibir_operacoes_auditoria(df)

    # ==========================================
    # FILTROS
    # ==========================================

    if df.empty:

        st.info(
            "Nenhuma auditoria cadastrada ainda."
        )

        return

    st.divider()

    st.subheader("Filtros")

    carteiras = ["Todas"] + sorted(
        base["CARTEIRA"].dropna().unique().tolist()
    )

    responsaveis = ["Todos"] + sorted(
        base["RESPONSAVEL"].dropna().unique().tolist()
    )

    status_opcoes = ["Todos"] + sorted(
        base["STATUS"].dropna().unique().tolist()
    )

    a, b, c, d = st.columns(4)

    with a:

        carteira = st.selectbox(
            "Carteira",
            carteiras
        )

    with b:

        urgencia = st.selectbox(
            "Urgência",
            ["Todas", 1, 2, 3],
            format_func=lambda x: {
                "Todas": "Todas",
                1: "1 - Baixa",
                2: "2 - Média",
                3: "3 - Alta"
            }.get(x, x)
        )

    with c:

        responsavel = st.selectbox(
            "Responsável",
            responsaveis
        )

    with d:

        status = st.selectbox(
            "Status",
            status_opcoes
        )

    pesquisa = st.text_input(
        "Pesquisar",
        placeholder="Digite uma carteira, descrição ou observação..."
    )

    if carteira != "Todas":

        base = base[
            base["CARTEIRA"] == carteira
        ]

    if urgencia != "Todas":

        base = base[
            base["URGÊNCIA"] == urgencia
        ]

    if responsavel != "Todos":

        base = base[
            base["RESPONSAVEL"] == responsavel
        ]

    if status != "Todos":

        base = base[
            base["STATUS"] == status
        ]

    if pesquisa:

        colunas_pesquisa = [
            "CARTEIRA",
            "DESCRIÇÃO",
            "OBSERVAÇÕES",
            "RESPONSAVEL"
        ]

        mascara = pd.Series(
            False,
            index=base.index
        )

        for coluna in colunas_pesquisa:

            mascara |= base[coluna].astype(str).str.contains(
                pesquisa,
                case=False,
                na=False
            )

        base = base[mascara]

    base = base.sort_values(
        "PRAZO",
        ascending=True,
        na_position="last"
    )

    # ==========================================
    # TABELA DE AUDITORIAS
    # ==========================================

    st.divider()

    st.subheader(
        "Auditorias cadastradas"
    )

    st.metric(
        "Registros encontrados",
        len(base)
    )

    if base.empty:

        st.warning(
            "Nenhuma auditoria encontrada com esses filtros."
        )

        return

    exibicao = base.copy()

    exibicao["URGÊNCIA"] = exibicao[
        "URGÊNCIA"
    ].map({
        1: "1 - BAIXA",
        2: "2 - MÉDIA",
        3: "3 - ALTA"
    }).fillna("Não informada")

    st.dataframe(
        exibicao,
        use_container_width=True,
        hide_index=True
    )

    # ==========================================
    # EXPORTAÇÃO
    # ==========================================

    st.download_button(
        "Exportar auditorias",
        gerar_excel(base),
        "rastro_auditorias.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
