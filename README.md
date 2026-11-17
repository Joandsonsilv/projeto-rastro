# RASTRO

Sistema de Rastreamento de Ativos, Saldos, Termos e Registros Operacionais.

## Requisitos
- Python 3.10 ou superior
- pip

## Instalação
No terminal, dentro da pasta RASTRO:

```bash
python -m venv .venv
```

Windows:
```bash
.venv\\Scripts\\activate
```

Linux/macOS:
```bash
source .venv/bin/activate
```

Instale as dependências:
```bash
pip install -r requirements.txt
```

Execute:
```bash
streamlit run app.py
```

## Estrutura
- `app.py`: inicialização e navegação.
- `data/`: planilhas de origem LZ e XZ.
- `modules/dados.py`: leitura e padronização.
- `modules/filtros.py`: consulta e filtros.
- `modules/indicadores.py`: dashboard, pendências e bases.
- `modules/validacoes.py`: identificação de inconsistências.
- `modules/exportacao.py`: exportação Excel e resumo.
- `modules/componentes.py`: identidade visual e menu.

## Observações sobre os dados
As planilhas são mantidas sem alteração. Os dados de cartas, protocolos, histórico e auditoria não estão presentes nas fontes fornecidas; por isso, essas áreas são sinalizadas como indisponíveis ou reservadas para integração futura.
