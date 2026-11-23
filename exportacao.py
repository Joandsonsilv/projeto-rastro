
from io import BytesIO

import pandas as pd


# ==========================================
# GERAR ARQUIVO EXCEL
# ==========================================

def gerar_excel(df):

    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Resultado"
        )

    return buffer.getvalue()


# ==========================================
# GERAR RESUMO EM TEXTO
# ==========================================

def resumo_texto(df):

    linhas = []

    for _, r in df.iterrows():

        protocolo = r.get("Protocolo", "-")
        operacao = r.get("Operação", "-")
        carteira = r.get("Carteira", "-")
        sistema = r.get("Sistema", "-")
        quantidade = r.get("Quantidade", "-")
        status = r.get("Status", "-")
        vencimento = r.get("Data de Vencimento", None)

        # Tratar valores vazios

        if pd.isna(protocolo):
            protocolo = "-"

        if pd.isna(operacao):
            operacao = "-"

        if pd.isna(carteira):
            carteira = "-"

        if pd.isna(sistema):
            sistema = "-"

        if pd.isna(quantidade):
            quantidade = "-"

        if pd.isna(status):
            status = "-"

        # Formatar vencimento

        data_formatada = "-"

        if pd.notna(vencimento):

            data_convertida = pd.to_datetime(
                vencimento,
                errors="coerce"
            )

            if pd.notna(data_convertida):

                data_formatada = data_convertida.strftime(
                    "%d/%m/%Y"
                )

        # Montar resumo

        linhas.append(
            f"Protocolo: {protocolo} | "
            f"Operação: {operacao} | "
            f"Carteira: {carteira} | "
            f"Sistema: {sistema} | "
            f"Quantidade: {quantidade} | "
            f"Status: {status} | "
            f"Vencimento: {data_formatada}"
        )

    return "\n".join(linhas)
