# 💰 B3 Portfolio Master (B3 Master)

A **Streamlit** financial dashboard to consolidate **B3 (Brazilian Stock Exchange)** statements and track portfolio
performance, passive income and asset allocation.

> **Privacy:** your `.xlsx` files are processed locally.
> **Internet:** the app makes read-only calls to **Yahoo Finance** (`yfinance`, no token) for live market prices,
> FX rates (**USD/BRL**, **EUR/BRL**), split history and historical close prices, and to **brapi.dev**
> (no token, public icon CDN) for ticker logo images.

## 🚀 Features

- **Multi-file upload**: upload multiple B3 `.xlsx` statements at once.
- **Multi-currency**: toggle between **BRL (R$)**, **USD ($)** and **EUR (€)**.
- **Internationalization**: **English**, **Português**, **Español** and **Français**.
- **Market data (optional)**: live prices, FX rates and split history via Yahoo Finance (no token); ticker logos via brapi.dev.
- **Visual analytics**:
  - Portfolio evolution (cumulative flow)
  - Monthly passive income
  - Allocation by asset type and by broker/institution

## 🧾 Expected input files

The app auto-detects the statement type based on column headers:

- **Trading / Negotiation** statement: must contain **`Data do Negócio`**
- **Movements** statement: must contain **`Data`** and **`Movimentação`**

If B3 changes the export layout, you may need to adjust the parser in `src/utils.py`.

## 🛠️ Project structure

```text
b3_importer/
├── src/
│   ├── app.py          # Streamlit UI
│   ├── utils.py        # Parsing + financial rules + market data (yfinance)
│   ├── tables.py       # Tables
│   ├── charts.py       # Charts (Plotly)
│   └── langs.py        # i18n dictionaries
├── setup.sh            # Setup & run script (macOS/Linux)
├── requirements.txt
├── requirements-dev.txt
├── tests/            # Unit tests (pytest)
└── .gitignore
```

## ⚙️ Installation & run

### Prerequisites

- Python **3.9+**

### Option A — macOS/Linux (script)

```bash
chmod +x setup.sh
./setup.sh
```

### Option B — manual (macOS/Linux/Windows)

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

Then open: **http://127.0.0.1:8501**

## ✅ Testing

### Manual test

1) Open the app in your browser
2) Upload one or more `.xlsx` files (Trading and/or Movements)
3) Validate:
- KPIs: invested amount, market value, PnL, earnings
- **Visuals** tab: evolution and allocation
- **Data** tab: tables by asset type
- **Earnings** tab (if earnings are present)
4) Click **Refresh Market Prices** and check the status indicators (✅/⚠️)
5) Click **Clear All Data** to reset the session

### Unit tests

The project includes **pytest** unit tests for the parsing/business rules and helpers.

Run:

```bash
# install dev dependencies
./venv/bin/pip install -r requirements-dev.txt

# run unit tests
./venv/bin/python -m pytest
```

### Coverage

```bash
./venv/bin/python -m pytest --cov=src --cov-report=term-missing
```

## 🧯 Troubleshooting

- **Nothing shows up after upload**: verify the file contains the expected columns (see “Expected input files”).
- **Prices / FX do not refresh**: Yahoo Finance may be rate-limiting or temporarily unreachable; click **Refresh Market Prices** again after a moment, or check `logs/app.log` for the underlying error. FX falls back to fixed rates (USD 5.45, EUR 5.90) if the fetch fails.
- **Language or currency resets after reload**: the app persists these settings in the URL (query params like `?lang=pt&cur=EUR`).
- **XLSX read errors**: upgrade dependencies and make sure the file is not corrupted.

## 🛡️ Privacy

- No database.
- Data stays in Streamlit session memory.
- Closing the tab (or clicking **Clear All Data**) removes the loaded data.

## 🗺️ Roadmap (ideas)

- Offline mode (no Yahoo Finance calls)
- Automated tests for parsing and calculation rules
- Improve parsers to support more B3 export variations
- Better consolidated Excel export

## 📚 Deep-dive docs

Scoped Software Design Documents live in `docs/` (see `docs/README.md` for
the index) — architecture, the cost-basis engine, parsing rules, market
data integration, the position analysis/advisory engine, UI internals,
testing conventions, a B3/CVM glossary, and known limitations.

## 📄 License

Personal use / portfolio tracking.

---

Created by Anderson Lopes
