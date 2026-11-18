
import re
import unicodedata

import pandas as pd
import streamlit as st

from modules.dados import carregar_vcra


# ==========================================
# CONFIGURAÇÕES DA COMPARAÇÃO
# ==========================================

CHAVES_IDENTIDADE = [
    "Data de Aquisição",
    "Data de Vencimento",
    "Tipo do Ativo",
    "Emitente"
]

CHAVES_LOCALIZACAO = [
    "Carteira",
    "Operação",
    "Sistema"
]

TOLERANCIA = 0.000001

REGISTROS_POR_PAGINA = 100

COLUNAS_RESULTADO = [
    "Movimentação",
    "Quantidade",
    "Quantidade restante na origem",
    "Tipo do Ativo",
    "Emitente",
    "Data de Aquisição",
    "Data de Vencimento",
    "Carteira de origem",
    "Operação de origem",
    "Sistema de origem",
    "Carteira de destino",
    "Operação de destino",
    "Sistema de destino",
    "Observação"
]


# ==========================================
# NORMALIZAÇÃO
# ==========================================

def normalizar_chave(valor):

    if pd.isna(valor):
        return ""

    if isinstance(valor, (pd.Timestamp,)):
        return valor.strftime("%Y-%m-%d")

    texto = str(valor).strip().upper()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    return texto


def normalizar_emitente(valor):

    """
    Normaliza o CNPJ do emitente.

    Remove pontos, barras, traços e espaços para evitar
    diferenças de formatação na identificação do ativo.
    """

    texto = normalizar_chave(valor)

    return re.sub(r"[^A-Z0-9]", "", texto)


def dados_local(local):

    if not local:
        return {
            "Carteira": "-",
            "Operação": "-",
            "Sistema": "-"
        }

    return {
        "Carteira": local[0] or "-",
        "Operação": local[1] or "-",
        "Sistema": local[2] or "-"
    }


# ==========================================
# ORGANIZAR POSIÇÕES POR ATIVO
# ==========================================

def organizar_posicoes(df):

    resultado = {}

    if df.empty:
        return resultado

    colunas_necessarias = (
        CHAVES_IDENTIDADE
        + CHAVES_LOCALIZACAO
        + ["Quantidade"]
    )

    dados = df[colunas_necessarias].copy()

    # Normalizar campos utilizados na comparação

    for coluna in CHAVES_IDENTIDADE + CHAVES_LOCALIZACAO:

        if coluna == "Emitente":

            dados[coluna] = dados[coluna].apply(
                normalizar_emitente
            )

        else:

            dados[coluna] = dados[coluna].apply(
                normalizar_chave
            )

    dados["Quantidade"] = pd.to_numeric(
        dados["Quantidade"],
        errors="coerce"
    ).fillna(0)

    # Agrupar registros com a mesma identidade e localização

    agrupado = (
        dados
        .groupby(
            CHAVES_IDENTIDADE + CHAVES_LOCALIZACAO,
            dropna=False,
            sort=False
        )["Quantidade"]
        .sum()
        .reset_index()
    )

    for linha in agrupado.to_dict("records"):

        identidade = tuple(
            linha[coluna]
            for coluna in CHAVES_IDENTIDADE
        )

        local = tuple(
            linha[coluna]
            for coluna in CHAVES_LOCALIZACAO
        )

        if identidade not in resultado:

            resultado[identidade] = {
                "locais": {},
                "tipo": identidade[2],
                "emitente": identidade[3]
            }

        resultado[identidade]["locais"][local] = float(
            linha["Quantidade"]
        )

    return resultado


# ==========================================
# MONTAR LINHA DO RESULTADO
# ==========================================

def criar_linha(
    movimentacao,
    quantidade,
    tipo_ativo,
    emitente,
    data_aquisicao,
    data_vencimento,
    origem=None,
    destino=None,
    quantidade_restante_origem=None,
    observacao=""
):

    origem_info = dados_local(origem)
    destino_info = dados_local(destino)

    if quantidade_restante_origem is None:
        quantidade_restante_origem = "-"

    return {
        "Movimentação": movimentacao,
        "Quantidade": quantidade,
        "Quantidade restante na origem": quantidade_restante_origem,
        "Tipo do Ativo": tipo_ativo,
        "Emitente": emitente,
        "Data de Aquisição": data_aquisicao,
        "Data de Vencimento": data_vencimento,

        "Carteira de origem": origem_info["Carteira"],
        "Operação de origem": origem_info["Operação"],
        "Sistema de origem": origem_info["Sistema"],

        "Carteira de destino": destino_info["Carteira"],
        "Operação de destino": destino_info["Operação"],
        "Sistema de destino": destino_info["Sistema"],

        "Observação": observacao
    }


