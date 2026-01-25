# 💰 B3 Portfolio Master

A sophisticated, multi-language financial dashboard built with Streamlit to consolidate B3 (Brazilian Stock Exchange)
statements. This tool provides deep insights into patrimony evolution, passive income flow, and asset allocation.

## 🚀 Features

- **Multi-File Processing**: Upload multiple B3 Excel statements simultaneously.
- **Bi-Currency Support**: Toggle between **BRL (R$)** and **USD ($)** with real-time exchange rate updates.
- **Internationalization**: Full support for **English** and **Português (Brasil)**.
- **Live Market Data**: Integrated with Yahoo Finance for real-time stock and REIT prices.
- **Visual Analytics**:
    - **Patrimony Evolution**: Track your invested capital journey.
    - **Passive Income Flow**: Monthly bar charts with trend averages.
    - **Sunburst Allocation**: Hierarchical view of categories and specific assets.
- **Security First**: 100% local processing. Your financial data never leaves your machine.

## 🛠️ Project Structure

The project follows a clean, modular architecture:

```text
b3_importer/
├── src/
│   ├── charts.py       # Visualization components
│   ├── tables.py       # Data tables and summaries
│   ├── app.py          # Dashboard UI and layout
│   ├── utils.py        # Financial logic and API integrations
│   └── langs.py        # Internationalization dictionaries
├── setup.sh            # Automated setup and launch script
├── .gitignore          # Security and environment filters
└── requirements.txt    # Project dependencies
```

## ⚙️ Installation & Setup

### Prerequisites

    - Python 3.9 or higher
    - macOS/Linux (for the .sh script)

### Quick Start

1. Clone the project to your local machine.
2. Open your terminal in the project root.
3. Run the setup script:

```bash
    chmod +x setup.sh
    ./setup.sh
```

The script will automatically create a virtual environment, install dependencies (including watchdog for performance),
and launch the dashboard in your browser.

## 📈 Usage

1. Upload: Export your statements from the B3 Investor Portal as .xlsx and upload them in the sidebar.
2. Analyze: Use the sidebar to switch languages or currencies.
3. Export: Click the download button to get a consolidated Excel report of your processed data.

## 🛡️ Privacy

This application is designed with privacy in mind. It does not use a database or cloud storage. All data is stored in
temporary session memory and is wiped when the browser tab is closed or the "Reset Session" button is clicked.

## 📄 License

This project is for personal use and portfolio tracking.

#

Created by Anderson Lopes
