import pandas as pd
import streamlit as st

def validar_base(df):
    problemas = []
    obrigatorios = ["Carteira","Operação","Data de Aquisição","Data de Vencimento",
                    "Quantidade","Status","Lastro","Tipo do Ativo","Indicador","PU Atual","Emitente"]
    for idx, row in df.iterrows():
        def add(campo, motivo):
            problemas.append({"Operação": row.get("Operação"), "Sistema": row.get("Sistema"),
                              "Campo": campo, "Valor encontrado": row.get(campo), "Motivo": motivo})
        for campo in obrigatorios:
            valor = row.get(campo)
            if pd.isna(valor) or (isinstance(valor, str) and not valor.strip()):
                add(campo, "Campo obrigatório vazio")
        if pd.notna(row.get("Data de Aquisição")) and pd.notna(row.get("Data de Vencimento")):
            if row["Data de Aquisição"] > row["Data de Vencimento"]:
                add("Data de Aquisição", "Aquisição posterior ao vencimento")
        if pd.notna(row.get("Quantidade")) and row["Quantidade"] <= 0:
            add("Quantidade", "Quantidade igual ou inferior a zero")
        if pd.notna(row.get("PU Atual")) and row["PU Atual"] <= 0:
            add("PU Atual", "PU Atual inválido (menor ou igual a zero)")
        if row.get("Status") not in ["NEGOCIAÇÃO", "VENCIMENTO"]:
            add("Status", "Status fora dos valores permitidos")
    duplicadas = df[df.duplicated(subset=["Sistema","Operação"], keep=False)]
    for _, row in duplicadas.iterrows():
        problemas.append({"Operação": row["Operação"], "Sistema": row["Sistema"],
                          "Campo": "Operação", "Valor encontrado": row["Operação"],
                          "Motivo": "Operação duplicada no mesmo sistema"})
    return pd.DataFrame(problemas)

def tela_validacoes(df):
    st.title("Validações da Base")
    st.caption("As validações identificam possíveis problemas; nenhum dado é corrigido automaticamente.")
    erros = validar_base(df)
    a,b = st.columns(2)
    a.metric("Inconsistências identificadas", len(erros))
    b.metric("Operações analisadas", len(df))
    if erros.empty:
        st.success("Nenhuma inconsistência identificada pelas regras implementadas.")
    else:
        st.warning("Foram encontradas inconsistências para análise.")
        st.dataframe(erros, use_container_width=True, hide_index=True)