# ==========================================
# IDENTIFICAR MOVIMENTAÇÕES
# ==========================================

def identificar_movimentacoes(posicao_anterior, posicao_atual):

    anterior = organizar_posicoes(posicao_anterior)
    atual = organizar_posicoes(posicao_atual)

    movimentacoes = []

    todas_identidades = sorted(
        set(anterior) | set(atual)
    )

    for identidade in todas_identidades:

        dados_ant = anterior.get(
            identidade,
            {"locais": {}, "tipo": "", "emitente": ""}
        )

        dados_atual = atual.get(
            identidade,
            {"locais": {}, "tipo": "", "emitente": ""}
        )

        locais_ant = dados_ant["locais"]
        locais_atual = dados_atual["locais"]

        tipo_ativo = dados_atual["tipo"] or dados_ant["tipo"]
        emitente = dados_atual["emitente"] or dados_ant["emitente"]

        data_aquisicao = identidade[0]
        data_vencimento = identidade[1]

        todos_locais = sorted(
            set(locais_ant) | set(locais_atual)
        )

        origens = []
        destinos = []

        # Identificar reduções e aumentos

        for local in todos_locais:

            quantidade_ant = locais_ant.get(local, 0)
            quantidade_atual = locais_atual.get(local, 0)

            diferenca = quantidade_atual - quantidade_ant

            if abs(diferenca) < TOLERANCIA:

                if quantidade_ant > 0:

                    movimentacoes.append(
                        criar_linha(
                            movimentacao="Sem alteração",
                            quantidade=quantidade_atual,
                            tipo_ativo=tipo_ativo,
                            emitente=emitente,
                            data_aquisicao=data_aquisicao,
                            data_vencimento=data_vencimento,
                            origem=local,
                            destino=local,
                            quantidade_restante_origem=quantidade_atual,
                            observacao="Quantidade e localização mantidas."
                        )
                    )

            elif diferenca < 0:

                origens.append({
                    "local": local,
                    "restante": abs(diferenca),
                    "anterior": quantidade_ant,
                    "atual": quantidade_atual
                })

            else:

                destinos.append({
                    "local": local,
                    "restante": diferenca,
                    "anterior": quantidade_ant,
                    "atual": quantidade_atual
                })

        # ======================================
        # VÁRIAS ORIGENS E DESTINOS
        # ======================================

        grupo_necessita_conferencia = (
            len(origens) > 1 and len(destinos) > 0
        )

        if grupo_necessita_conferencia:

            # Não associa automaticamente uma origem a um destino.
            # Cada redução e cada aumento ficam separados para conferência.

            for origem in origens:

                movimentacoes.append(
                    criar_linha(
                        movimentacao="Necessita conferência",
                        quantidade=origem["restante"],
                        tipo_ativo=tipo_ativo,
                        emitente=emitente,
                        data_aquisicao=data_aquisicao,
                        data_vencimento=data_vencimento,
                        origem=origem["local"],
                        quantidade_restante_origem=origem["atual"],
                        observacao=(
                            "Existem várias origens e destinos possíveis "
                            "para este ativo. A associação entre as "
                            "localizações não foi determinada."
                        )
                    )
                )

            for destino in destinos:

                movimentacoes.append(
                    criar_linha(
                        movimentacao="Necessita conferência",
                        quantidade=destino["restante"],
                        tipo_ativo=tipo_ativo,
                        emitente=emitente,
                        data_aquisicao=data_aquisicao,
                        data_vencimento=data_vencimento,
                        destino=destino["local"],
                        observacao=(
                            "Existe aumento de quantidade, mas há várias "
                            "origens possíveis. A origem correspondente "
                            "precisa ser conferida."
                        )
                    )
                )

            continue

        # ======================================
        # DISTRIBUIR QUANTIDADES
        # QUANDO HÁ UMA ÚNICA ORIGEM
        # ======================================

        indice_destino = 0

        for origem in origens:

            quantidade_transferida = 0
            correspondencias = []

            while (
                origem["restante"] > TOLERANCIA
                and indice_destino < len(destinos)
            ):

                destino = destinos[indice_destino]

                if destino["restante"] <= TOLERANCIA:
                    indice_destino += 1
                    continue

                quantidade = min(
                    origem["restante"],
                    destino["restante"]
                )

                origem["restante"] -= quantidade
                destino["restante"] -= quantidade

                quantidade_transferida += quantidade

                correspondencias.append({
                    "destino": destino["local"],
                    "quantidade": quantidade
                })

                if destino["restante"] <= TOLERANCIA:
                    indice_destino += 1

            # ==================================
            # CLASSIFICAR A TRANSFERÊNCIA
            # ==================================

            if quantidade_transferida > 0:

                transferencia_total = (
                    origem["atual"] <= TOLERANCIA
                    and quantidade_transferida >= (
                        origem["anterior"] - TOLERANCIA
                    )
                )

                if transferencia_total:

                    classificacao = "Possível transferência total"

                else:

                    classificacao = "Possível transferência parcial"

                for correspondencia in correspondencias:

                    quantidade_destino = correspondencia["quantidade"]

                    observacao_destino = (
                        f"Esta linha representa {quantidade_destino:g} "
                        f"unidades de uma possível transferência de "
                        f"{quantidade_transferida:g} unidades. "
                        "A associação precisa de validação."
                    )

                    movimentacoes.append(
                        criar_linha(
                            movimentacao=classificacao,
                            quantidade=quantidade_destino,
                            tipo_ativo=tipo_ativo,
                            emitente=emitente,
                            data_aquisicao=data_aquisicao,
                            data_vencimento=data_vencimento,
                            origem=origem["local"],
                            destino=correspondencia["destino"],
                            quantidade_restante_origem=origem["atual"],
                            observacao=observacao_destino
                        )
                    )

            # ==================================
            # QUANTIDADE REDUZIDA SEM DESTINO
            # ==================================

            if origem["restante"] > TOLERANCIA:

                if origem["atual"] <= TOLERANCIA:

                    classificacao = "Possível saída/baixa"

                else:

                    classificacao = "Redução de quantidade"

                observacao = (
                    "Não foi encontrada quantidade correspondente "
                    "em outra localização."
                )

                movimentacoes.append(
                    criar_linha(
                        movimentacao=classificacao,
                        quantidade=origem["restante"],
                        tipo_ativo=tipo_ativo,
                        emitente=emitente,
                        data_aquisicao=data_aquisicao,
                        data_vencimento=data_vencimento,
                        origem=origem["local"],
                        quantidade_restante_origem=origem["atual"],
                        observacao=observacao
                    )
                )

        # ======================================
        # AUMENTOS SEM ORIGEM CORRESPONDENTE
        # ======================================

        for destino in destinos:

            if destino["restante"] <= TOLERANCIA:
                continue

            if destino["anterior"] <= TOLERANCIA:

                classificacao = "Nova entrada sem origem identificada"

                observacao = (
                    "Não foi encontrada redução correspondente "
                    "em outra localização."
                )

            else:

                classificacao = "Aumento de quantidade"

                observacao = (
                    "Quantidade aumentou sem correspondência "
                    "com uma redução identificada."
                )

            movimentacoes.append(
                criar_linha(
                    movimentacao=classificacao,
                    quantidade=destino["restante"],
                    tipo_ativo=tipo_ativo,
                    emitente=emitente,
                    data_aquisicao=data_aquisicao,
                    data_vencimento=data_vencimento,
                    destino=destino["local"],
                    observacao=observacao
                )
            )

    return pd.DataFrame(
        movimentacoes,
        columns=COLUNAS_RESULTADO
    )


