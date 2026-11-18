
import unicodedata

import pandas as pd
import streamlit as st


# ==========================================
# NORMALIZAÇÃO
# ==========================================

def normalizar_texto(valor):

    if pd.isna(valor):
        return ""

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


# ==========================================
# VALIDAR BASE
# ==========================================

def validar_base(df):

    problemas = []

    if df.empty:
        return pd.DataFrame(
            columns=[
                "Operação",
                "Sistema",
                "Campo",
                "Valor encontrado",
                "Motivo"
            ]
        )

    # Campos que podem ser efetivamente validados
    # conforme a estrutura disponível na base.

    obrigatorios = [
        "Carteira",
        "Operação",
        "Data de Vencimento",
        "Quantidade",
        "Lastro",
        "Tipo do Ativo",
        "Emitente",
        "Sistema"
    ]

    campos_opcionais = [
        "Data de Aquisição",
        "Status",
        "Indicador",
        "PU Atual"
    ]

    colunas_disponiveis = set(df.columns)

    def adicionar_problema(row, campo, motivo):

        problemas.append({
            "Operação": row.get("Operação"),
            "Sistema": row.get("Sistema"),
            "Campo": campo,
            "Valor encontrado": row.get(campo),
            "Motivo": motivo
        })

    for _, row in df.iterrows():

        # ======================================
        # CAMPOS OBRIGATÓRIOS
        # ======================================

        for campo in obrigatorios:

            if campo not in colunas_disponiveis:
                continue

            valor = row.get(campo)

            if pd.isna(valor) or (
                isinstance(valor, str)
                and not valor.strip()
            ):

                adicionar_problema(
                    row,
                    campo,
                    "Campo obrigatório vazio"
                )

        # ======================================
        # DATA DE AQUISIÇÃO
        # ======================================

        if "Data de Aquisição" in colunas_disponiveis:

            data_aquisicao = row.get("Data de Aquisição")
            data_vencimento = row.get("Data de Vencimento")

            if (
                pd.notna(data_aquisicao)
                and pd.notna(data_vencimento)
            ):

                if data_aquisicao > data_vencimento:

                    adicionar_problema(
                        row,
                        "Data de Aquisição",
                        "Aquisição posterior ao vencimento"
                    )

        # ======================================
        # QUANTIDADE
        # ======================================

        if "Quantidade" in colunas_disponiveis:

            quantidade = pd.to_numeric(
                pd.Series([row.get("Quantidade")]),
                errors="coerce"
            ).iloc[0]

            if pd.notna(row.get("Quantidade")) and pd.isna(quantidade):

                adicionar_problema(
                    row,
                    "Quantidade",
                    "Quantidade em formato inválido"
                )

            elif pd.notna(quantidade) and quantidade <= 0:

                adicionar_problema(
                    row,
                    "Quantidade",
                    "Quantidade igual ou inferior a zero"
                )

        # ======================================
        # PU ATUAL
        # ======================================

        if "PU Atual" in colunas_disponiveis:

            pu = pd.to_numeric(
                pd.Series([row.get("PU Atual")]),
                errors="coerce"
            ).iloc[0]

            if pd.notna(row.get("PU Atual")) and pd.isna(pu):

                adicionar_problema(
                    row,
                    "PU Atual",
                    "PU Atual em formato inválido"
                )

            elif pd.notna(pu) and pu <= 0:

                adicionar_problema(
                    row,
                    "PU Atual",
                    "PU Atual inválido (menor ou igual a zero)"
                )

        # ======================================
        # STATUS
        # ======================================

        if "Status" in colunas_disponiveis:

            status = normalizar_texto(
                row.get("Status")
            )

            if status and status not in [
                "NEGOCIACAO",
                "VENCIMENTO"
            ]:

                adicionar_problema(
                    row,
                    "Status",
                    "Status fora dos valores permitidos"
                )

        # ======================================
        # INDICADOR
        # ======================================

        if "Indicador" in colunas_disponiveis:

            indicador = normalizar_texto(
                row.get("Indicador")
            )

            if indicador and indicador not in [
                "NEGOCIACAO",
                "VENCIMENTO"
            ]:

                adicionar_problema(
                    row,
                    "Indicador",
                    "Indicador fora dos valores permitidos"
                )

    # ==========================================
    # IDENTIFICAR OPERAÇÕES DUPLICADAS
    # ==========================================

    colunas_chave = [
        "Sistema",
        "Operação"
    ]

    if all(
        coluna in colunas_disponiveis
        for coluna in colunas_chave
    ):

        base_duplicidade = df.copy()

        base_duplicidade["_SISTEMA_NORMALIZADO"] = (
            base_duplicidade["Sistema"].apply(
                normalizar_texto
            )
        )

        base_duplicidade["_OPERACAO_NORMALIZADA"] = (
            base_duplicidade["Operação"].apply(
                normalizar_texto
            )
        )

        duplicadas = base_duplicidade[
            base_duplicidade.duplicated(
                subset=[
                    "_SISTEMA_NORMALIZADO",
                    "_OPERACAO_NORMALIZADA"
                ],
                keep=False
            )
        ]

        for indice in duplicadas.index:

            row = df.loc[indice]

            adicionar_problema(
                row,
                "Operação",
                "Operação duplicada no mesmo sistema"
            )

    return pd.DataFrame(
        problemas,
        columns=[
            "Operação",
            "Sistema",
            "Campo",
            "Valor encontrado",
            "Motivo"
        ]
    )


# ==========================================
# TELA DE VALIDAÇÕES
# ==========================================

def tela_validacoes(df):

    st.title("Validações da Base")

    st.caption(
        "As validações identificam possíveis problemas; "
        "nenhum dado é corrigido automaticamente."
    )

    if df.empty:

        st.info(
            "Não existem registros disponíveis para validação."
        )
        return

    erros = validar_base(df)

    a, b = st.columns(2)

    a.metric(
        "Inconsistências identificadas",
        len(erros)
    )

    b.metric(
        "Operações analisadas",
        len(df)
    )

    if erros.empty:

        st.success(
            "Nenhuma inconsistência identificada "
            "pelas regras implementadas."
        )

    else:

        st.warning(
            "Foram encontradas inconsistências para análise."
        )

        st.dataframe(
            erros,
            use_container_width=True,
            hide_index=True
        )
