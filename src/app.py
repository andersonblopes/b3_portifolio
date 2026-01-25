import streamlit as st

import charts
import utils
from langs import LANGUAGES

st.set_page_config(page_title="B3 Custody Master", layout="wide", page_icon="📈")

# --- SIDEBAR ---
lang_choice = st.sidebar.selectbox("🌐 Idioma", ["Português (Brasil)", "English"])
texts = LANGUAGES[lang_choice]
currency_choice = st.sidebar.radio(texts['currency_label'], ["BRL (R$)", "USD ($)"])
rate = utils.get_exchange_rate()
st.sidebar.metric(label=texts['exchange_rate_msg'], value=f"R$ {rate:.2f}")

is_usd = currency_choice == "USD ($)"
sym, factor = ("$", 1 / rate) if is_usd else ("R$", 1.0)


# Função de Formatação Regional (KPIs e Tabela)
def fmt_reg(v):
    # Formato: 1234.56 (USD) ou 1234,56 (BRL) - Sem separador de milhar
    return f"{sym} {v:.2f}".replace('.', ',' if not is_usd else '.')


st.sidebar.divider()
uploaded_files = st.sidebar.file_uploader(texts['upload_msg'], type=['xlsx'], accept_multiple_files=True)

# --- MAIN ---
if uploaded_files:
    raw_df = utils.load_and_process_files(uploaded_files)
    if not raw_df.empty:
        portfolio = utils.calculate_portfolio(raw_df)
        prices = utils.fetch_market_prices(portfolio['ticker'].unique().tolist())

        # Merge Preços e Detecção de Status
        res = portfolio['ticker'].apply(
            lambda t: (prices.get(t, {}).get('p', 0) * factor, "✅" if prices.get(t, {}).get('live') else "⚠️"))
        portfolio['p_atual'] = [
            x[0] if x[0] > 0 else portfolio.loc[portfolio['ticker'] == t, 'avg_price'].values[0] * factor for t, x in
            zip(portfolio['ticker'], res)]
        portfolio['status'] = [x[1] for x in res]

        # Financeiro e Conversão
        for c in ['avg_price', 'total_cost']: portfolio[c] *= factor
        portfolio['v_mercado'] = portfolio['p_atual'] * portfolio['qty']
        portfolio['pnl'] = portfolio['v_mercado'] - portfolio['total_cost']
        portfolio['yield'] = (portfolio['pnl'] / portfolio['total_cost'] * 100)

        # KPIs (Totalizadores)
        inv, mkt = portfolio['total_cost'].sum(), portfolio['v_mercado'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric(texts['total_invested'], fmt_reg(inv))
        c2.metric(texts['market_value'], fmt_reg(mkt), f"{(mkt / inv - 1) * 100:.2f}%")
        c3.metric(texts['gross_pnl'], fmt_reg(mkt - inv))

        # --- ABAS ---
        tab_vis, tab_data = st.tabs([f"📊 {texts['tab_visuals']}", f"📝 {texts['tab_data']}"])

        with tab_vis:
            col_left, col_right = st.columns(2)
            with col_left:
                ev_df = utils.calculate_evolution(raw_df, factor)
                st.plotly_chart(charts.plot_evolution(ev_df, sym, is_usd, texts['chart_evolution']),
                                use_container_width=True)
            with col_right:
                st.plotly_chart(
                    charts.plot_allocation(portfolio, 'asset_type', 'v_mercado', is_usd, texts['chart_allocation']),
                    use_container_width=True)

        with tab_data:
            display_df = portfolio.rename(columns={
                'ticker': texts['col_ticker'], 'asset_type': texts['col_type'],
                'qty': texts['col_qty'], 'avg_price': texts['col_avg_price'],
                'total_cost': texts['col_total_cost'], 'p_atual': texts['col_curr_price'],
                'v_mercado': texts['market_value'], 'pnl': texts['col_pnl'],
                'yield': texts['col_yield'], 'status': texts['col_status']
            })

            # Reordenar colunas
            cols = [texts['col_ticker'], texts['col_type'], texts['col_qty'], texts['col_avg_price'],
                    texts['col_total_cost'], texts['col_curr_price'], texts['market_value'],
                    texts['col_pnl'], texts['col_yield'], texts['col_status']]
            display_df = display_df[cols]

            # Estilização da Tabela com Gradiente e Formatação Regional
            st.dataframe(
                display_df.style.format({
                    texts['col_qty']: "{:.0f}",
                    texts['col_yield']: "{:.2f}%",
                    texts['col_avg_price']: fmt_reg,
                    texts['col_curr_price']: fmt_reg,
                    texts['col_total_cost']: fmt_reg,
                    texts['market_value']: fmt_reg,
                    texts['col_pnl']: fmt_reg,
                }).background_gradient(subset=[texts['col_yield']], cmap='RdYlGn', vmin=-15, vmax=15),
                use_container_width=True, hide_index=True
            )
            st.caption(texts['status_legend'])
else:
    st.title("📈 B3 Custody Master")
    st.info(texts['welcome_sub'])