# ==========================================
# FILTROS DAS MOVIMENTAÇÕES
# ==========================================

def aplicar_filtros(resultado):

    st.subheader("Filtros")

    with st.expander("Abrir filtros", expanded=True):

        situacao = st.radio(
            "Situação da movimentação",
            options=[
                "Todas",
                "Somente com movimentação",
                "Somente sem alteração"
            ],
            horizontal=True,
            key="filtro_situacao"
        )

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            filtro_movimentacao = st.multiselect(
                "Tipo de movimentação",
                options=sorted(
                    resultado["Movimentação"].dropna().unique()
                ),
                key="filtro_movimentacao"
            )

        with col2:
            filtro_tipo = st.multiselect(
                "Tipo do ativo",
                options=sorted(
                    resultado["Tipo do Ativo"].dropna().unique()
                ),
                key="filtro_tipo"
            )

        with col3:
            filtro_emitente = st.multiselect(
                "Emitente",
                options=sorted(
                    resultado["Emitente"].dropna().unique()
                ),
                key="filtro_emitente"
            )

        st.divider()

        col4, col5, col6 = st.columns(3)

        with col4:
            filtro_carteira_origem = st.multiselect(
                "Carteira de origem",
                options=sorted(
                    resultado["Carteira de origem"]
                    .replace("-", pd.NA)
                    .dropna()
                    .unique()
                ),
                key="filtro_carteira_origem"
            )

        with col5:
            filtro_operacao_origem = st.multiselect(
                "Operação de origem",
                options=sorted(
                    resultado["Operação de origem"]
                    .replace("-", pd.NA)
                    .dropna()
                    .unique()
                ),
                key="filtro_operacao_origem"
            )

        with col6:
            filtro_sistema_origem = st.multiselect(
                "Sistema de origem",
                options=sorted(
                    resultado["Sistema de origem"]
                    .replace("-", pd.NA)
                    .dropna()
                    .unique()
                ),
                key="filtro_sistema_origem"
            )

        col7, col8, col9 = st.columns(3)

        with col7:
            filtro_carteira_destino = st.multiselect(
                "Carteira de destino",
                options=sorted(
                    resultado["Carteira de destino"]
                    .replace("-", pd.NA)
                    .dropna()
                    .unique()
                ),
                key="filtro_carteira_destino"
            )

        with col8:
            filtro_operacao_destino = st.multiselect(
                "Operação de destino",
                options=sorted(
                    resultado["Operação de destino"]
                    .replace("-", pd.NA)
                    .dropna()
                    .unique()
                ),
                key="filtro_operacao_destino"
            )

        with col9:
            filtro_sistema_destino = st.multiselect(
                "Sistema de destino",
                options=sorted(
                    resultado["Sistema de destino"]
                    .replace("-", pd.NA)
                    .dropna()
                    .unique()
                ),
                key="filtro_sistema_destino"
            )

    filtrado = resultado.copy()

    if situacao == "Somente com movimentação":

        filtrado = filtrado[
            filtrado["Movimentação"] != "Sem alteração"
        ]

    elif situacao == "Somente sem alteração":

        filtrado = filtrado[
            filtrado["Movimentação"] == "Sem alteração"
        ]

    filtros = [
        ("Movimentação", filtro_movimentacao),
        ("Tipo do Ativo", filtro_tipo),
        ("Emitente", filtro_emitente),
        ("Carteira de origem", filtro_carteira_origem),
        ("Operação de origem", filtro_operacao_origem),
        ("Sistema de origem", filtro_sistema_origem),
        ("Carteira de destino", filtro_carteira_destino),
        ("Operação de destino", filtro_operacao_destino),
        ("Sistema de destino", filtro_sistema_destino)
    ]

    for coluna, valores in filtros:

        if valores:
            filtrado = filtrado[
                filtrado[coluna].isin(valores)
            ]

    return filtrado


