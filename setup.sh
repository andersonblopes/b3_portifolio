#!/bin/bash

# Force the script to run from the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# shellcheck disable=SC2164
cd "$SCRIPT_DIR"

# --- CONFIGURATION ---
APP_PATH="src/app.py"
VENV_NAME="venv"

echo "🚀 Starting B3 Portfolio Master Setup..."

# 1. Check for Virtual Environment
if [ ! -d "$VENV_NAME" ]; then
    echo "📦 Creating Virtual Environment..."
    python3 -m venv $VENV_NAME
fi

# 2. Activate Virtual Environment
source $VENV_NAME/bin/activate

# 3. Install/Update Dependencies (Including Watchdog)
echo "📥 Syncing dependencies..."
pip install --upgrade pip
pip install streamlit pandas yfinance plotly openpyxl matplotlib watchdog

# 4. Final Path Check and Run
if [ -f "$APP_PATH" ]; then
    echo "✨ Dashboard optimized with Watchdog. Launching..."
    streamlit run "$APP_PATH"
else
    echo "❌ Error: Cannot find $APP_PATH"
    echo "Please ensure you are running this from the b3_importer root."
fi
