# B3 Portfolio Master 💰

A professional-grade Python dashboard built with **Streamlit** to consolidate B3 (Brazilian Stock Exchange) investment
statements. It provides real-time portfolio tracking, dividend analysis, and automated P&L calculations.

## 🚀 Key Features

- **Automated Ingestion**: Seamlessly processes B3 `.xlsx` statement files.
- **Smart Categorization**: Automatically detects Stocks, REITs (FIIs), BDRs, ETFs, Treasury Bonds, and Fixed Income.
- **Real-time Market Data**: Integrates with Yahoo Finance API for live price updates.
- **Granular P&L Tracking**: Calculates Average Price, Market Value, and Yield-on-Cost.
- **Privacy Focused**: No data is sent to external databases; everything is processed locally in memory.
- **Export Capabilities**: Generate consolidated reports in Excel format.

## 🛠️ Project Structure

```text
b3-importer/
├── src/
│   ├── app.py          # User Interface (Streamlit)
│   └── utils.py        # Business Logic & Data Processing
├── .gitignore          # Git exclusion rules (IDE, Data, Cache)
├── requirements.txt    # Project dependencies
└── README.md           # Documentation

```

## ⚙️ Installation & Setup

- Prerequisites
    - Python 3.9 or higher
    - Pip (Python package manager)

1. Clone the project and install dependencies

```bash
      pip install -r requirements.txt
```

2. Run the application

```bash
      streamlit run src/app.py
```

3. IDE Setup (IntelliJ / PyCharm)

- Open the project in IntelliJ.
- Mark the src folder as Sources Root.
- Create a Python Run Configuration:
    - Module name: streamlit
    - Parameters: run src/app.py
    - Working directory: [project_root]

## 📊 How to Use

1. Log in to the B3 Investor Portal.
2. Export your Movements history in .xlsx format.
3. Upload the file(s) to the dashboard sidebar.
4. Set your dividend goals and analyze your portfolio performance.

## 🛡️ Security & Privacy

The .gitignore is pre-configured to ensure that your private financial data (stored in the data/ folder or root) is
never committed to a version control system.

## 📄 License

This project is for personal use and portfolio tracking.

#

Created by Anderson Lopes
