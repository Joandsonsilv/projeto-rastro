
from pathlib import Path

import pandas as pd
import streamlit as st


# ==========================================
# CAMINHOS
# ==========================================

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


# ==========================================
# COLUNAS DAS BASES
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
    "DATA_AQUISIÇÃO",
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
# LEITURA DE EXCEL
# ==========================================

@st.cache_data
def _ler_excel(caminho: str, modificacao: float, aba: str) -> pd.DataFrame:
    return pd.read_excel(
        caminho,
        sheet_name=aba,
        engine="openpyxl"
    )


# ==========================================
# CARREGAR BASES CLASSIFICADAS
# ==========================================

def carregar_bases():

    partes = []
    avisos = []

    arquivos = [
        ("Base_RASTRO_LZ.xlsx", "LZ", "Sistema LZ"),
        ("Base_RASTRO_XZ.xlsx", "XZ", "Sistema XZ")
    ]

    for nome, sistema, aba in arquivos:

        caminho = DATA_DIR / nome

        if not caminho.exists():
            avisos.append(f"Arquivo não encontrado: {nome}.")
            continue

        try:

            base = _ler_excel(
                str(caminho),
                caminho.stat().st_mtime,
                aba
            ).copy()

            faltantes = [
                coluna
                for coluna in COLUNAS
                if coluna not in base.columns
            ]

            if faltantes:
                avisos.append(
                    f"{nome}: colunas ausentes: {', '.join(faltantes)}."
                )
                continue

            base = base[COLUNAS].copy()

            base["Sistema"] = sistema

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
                f"Não foi possível ler a aba {aba} de {nome}: {erro}"
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
        ("Base_RASTRO_LZ.xlsx", "LZ"),
        ("Base_RASTRO_XZ.xlsx", "XZ")
    ]

    for nome, sistema in arquivos:

        caminho = DATA_DIR / nome

        if not caminho.exists():
            avisos.append(f"Arquivo não encontrado: {nome}.")
            continue

        try:

            base = _ler_excel(
                str(caminho),
                caminho.stat().st_mtime,
                "Pendentes"
            ).copy()

            colunas_origem = [
                "CARTEIRA",
                "OPERAÇÃO",
                "QUANTIDADE",
                "DATA_AQUISIÇÃO",
                "DATA_VENCIMENTO"
            ]

            faltantes = [
                coluna
                for coluna in colunas_origem
                if coluna not in base.columns
            ]

            if faltantes:
                avisos.append(
                    f"{nome} - aba Pendentes: "
                    f"colunas ausentes: {', '.join(faltantes)}."
                )
                continue

            base = base[colunas_origem].copy()

            base = base.dropna(how="all")

            base["Sistema"] = sistema

            for coluna in ["CARTEIRA", "OPERAÇÃO"]:
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

            for coluna in [
                "DATA_AQUISIÇÃO",
                "DATA_VENCIMENTO"
            ]:
                base[coluna] = pd.to_datetime(
                    base[coluna],
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
                f"Não foi possível ler a aba Pendentes de {nome}: {erro}"
            )

    if not partes:
        return pd.DataFrame(columns=COLUNAS_PENDENTES), avisos

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

        base = base[COLUNAS_OPERACOES_AUDITORIA].copy()

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
        usecols=lambda coluna: coluna in COLUNAS_VCRA,
        engine="openpyxl"
    )


def carregar_vcra():

    caminho = DATA_DIR / "Base_VCRA.xlsx"
    avisos = []

    if not caminho.exists():

        return pd.DataFrame(
            columns=COLUNAS_VCRA
        ), [
            "Arquivo Base_VCRA.xlsx não encontrado na pasta data."
        ]

    try:

        modificacao = caminho.stat().st_mtime
        tamanho = caminho.stat().st_size

        base = _ler_excel_vcra(
            str(caminho),
            modificacao,
            tamanho,
            "Posicoes"
        ).copy()

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
