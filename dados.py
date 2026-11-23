
from pathlib import Path
import re

import pandas as pd
import streamlit as st


# ==========================================
# CAMINHOS
# ==========================================

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


# ==========================================
# COLUNAS INTERNAS DO RASTRO
# ==========================================

COLUNAS = [
    "Carteira",
    "Operação",
    "Protocolo",
    "Data de Aquisição",
    "Data de Vencimento",
    "Quantidade",
    "Status",
    "Lastro",
    "Tipo do Ativo",
    "Indicador",
    "PU Atual",
    "Emitente",
    "Sistema"
]


COLUNAS_PENDENTES = [
    "CARTEIRA",
    "OPERAÇÃO",
    "QUANTIDADE",
    "DATA_VENCIMENTO",
    "Sistema"
]


# ==========================================
# COLUNAS DAS AUDITORIAS
# ==========================================

COLUNAS_AUDITORIAS = [
    "ID",
    "DATA DE RECEBIMENTO",
    "CARTEIRA",
    "URGÊNCIA",
    "PRAZO",
    "RESPONSAVEL",
    "STATUS",
    "ORIGEM",
    "DESCRIÇÃO",
    "OBSERVAÇÕES"
]


COLUNAS_OPERACOES_AUDITORIA = [
    "ID_AUDITORIA",
    "CARTEIRA",
    "OPERAÇÃO",
    "QUANTIDADE",
    "DATA_AQUISIÇÃO",
    "DATA_VENCIMENTO"
]


# ==========================================
# COLUNAS INTERNAS DO VCRA
# ==========================================

COLUNAS_VCRA = [
    "Data de Posição",
    "Carteira",
    "Operação",
    "Data de Aquisição",
    "Data de Vencimento",
    "Quantidade",
    "Tipo do Ativo",
    "Emitente",
    "Sistema"
]


# ==========================================
# NORMALIZAÇÃO DE CABEÇALHOS
# ==========================================

def normalizar_cabecalho(coluna):
    return (
        str(coluna)
        .strip()
        .upper()
        .replace("\n", " ")
    )


# ==========================================
# CONVERSÃO SEGURA DE DATAS
# ==========================================

def converter_data_segura(valor):

    if pd.isna(valor):
        return pd.NaT

    if isinstance(valor, pd.Timestamp):
        return valor

    if isinstance(valor, (int, float)):

        numero = float(valor)

        if numero <= 0:
            return pd.NaT

        # Número serial do Excel.
        if 20000 <= numero <= 80000:
            return pd.to_datetime(
                numero,
                unit="D",
                origin="1899-12-30",
                errors="coerce"
            )

        # Formato numérico AAAAMMDD.
        if numero.is_integer():

            texto = str(int(numero))

            if re.fullmatch(r"\d{8}", texto):
                return pd.to_datetime(
                    texto,
                    format="%Y%m%d",
                    errors="coerce"
                )

        return pd.NaT

    texto = str(valor).strip()

    if texto.lower() in [
        "",
        "0",
        "0.0",
        "nan",
        "none",
        "nat",
        "null"
    ]:
        return pd.NaT

    # Data no formato AAAAMMDD.
    if re.fullmatch(r"\d{8}", texto):

        data = pd.to_datetime(
            texto,
            format="%Y%m%d",
            errors="coerce"
        )

        if not pd.isna(data):
            return data

    # Número serial do Excel armazenado como texto.
    if re.fullmatch(r"\d+(\.\d+)?", texto):

        numero = float(texto)

        if 20000 <= numero <= 80000:
            return pd.to_datetime(
                numero,
                unit="D",
                origin="1899-12-30",
                errors="coerce"
            )

        return pd.NaT

    return pd.to_datetime(
        texto,
        errors="coerce",
        dayfirst=True
    )


def converter_coluna_data(base, coluna):

    if coluna in base.columns:

        base[coluna] = base[coluna].apply(
            converter_data_segura
        )

    return base


# ==========================================
# CONVERTER BASE PRINCIPAL
# ==========================================

