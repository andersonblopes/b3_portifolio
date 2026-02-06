# 💰 B3 Portfolio Master (B3 Master)

Dashboard financeiro em **Streamlit** para consolidar extratos da **B3 (Bolsa do Brasil)** e acompanhar evolução de patrimônio,
proventos e alocação de ativos.

> **Privacidade:** os arquivos `.xlsx` são processados localmente.
> **Internet:** o app pode consultar **Yahoo Finance (yfinance)** para cotação de ativos e câmbio **USD/BRL**.

## 🚀 Features

- **Multi-arquivo**: envie vários extratos `.xlsx` de uma vez.
- **Moeda**: alternar entre **BRL (R$)** e **USD ($)**.
- **Idiomas**: **Português (Brasil)** e **English**.
- **Dados de mercado (opcional)**: integração com Yahoo Finance para preços.
- **Visualizações**:
  - Evolução de patrimônio (fluxo acumulado)
  - Proventos por mês
  - Alocação por tipo de ativo e por instituição

## 🧾 Formato dos arquivos (input esperado)

O app detecta automaticamente o tipo de planilha pelos cabeçalhos:

- **Negociação**: precisa conter a coluna **`Data do Negócio`**
- **Movimentação**: precisa conter as colunas **`Data`** e **`Movimentação`**

Se o layout do arquivo exportado mudar, pode ser necessário ajustar o parser em `src/utils.py`.

## 🛠️ Estrutura do projeto

```text
b3_importer/
├── src/
│   ├── app.py          # UI (Streamlit)
│   ├── utils.py        # Parsing + regras financeiras + mercado (yfinance)
│   ├── tables.py       # Tabelas
│   ├── charts.py       # Gráficos (Plotly)
│   └── langs.py        # Textos/i18n
├── setup.sh            # Setup e execução (macOS/Linux)
├── requirements.txt
└── .gitignore
```

## ⚙️ Instalação e execução

### Pré-requisitos

- Python **3.9+**

### Opção A — macOS/Linux (script)

```bash
chmod +x setup.sh
./setup.sh
```

### Opção B — manual (macOS/Linux/Windows)

```bash
python -m venv venv
# macOS/Linux:
./venv/bin/pip install -U pip
./venv/bin/pip install -r requirements.txt
./venv/bin/streamlit run src/app.py

# Windows (PowerShell):
# .\venv\Scripts\pip install -U pip
# .\venv\Scripts\pip install -r requirements.txt
# .\venv\Scripts\streamlit run src\app.py
```

Depois abra: **http://127.0.0.1:8501**

## ✅ Como testar (manual)

1) Abra o app no browser
2) Faça upload de 1+ arquivos `.xlsx` (Negociação e/ou Movimentação)
3) Valide:
- KPIs: total investido, valor de mercado, PnL, proventos
- Aba **Visuals**: evolução e alocação
- Aba **Data**: tabelas por tipo de ativo
- Aba **Earnings** (se houver proventos)
4) Clique **Refresh Market Prices** e verifique o status (✅/⚠️)
5) Clique **Clear All Data** para limpar a sessão

## 🧯 Troubleshooting

- **Nada aparece após o upload**: confira se a planilha possui as colunas esperadas (ver seção “Formato dos arquivos”).
- **Cotações/câmbio não atualizam**: pode ser instabilidade/limite do Yahoo Finance. Tente novamente ou use o app sem refresh.
- **Erros ao ler XLSX**: atualize dependências e garanta que o arquivo não está corrompido.

## 🛡️ Privacidade

- Não usa banco de dados.
- Os dados ficam em memória de sessão do Streamlit.
- Ao fechar a aba (ou usar **Clear All Data**), você elimina os dados carregados.

## 🗺️ Roadmap (ideias)

- Modo offline (sem consultas ao Yahoo Finance)
- Testes automatizados para parsing e regras de cálculo
- Melhorias no parser para suportar mais variações de export da B3
- Export consolidado (Excel) mais completo

## 📄 License

Projeto para uso pessoal e acompanhamento de portfólio.

---

Criado por Anderson Lopes