# ==========================================
# CONSULTA PAGINADA DAS POSIÇÕES
# ==========================================

def exibir_consulta_posicao(df, identificador):

    consulta = df.drop(
        columns=["Data de Posição"],
        errors="ignore"
    ).copy()

    st.caption(
        "Consulte os registros da posição usando os filtros abaixo. "
        "São exibidos até 100 registros por página."
    )

    st.markdown("**Filtros da posição**")

    colunas_filtros = [
        ("Carteira", "carteira"),
        ("Operação", "operacao"),
        ("Sistema", "sistema"),
        ("Tipo do Ativo", "tipo"),
        ("Emitente", "emitente")
    ]

    colunas = st.columns(5)

    for coluna, (campo, nome_chave) in zip(
        colunas,
        colunas_filtros
    ):

        with coluna:

            if campo in consulta.columns:

                pesquisa = st.text_input(
                    campo,
                    key=f"pesquisa_{identificador}_{nome_chave}",
                    placeholder="Pesquisar..."
                )

                if pesquisa.strip():

                    consulta = consulta[
                        consulta[campo]
                        .astype("string")
                        .str.contains(
                            pesquisa.strip(),
                            case=False,
                            na=False,
                            regex=False
                        )
                    ]

    total_registros = len(consulta)

    st.divider()

    st.caption(
        "Total de registros encontrados: "
        f"{total_registros:,}".replace(",", ".")
    )

    if total_registros == 0:

        st.info(
            "Nenhum registro encontrado com esses filtros."
        )
        return

    total_paginas = (
        total_registros + REGISTROS_POR_PAGINA - 1
    ) // REGISTROS_POR_PAGINA

    pagina = st.selectbox(
        "Página",
        options=list(range(1, total_paginas + 1)),
        format_func=lambda p: f"{p} de {total_paginas}",
        key=(
            f"pagina_{identificador}_"
            f"{total_paginas}_{total_registros}"
        )
    )

    inicio = (pagina - 1) * REGISTROS_POR_PAGINA
    fim = inicio + REGISTROS_POR_PAGINA

    amostra = consulta.iloc[inicio:fim]

    st.caption(
        f"Exibindo registros {inicio + 1} até "
        f"{min(fim, total_registros):,}."
        .replace(",", ".")
    )

    st.dataframe(
        amostra,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# TELA PRINCIPAL
# ==========================================

def tela_rastreamento():

    st.title("Rastreamento de Movimentações")

    st.caption(
        "Compare posições do VCRA para identificar alterações "
        "nas operações e quantidades."
    )

    df, avisos = carregar_vcra()

    for aviso in avisos:
        st.warning(aviso)

    if df.empty:

        st.info("Nenhuma posição disponível na base VCRA.")
        return

    datas = sorted(
        df["Data de Posição"].dropna().dt.date.unique()
    )

    if len(datas) < 2:

        st.warning(
            "É necessário ter pelo menos duas datas de posição "
            "para realizar uma comparação."
        )
        return

    # ======================================
    # SELECIONAR POSIÇÕES
    # ======================================

    st.subheader("Selecionar posições")

    col1, col2 = st.columns(2)

    with col1:

        data_anterior = st.selectbox(
            "Data anterior",
            options=datas,
            index=len(datas) - 2,
            format_func=lambda data: data.strftime("%d/%m/%Y")
        )

    with col2:

        data_atual = st.selectbox(
            "Data atual",
            options=datas,
            index=len(datas) - 1,
            format_func=lambda data: data.strftime("%d/%m/%Y")
        )

    if data_anterior == data_atual:

        st.warning("Selecione duas datas diferentes.")
        return

    posicao_anterior = df[
        df["Data de Posição"].dt.date == data_anterior
    ].copy()

    posicao_atual = df[
        df["Data de Posição"].dt.date == data_atual
    ].copy()

    # ======================================
    # RESUMO DAS POSIÇÕES
    # ======================================

    st.divider()

    st.subheader("Resumo das posições")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Registros anteriores",
        f"{len(posicao_anterior):,}".replace(",", ".")
    )

    col2.metric(
        "Registros atuais",
        f"{len(posicao_atual):,}".replace(",", ".")
    )

    col3.metric(
        "Diferença de registros",
        f"{len(posicao_atual) - len(posicao_anterior):+,}"
        .replace(",", ".")
    )

    # ======================================
    # RESULTADO DA COMPARAÇÃO
    # ======================================

    st.divider()

    st.subheader("Movimentações identificadas")

    resultado = identificar_movimentacoes(
        posicao_anterior,
        posicao_atual
    )

    if resultado.empty:

        st.info("Nenhuma movimentação identificada.")

    else:

        transferencias = resultado[
            resultado["Movimentação"].str.contains(
                "transferência",
                case=False,
                na=False
            )
        ]

        reducoes = resultado[
            resultado["Movimentação"].isin([
                "Redução de quantidade",
                "Possível saída/baixa"
            ])
        ]

        aumentos = resultado[
            resultado["Movimentação"].isin([
                "Aumento de quantidade",
                "Nova entrada sem origem identificada"
            ])
        ]

        sem_alteracao = resultado[
            resultado["Movimentação"] == "Sem alteração"
        ]

        necessita_conferencia = resultado[
            resultado["Movimentação"] == "Necessita conferência"
        ]

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric("Transferências", len(transferencias))
        c2.metric("Reduções / saídas", len(reducoes))
        c3.metric("Aumentos / entradas", len(aumentos))
        c4.metric("Sem alteração", len(sem_alteracao))
        c5.metric(
            "Necessita conferência",
            len(necessita_conferencia)
        )

        resultado_filtrado = aplicar_filtros(resultado)

        st.caption(
            f"Exibindo {len(resultado_filtrado):,} de "
            f"{len(resultado):,} movimentações."
            .replace(",", ".")
        )

        st.dataframe(
            resultado_filtrado[COLUNAS_RESULTADO],
            use_container_width=True,
            hide_index=True
        )

    # ======================================
    # CONSULTA PAGINADA DAS POSIÇÕES
    # ======================================

    st.divider()

    st.subheader("Consulta das posições")

    aba_anterior, aba_atual = st.tabs([
        f"Posição {data_anterior.strftime('%d/%m/%Y')}",
        f"Posição {data_atual.strftime('%d/%m/%Y')}"
    ])

    with aba_anterior:

        exibir_consulta_posicao(
            posicao_anterior,
            "anterior"
        )

    with aba_atual:

        exibir_consulta_posicao(
            posicao_atual,
            "atual"
        )