def converter_base_rastro(base, sistema_padrao):

    base = base.copy()

    base.columns = [
        normalizar_cabecalho(coluna)
        for coluna in base.columns
    ]

    mapeamento = {
        "SISTEMA": "Sistema",
        "CD OPERAÇÃO": "Operação",
        "CARTEIRA": "Carteira",
        "PROTOCOLO": "Protocolo",
        "DT DIGITAÇÃO": "Data de Aquisição",
        "DT DIGITACAO": "Data de Aquisição",
        "DT AQUISIÇÃO": "Data de Aquisição",
        "DT AQUISICAO": "Data de Aquisição",
        "DT VENCIMENTO": "Data de Vencimento",
        "QDE": "Quantidade",
        "TIPO": "Tipo do Ativo",
        "LASTRO": "Lastro",
        "NEG/VENC": "Indicador",
        "CNPJ": "Emitente"
    }

    base = base.rename(columns=mapeamento)

    # NEG/VENC alimenta Indicador e Status.
    if "Indicador" in base.columns:
        base["Status"] = base["Indicador"].copy()

    # Campos opcionais da BASE.
    campos_opcionais = [
        "Protocolo",
        "Data de Aquisição",
        "Status",
        "PU Atual"
    ]

    for coluna in campos_opcionais:

        if coluna not in base.columns:
            base[coluna] = None

    # Sistema.
    if "Sistema" not in base.columns:

        base["Sistema"] = sistema_padrao

    else:

        base["Sistema"] = (
            base["Sistema"]
            .fillna(sistema_padrao)
            .astype(str)
            .str.strip()
        )

        base.loc[
            base["Sistema"] == "",
            "Sistema"
        ] = sistema_padrao

    # Garantir todas as colunas internas.
    for coluna in COLUNAS:

        if coluna not in base.columns:
            base[coluna] = None

    return base[COLUNAS].copy()


# ==========================================
# CONVERTER PENDENTES
# ==========================================

def converter_pendentes(base, sistema_padrao):

    base = base.copy()

    base.columns = [
        normalizar_cabecalho(coluna)
        for coluna in base.columns
    ]

    mapeamento = {
        "SISTEMA": "Sistema",
        "CD OPERAÇÃO": "OPERAÇÃO",
        "CARTEIRA": "CARTEIRA",
        "QDE": "QUANTIDADE",
        "DT VENCIMENTO": "DATA_VENCIMENTO"
    }

    base = base.rename(columns=mapeamento)

    for coluna in COLUNAS_PENDENTES:

        if coluna not in base.columns:
            base[coluna] = None

    base["Sistema"] = (
        base["Sistema"]
        .fillna(sistema_padrao)
        .astype(str)
        .str.strip()
    )

    base.loc[
        base["Sistema"] == "",
        "Sistema"
    ] = sistema_padrao

    return base[COLUNAS_PENDENTES].copy()


# ==========================================
# IDENTIFICAR ENGINE DO EXCEL
# ==========================================

def _identificar_engine(caminho):

    extensao = Path(caminho).suffix.lower()

    if extensao == ".xlsb":
        return "pyxlsb"

    if extensao in [".xlsx", ".xlsm"]:
        return "openpyxl"

    raise ValueError(
        f"Formato de Excel não suportado: {extensao}"
    )


# ==========================================
# LEITURA DE EXCEL LZ E XZ
# ==========================================

@st.cache_data
def _ler_excel(
    caminho: str,
    modificacao: float,
    aba: str
) -> pd.DataFrame:

    engine = _identificar_engine(caminho)

    return pd.read_excel(
        caminho,
        sheet_name=aba,
        engine=engine
    )


# ==========================================
# CARREGAR BASES CLASSIFICADAS
# ==========================================

