from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

import utils

# --- PAGE CONFIG ---
st.set_page_config(page_title="B3 Portfolio Master", layout="wide", page_icon="💰")


@st.cache_data
def load_and_process_files(uploaded_files):
    all_data = []
    for file in uploaded_files:
        df = pd.read_excel(file)
        if 'Data' not in df.columns:
            for i, row in df.iterrows():
                if 'Data' in [str(v) for v in row.values]:
                    df.columns = df.iloc[i]
                    df = df.iloc[i + 1:].reset_index(drop=True)
                    break

        temp = pd.DataFrame()
        temp['date'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        temp['type'] = df['Movimentação'].apply(utils.map_operation_type)
        temp['ticker'] = df['Produto'].apply(utils.clean_ticker)
        temp['raw_product'] = df['Produto']
        temp['quantity'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
        temp['operation_value'] = pd.to_numeric(df['Valor da Operação'], errors='coerce').fillna(0)
        all_data.append(temp.dropna(subset=['date', 'type']))

    return pd.concat(all_data).sort_values(by='date') if all_data else pd.DataFrame()


# --- MAIN UI ---
st.sidebar.title("Settings")
uploaded_files = st.sidebar.file_uploader("Upload B3 Statements (XLSX)", type=['xlsx'], accept_multiple_files=True)

if uploaded_files:
    raw_df = load_and_process_files(uploaded_files)
    if not raw_df.empty:
        portfolio = utils.calculate_portfolio(raw_df)
        prices = utils.fetch_market_prices(portfolio['Ticker'].tolist())

        # Market Logic
        portfolio['Current Price'] = portfolio['Ticker'].map(prices).fillna(portfolio['Avg Price'])
        portfolio['Market Value'] = portfolio['Current Price'] * portfolio['Quantity']
        portfolio['P&L'] = portfolio['Market Value'] - portfolio['Total Invested']
        portfolio['Yield (%)'] = (portfolio['P&L'] / portfolio['Total Invested'] * 100)

        # KPIs using scalar values
        total_cost = float(portfolio['Total Invested'].to_numpy().sum())
        total_market = float(portfolio['Market Value'].to_numpy().sum())
        total_earnings = float(portfolio['Earnings Received'].to_numpy().sum())
        performance = ((total_market / total_cost) - 1) * 100 if total_cost > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Invested", f"R$ {total_cost:,.2f}")
        c2.metric("Market Value", f"R$ {total_market:,.2f}", f"{performance:.2f}%")
        c3.metric("Gross P&L", f"R$ {(total_market - total_cost):,.2f}")
        c4.metric("Total Earnings", f"R$ {total_earnings:,.2f}")

        st.divider()

        # Visuals
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Allocation by Category")
            fig_pie = px.pie(portfolio, values='Market Value', names='Category', hole=0.4)
            fig_pie.update_traces(hovertemplate="R$ %{value:,.2f}")
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b:
            st.subheader("Top Earnings by Ticker")
            fig_bar = px.bar(portfolio.sort_values('Earnings Received', ascending=False).head(10),
                             x='Ticker', y='Earnings Received', text_auto=False)
            fig_bar.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.2f")
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Detailed Position")
        st.dataframe(
            portfolio.style.format({
                'Avg Price': 'R$ {:.2f}', 'Current Price': 'R$ {:.2f}',
                'Total Invested': 'R$ {:.2f}', 'Market Value': 'R$ {:.2f}',
                'P&L': 'R$ {:.2f}', 'Earnings Received': 'R$ {:.2f}',
                'Quantity': '{:,.2f}', 'Yield (%)': '{:.2f}%'
            }).map(lambda x: 'color: red' if str(x).startswith('-') else 'color: green', subset=['P&L', 'Yield (%)']),
            use_container_width=True, hide_index=True
        )

        # Export
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            portfolio.to_excel(writer, index=False, sheet_name='Portfolio')
        st.download_button("📥 Download Consolidated Excel", buffer, "B3_Portfolio_Summary.xlsx")
else:
    st.info("💡 Welcome! Please upload your B3 statement files in the sidebar.")
