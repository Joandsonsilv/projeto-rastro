
from pathlib import Path

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
# CONVERSÃO DOS CABEÇALHOS
# ==========================================

def normalizar_cabecalho(coluna):

    return (
        str(coluna)
        .strip()
        .upper()
        .replace("\n", " ")
    )


def converter_base_rastro(base, sistema_padrao):

    """
    Converte os cabeçalhos das abas BASE das planilhas
    LZ e XZ para os nomes internos utilizados pelo RASTRO.
    """

    base = base.copy()

    base.columns = [
        normalizar_cabecalho(coluna)
        for coluna in base.columns
    ]

    mapeamento = {
        "SISTEMA": "Sistema",
        "CD OPERAÇÃO": "Operação",
        "CARTEIRA": "Carteira",
        "TIPO": "Tipo do Ativo",
        "DT VENCIMENTO": "Data de Vencimento",
        "LASTRO": "Lastro",
        "QDE": "Quantidade",
        "NEG/VENC": "Indicador",
        "CNPJ": "Emitente"
    }

    base = base.rename(columns=mapeamento)

    campos_opcionais = [
        "Data de Aquisição",
        "Status",
        "PU Atual"
    ]

    for coluna in campos_opcionais:

        if coluna not in base.columns:
            base[coluna] = None

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

    for coluna in COLUNAS:

        if coluna not in base.columns:
            base[coluna] = None

    return base[COLUNAS].copy()


def converter_pendentes(base, sistema_padrao):

    """
    Converte os cabeçalhos da aba PENDENTES
    para a estrutura interna do RASTRO.

    A estrutura de PENDENTES não possui Data de Aquisição.
    """

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
# LEITURA DE EXCEL
# ==========================================

def _identificar_engine(caminho):

    """
    Identifica o mecanismo de leitura conforme
    a extensão do arquivo Excel.
    """

    extensao = Path(caminho).suffix.lower()

    if extensao == ".xlsb":
        return "pyxlsb"

    if extensao in [".xlsx", ".xlsm"]:
        return "openpyxl"

    raise ValueError(
        f"Formato de Excel não suportado: {extensao}"
    )


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
        ("Base_RASTRO_LZ.xlsm", "LZ"),
        ("Base_RASTRO_XZ.xlsm", "XZ")
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

            for coluna in [
                "Data de Aquisição",
                "Data de Vencimento"
            ]:

                base[coluna] = pd.to_datetime(
                    base[coluna],
                    errors="coerce",
                    dayfirst=True
                )

            base["Quantidade"] = pd.to_numeric(
                base["Quantidade"],
                errors="coerce"
            )

            base["PU Atual"] = pd.to_numeric(
                base["PU Atual"],
                errors="coerce"
            )

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
        ("Base_RASTRO_LZ.xlsm", "LZ"),
        ("Base_RASTRO_XZ.xlsm", "XZ")
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

            base["DATA_VENCIMENTO"] = pd.to_datetime(
                base["DATA_VENCIMENTO"],
                errors="coerce",
                dayfirst=True
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
# CARREGAR BASE VCRA
# ==========================================

@st.cache_data
def _ler_excel_vcra(
    caminho: str,
    modificacao: float,
    tamanho: int,
    aba: str
) -> pd.DataFrame:

    engine = _identificar_engine(caminho)

    return pd.read_excel(
        caminho,
        sheet_name=aba,
        engine=engine
    )


def converter_vcra(base):

    """
    Converte os cabeçalhos originais da planilha VCRA
    para os nomes internos utilizados pelo RASTRO.

    Não cria colunas ausentes. A validação é feita
    posteriormente em carregar_vcra().
    """

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


def carregar_vcra():

    caminho = DATA_DIR / "Base_VCRA.xlsb"
    avisos = []

    if not caminho.exists():

        return pd.DataFrame(
            columns=COLUNAS_VCRA
        ), [
            "Arquivo Base_VCRA.xlsb não encontrado na pasta data."
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

        for coluna in [
            "Data de Posição",
            "Data de Aquisição",
            "Data de Vencimento"
        ]:

            base[coluna] = pd.to_datetime(
                base[coluna],
                errors="coerce",
                dayfirst=True
            )

        base["Quantidade"] = pd.to_numeric(
            base["Quantidade"],
            errors="coerce"
        )

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