def carregar_bases():

    partes = []
    avisos = []

    arquivos = [
        ("Base_LZ.xlsb", "LZ"),
        ("Base_XZ.xlsb", "XZ")
    ]

    for nome, sistema in arquivos:

        caminho = DATA_DIR / nome

        if not caminho.exists():

            avisos.append(
                f"Arquivo não encontrado: {nome}."
            )

            continue

        try:

            base = _ler_excel(
                str(caminho),
                caminho.stat().st_mtime,
                "BASE"
            ).copy()

            base = converter_base_rastro(
                base,
                sistema
            )

            # Converter datas.
            for coluna in [
                "Data de Aquisição",
                "Data de Vencimento"
            ]:

                base = converter_coluna_data(
                    base,
                    coluna
                )

            # Quantidade.
            base["Quantidade"] = pd.to_numeric(
                base["Quantidade"],
                errors="coerce"
            )

            # PU.
            base["PU Atual"] = pd.to_numeric(
                base["PU Atual"],
                errors="coerce"
            )

            # Protocolo.
            base["Protocolo"] = (
                base["Protocolo"]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            base.loc[
                base["Protocolo"].str.lower().isin(
                    ["nan", "none", "null"]
                ),
                "Protocolo"
            ] = ""

            partes.append(base)

        except Exception as erro:

            avisos.append(
                f"Não foi possível ler a aba BASE de {nome}: {erro}"
            )

    if not partes:

        return pd.DataFrame(columns=COLUNAS), avisos

    return pd.concat(
        partes,
        ignore_index=True
    ), avisos


# ==========================================
# CARREGAR PENDÊNCIAS
# ==========================================

def carregar_pendentes():

    partes = []
    avisos = []

    arquivos = [
        ("Base_LZ.xlsb", "LZ"),
        ("Base_XZ.xlsb", "XZ")
    ]

    for nome, sistema in arquivos:

        caminho = DATA_DIR / nome

        if not caminho.exists():

            avisos.append(
                f"Arquivo não encontrado: {nome}."
            )

            continue

        try:

            base = _ler_excel(
                str(caminho),
                caminho.stat().st_mtime,
                "PENDENTES"
            ).copy()

            base = converter_pendentes(
                base,
                sistema
            )

            base = base.dropna(how="all")

            for coluna in [
                "CARTEIRA",
                "OPERAÇÃO"
            ]:

                base[coluna] = (
                    base[coluna]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

            base["QUANTIDADE"] = pd.to_numeric(
                base["QUANTIDADE"],
                errors="coerce"
            )

            base = converter_coluna_data(
                base,
                "DATA_VENCIMENTO"
            )

            base = base[
                (base["CARTEIRA"] != "") |
                (base["OPERAÇÃO"] != "")
            ]

            partes.append(base)

        except Exception as erro:

            avisos.append(
                f"Não foi possível ler a aba PENDENTES de {nome}: {erro}"
            )

    if not partes:

        return pd.DataFrame(
            columns=COLUNAS_PENDENTES
        ), avisos

    return pd.concat(
        partes,
        ignore_index=True
    ), avisos


# ==========================================
# GARANTIR BASE DE OPERAÇÕES DAS AUDITORIAS
# ==========================================

def garantir_base_operacoes_auditoria():

    caminho = DATA_DIR / "Base_Operacoes_Auditoria.xlsx"

    if not caminho.exists():

        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        pd.DataFrame(
            columns=COLUNAS_OPERACOES_AUDITORIA
        ).to_excel(
            caminho,
            index=False,
            engine="openpyxl"
        )


# ==========================================
# CARREGAR AUDITORIAS
# ==========================================

@st.cache_data
def _ler_excel_auditorias(
    caminho: str,
    modificacao: float
) -> pd.DataFrame:

    return pd.read_excel(
        caminho,
        engine="openpyxl"
    )


def carregar_auditorias():

    caminho = DATA_DIR / "Base_Auditorias.xlsx"
    avisos = []

    if not caminho.exists():

        avisos.append(
            "Arquivo Base_Auditorias.xlsx não encontrado na pasta data."
        )

        return pd.DataFrame(
            columns=COLUNAS_AUDITORIAS
        ), avisos

    try:

        base = _ler_excel_auditorias(
            str(caminho),
            caminho.stat().st_mtime
        )

        for coluna in COLUNAS_AUDITORIAS:

            if coluna not in base.columns:
                base[coluna] = None

        base = base[COLUNAS_AUDITORIAS].copy()

        return base, avisos

    except Exception as erro:

        avisos.append(
            f"Erro ao carregar a base de auditorias: {erro}"
        )

        return pd.DataFrame(
            columns=COLUNAS_AUDITORIAS
        ), avisos


# ==========================================
# CARREGAR OPERAÇÕES DAS AUDITORIAS
# ==========================================

@st.cache_data
def _ler_excel_operacoes(
    caminho: str,
    modificacao: float
) -> pd.DataFrame:

    return pd.read_excel(
        caminho,
        engine="openpyxl"
    )


def carregar_operacoes_auditoria():

    caminho = DATA_DIR / "Base_Operacoes_Auditoria.xlsx"
    avisos = []

    if not caminho.exists():

        avisos.append(
            "Arquivo Base_Operacoes_Auditoria.xlsx não encontrado."
        )

        return pd.DataFrame(
            columns=COLUNAS_OPERACOES_AUDITORIA
        ), avisos

    try:

        base = _ler_excel_operacoes(
            str(caminho),
            caminho.stat().st_mtime
        )

        for coluna in COLUNAS_OPERACOES_AUDITORIA:

            if coluna not in base.columns:
                base[coluna] = None

        base = base[
            COLUNAS_OPERACOES_AUDITORIA
        ].copy()

        return base, avisos

    except Exception as erro:

        avisos.append(
            f"Erro ao carregar operações das auditorias: {erro}"
        )

        return pd.DataFrame(
            columns=COLUNAS_OPERACOES_AUDITORIA
        ), avisos


# ==========================================
# INICIALIZAÇÃO
# ==========================================

garantir_base_operacoes_auditoria()


# ==========================================
# LEITURA DO VCRA
# ==========================================

@st.cache_data
def _ler_excel_vcra(
    caminho: str,
    modificacao: float,
    tamanho: int,
    aba: str
) -> pd.DataFrame:

    return pd.read_excel(
        caminho,
        sheet_name=aba,
        engine="openpyxl",
        header=8
    )


# ==========================================
# CONVERTER CABEÇALHOS DO VCRA
# ==========================================

def converter_vcra(base):

    base = base.copy()

    base.columns = [
        normalizar_cabecalho(coluna)
        for coluna in base.columns
    ]

    mapeamento = {
        "DATA_POSICAO": "Data de Posição",
        "SIGLA_CARTEIRA": "Carteira",
        "CODIGO_OPERACAO": "Operação",
        "CODIGO_LASTRO": "Lastro",
        "TIPO_ATIVO": "Tipo do Ativo",
        "CODIGO_EMITENTE": "Emitente",
        "DATA_AQUISICAO": "Data de Aquisição",
        "DATA_VENCIMENTO": "Data de Vencimento",
        "QUANTIDADE_TOTAL": "Quantidade",
        "VALOR_PU": "PU Atual",
        "CODIGO_SISTEMA": "Sistema",
        "INDICADOR_NEGOCIACAO_VENCIMENTO": "Indicador"
    }

    return base.rename(columns=mapeamento)


# ==========================================
# CARREGAR BASE VCRA
# ==========================================

def carregar_vcra():

    caminho = DATA_DIR / "Base_VCRA.xlsm"
    avisos = []

    if not caminho.exists():

        return pd.DataFrame(
            columns=COLUNAS_VCRA
        ), [
            "Arquivo Base_VCRA.xlsm não encontrado na pasta data."
        ]

    try:

        modificacao = caminho.stat().st_mtime
        tamanho = caminho.stat().st_size

        base = _ler_excel_vcra(
            str(caminho),
            modificacao,
            tamanho,
            "VCRA"
        ).copy()

        base = converter_vcra(base)

        # Validar colunas obrigatórias antes de selecionar.
        faltantes = [
            coluna
            for coluna in COLUNAS_VCRA
            if coluna not in base.columns
        ]

        if faltantes:

            return pd.DataFrame(
                columns=COLUNAS_VCRA
            ), [
                f"Colunas ausentes na base VCRA: {', '.join(faltantes)}."
            ]

        base = base[COLUNAS_VCRA].copy()

        # Converter datas.
        for coluna in [
            "Data de Posição",
            "Data de Aquisição",
            "Data de Vencimento"
        ]:

            base = converter_coluna_data(
                base,
                coluna
            )

        # Converter quantidade.
        base["Quantidade"] = pd.to_numeric(
            base["Quantidade"],
            errors="coerce"
        )

        # Normalizar textos.
        for coluna in [
            "Carteira",
            "Operação",
            "Tipo do Ativo",
            "Emitente",
            "Sistema"
        ]:

            base[coluna] = (
                base[coluna]
                .fillna("")
                .astype(str)
                .str.strip()
            )

        # Manter registros com data de posição.
        base = base.dropna(
            subset=["Data de Posição"]
        )

        return base, avisos

    except Exception as erro:

        return pd.DataFrame(
            columns=COLUNAS_VCRA
        ), [
            f"Erro ao carregar a base VCRA: {erro}"
        ]
