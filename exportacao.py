from io import BytesIO
import pandas as pd

def gerar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")
    return buffer.getvalue()

def resumo_texto(df):
    linhas = []
    for _, r in df.iterrows():
        linhas.append(
            f'Operação: {r["Operação"]} | Carteira: {r["Carteira"]} | '
            f'Sistema: {r["Sistema"]} | Quantidade: {r["Quantidade"]} | '
            f'Status: {r["Status"]} | Vencimento: {r["Data de Vencimento"]:%d/%m/%Y}'
        )
    return "\\n".join(linhas)
