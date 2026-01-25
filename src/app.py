import streamlit as st

import charts
import utils
from langs import LANGUAGES

st.set_page_config(page_title="B3 Master", layout="wide", page_icon="📈")

lang_choice = st.sidebar.selectbox("🌐 Idioma", ["Português (Brasil)", "English"])
texts = LANGUAGES[lang_choice]
currency_choice = st.sidebar.radio(texts['currency_label'], ["BRL (R$)", "USD ($)"])
rate = utils.get_exchange_rate()
st.sidebar.metric(label=texts['exchange_rate_msg'], value=f"R$ {rate:.2f}")

is_usd = currency_choice == "USD ($)"
sym, factor = ("$", 1 / rate) if is_usd else ("R$", 1.0)


def fmt_reg(v): return f"{sym} {v:.2f}".replace('.', ',' if not is_usd else '.')


uploaded_files = st.sidebar.file_uploader(texts['upload_msg'], type=['xlsx'], accept_multiple_files=True)

if uploaded_files:
    raw_df = utils.load_and_process_files(uploaded_files)
    if not raw_df.empty:
        portfolio = utils.calculate_portfolio(raw_df)
        has_earnings = not raw_df[raw_df['type'] == 'EARNINGS'].empty
        portfolio_main = portfolio[portfolio['qty'] > 0].copy()

        prices = utils.fetch_market_prices(portfolio_main['ticker'].unique().tolist())


        def map_info(t):
            p = prices.get(t, {}).get('p')
            return (p * factor, "✅") if p else (None, "⚠️")


        res = portfolio_main['ticker'].apply(map_info)
        portfolio_main['p_atual'] = [x[0] for x in res]
        portfolio_main['status'] = [x[1] for x in res]
        portfolio_main['p_atual'] = portfolio_main['p_atual'].fillna(portfolio_main['avg_price'] * factor)

        for c in ['avg_price', 'total_cost', 'earnings']: portfolio_main[c] *= factor
        portfolio_main['v_mercado'] = portfolio_main['p_atual'] * portfolio_main['qty']
        portfolio_main['pnl'] = portfolio_main['v_mercado'] - portfolio_main['total_cost']
        portfolio_main['yield'] = (portfolio_main['pnl'] / portfolio_main['total_cost'] * 100)

        # KPIs
        inv, mkt, earn = portfolio_main['total_cost'].sum(), portfolio_main['v_mercado'].sum(), portfolio_main[
            'earnings'].sum()
        k1, k2, k3, k4 = st.columns(4)
        k1.metric(texts['total_invested'], fmt_reg(inv))
        k2.metric(texts['market_value'], fmt_reg(mkt), f"{(mkt / inv - 1) * 100:.2f}%")
        k3.metric(texts['gross_pnl'], fmt_reg(mkt - inv))
        if has_earnings: k4.metric(texts['total_earnings'], fmt_reg(earn))

        # ABAS
        t_titles = [f"📊 {texts['tab_visuals']}", f"📝 {texts['tab_data']}"]
        if has_earnings: t_titles.append(f"💰 {texts['tab_earnings']}")
        tabs = st.tabs(t_titles)

        with tabs[0]:  # Dashboard
            c_left, c_right = st.columns(2)
            ev_df = utils.calculate_evolution(raw_df, factor)
            if not ev_df.empty:
                c_left.plotly_chart(charts.plot_evolution(ev_df, sym, is_usd, texts['chart_evolution']),
                                    use_container_width=True)
            c_right.plotly_chart(
                charts.plot_allocation(portfolio_main, 'asset_type', 'v_mercado', is_usd, texts['chart_allocation']),
                use_container_width=True)

        with tabs[1]:  # Data Lab
            st.dataframe(portfolio_main.rename(
                columns={'ticker': texts['col_ticker'], 'asset_type': texts['col_type'], 'qty': texts['col_qty'],
                         'avg_price': texts['col_avg_price'], 'total_cost': texts['col_total_cost'],
                         'p_atual': texts['col_curr_price'], 'v_mercado': texts['market_value'],
                         'pnl': texts['col_pnl'], 'yield': texts['col_yield'], 'status': texts['col_status'],
                         'earnings': texts['col_earnings']}).style.format(
                {texts['col_qty']: "{:.0f}", texts['col_yield']: "{:.2f}%", texts['col_avg_price']: fmt_reg,
                 texts['col_curr_price']: fmt_reg, texts['col_total_cost']: fmt_reg, texts['market_value']: fmt_reg,
                 texts['col_pnl']: fmt_reg, texts['col_earnings']: fmt_reg}).background_gradient(
                subset=[texts['col_yield']], cmap='RdYlGn', vmin=-15, vmax=15), use_container_width=True,
                hide_index=True)

        if has_earnings:
            with tabs[2]:
                earn_df = utils.calculate_monthly_earnings(raw_df, factor)
                st.plotly_chart(charts.plot_earnings_evolution(earn_df, sym, is_usd, texts['tab_earnings']),
                                use_container_width=True)
else:
    st.info(texts['welcome_sub'])
