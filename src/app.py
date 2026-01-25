import streamlit as st

import charts
import utils
from langs import LANGUAGES

st.set_page_config(page_title="B3 Master", layout="wide", page_icon="📈")

if 'raw_df' not in st.session_state: st.session_state.raw_df = None

lang_choice = st.sidebar.selectbox("🌐 Idioma", ["Português (Brasil)", "English"])
texts = LANGUAGES[lang_choice];
currency_choice = st.sidebar.radio(texts['currency_label'], ["BRL (R$)", "USD ($)"])
rate = utils.get_exchange_rate();
st.sidebar.metric(label=texts['exchange_rate_msg'], value=f"R$ {rate:.2f}")
is_usd = currency_choice == "USD ($)";
sym, factor = ("$", 1 / rate) if is_usd else ("R$", 1.0)


def fmt_reg(v): return f"{sym} {v:.2f}".replace('.', ',' if not is_usd else '.')


uploaded_files = st.sidebar.file_uploader(texts['upload_msg'], type=['xlsx'], accept_multiple_files=True)
if uploaded_files: st.session_state.raw_df = utils.load_and_process_files(uploaded_files)

if st.session_state.raw_df is not None:
    raw_df = st.session_state.raw_df
    portfolio = utils.calculate_portfolio(raw_df)
    has_earnings = not raw_df[raw_df['type'] == 'EARNINGS'].empty
    portfolio_main = portfolio[portfolio['qty'] > 0].copy()

    prices = utils.fetch_market_prices(portfolio_main['ticker'].unique().tolist())
    res = portfolio_main['ticker'].apply(
        lambda t: (prices.get(t, {}).get('p', 0) * factor, "✅" if prices.get(t, {}).get('live') else "⚠️"))
    portfolio_main['p_atual'] = [
        x[0] if x[0] > 0 else portfolio_main.loc[portfolio_main['ticker'] == t, 'avg_price'].values[0] * factor for t, x
        in zip(portfolio_main['ticker'], res)]
    portfolio_main['status'] = [x[1] for x in res]

    for c in ['avg_price', 'total_cost', 'earnings']: portfolio_main[c] *= factor
    portfolio_main['v_mercado'] = portfolio_main['p_atual'] * portfolio_main['qty']
    portfolio_main['pnl'] = portfolio_main['v_mercado'] - portfolio_main['total_cost']
    portfolio_main['yield'] = (portfolio_main['pnl'] / portfolio_main['total_cost'] * 100)

    # KPIs
    inv, mkt, earn = portfolio_main['total_cost'].sum(), portfolio_main['v_mercado'].sum(), portfolio_main[
        'earnings'].sum()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(texts['total_invested'], fmt_reg(inv));
    k2.metric(texts['market_value'], fmt_reg(mkt), f"{(mkt / inv - 1) * 100:.2f}%")
    k3.metric(texts['gross_pnl'], fmt_reg(mkt - inv));
    if has_earnings: k4.metric(texts['total_earnings'], fmt_reg(earn))

    tabs = st.tabs(
        [f"📊 {texts['tab_visuals']}", f"📝 {texts['tab_data']}", f"💰 {texts['tab_earnings']}"] if has_earnings else [
            f"📊 {texts['tab_visuals']}", f"📝 {texts['tab_data']}"])

    with tabs[0]:  # Dashboard Global - TODOS OS GRÁFICOS AQUI
        # LINHA 1: Evolução Global e Alocação por Tipo
        c1, c2 = st.columns(2)
        df_ev = raw_df[raw_df['source'] == 'NEG'].copy()
        if not df_ev.empty:
            ev = df_ev.sort_values('date').groupby('date')['val'].sum().cumsum().reset_index();
            ev['val'] *= factor
            c1.plotly_chart(
                charts.plot_evolution(ev.rename(columns={'val': 'flow'}), sym, is_usd, texts['chart_evolution']),
                use_container_width=True)
        c2.plotly_chart(
            charts.plot_allocation(portfolio_main, 'asset_type', 'v_mercado', is_usd, texts['chart_allocation']),
            use_container_width=True)

        # LINHA 2: Patrimônio por Instituição e Evolução da Renda
        st.divider()
        c3, c4 = st.columns(2)
        # Patrimônio por Inst
        df_inst = raw_df[raw_df['source'] == 'NEG'].groupby('inst')['val'].sum().reset_index();
        df_inst['val'] *= factor
        c3.plotly_chart(charts.plot_allocation(df_inst, 'inst', 'val', is_usd, texts['chart_asset_inst']),
                        use_container_width=True)

        if has_earnings:
            earn_raw = raw_df[raw_df['type'] == 'EARNINGS'].copy();
            earn_raw['val'] *= factor
            # Renda Mensal
            df_m = earn_raw.copy();
            df_m['month_year'] = df_m['date'].dt.strftime('%Y-%m')
            res_m = df_m.groupby('month_year')['val'].sum().reset_index().sort_values('month_year')
            c4.plotly_chart(charts.plot_earnings_evolution(res_m, sym, is_usd, texts['chart_earn_monthly']),
                            use_container_width=True)

            # LINHA 3: Renda por Instituição e Maiores Pagadores
            st.divider()
            c5, c6 = st.columns(2)
            # Renda por Inst
            earn_inst = earn_raw.groupby('inst')['val'].sum().reset_index()
            c5.plotly_chart(charts.plot_allocation(earn_inst, 'inst', 'val', is_usd, texts['chart_earn_inst']),
                            use_container_width=True)
            # Ranking Maiores Pagadores
            earn_ticker = earn_raw.groupby('ticker')['val'].sum().reset_index()
            c6.plotly_chart(charts.plot_bar_earnings_horizontal(earn_ticker, 'ticker', 'val', sym, is_usd,
                                                                texts['chart_earn_ticker']), use_container_width=True)

    with tabs[1]:  # Data Lab
        st.dataframe(portfolio_main.rename(
            columns={'ticker': texts['col_ticker'], 'asset_type': texts['col_type'], 'qty': texts['col_qty'],
                     'avg_price': texts['col_avg_price'], 'total_cost': texts['col_total_cost'],
                     'p_atual': texts['col_curr_price'], 'v_mercado': texts['market_value'], 'pnl': texts['col_pnl'],
                     'yield': texts['col_yield'], 'status': texts['col_status'],
                     'earnings': texts['col_earnings']}).style.format(
            {texts['col_qty']: "{:.0f}", texts['col_yield']: "{:.2f}%", texts['col_avg_price']: fmt_reg,
             texts['col_curr_price']: fmt_reg, texts['col_total_cost']: fmt_reg, texts['market_value']: fmt_reg,
             texts['col_pnl']: fmt_reg, texts['col_earnings']: fmt_reg}).background_gradient(
            subset=[texts['col_yield']], cmap='RdYlGn', vmin=-15, vmax=15), use_container_width=True, hide_index=True)

    if has_earnings:
        with tabs[2]:  # Aba Proventos Detalhada
            earn_raw = raw_df[raw_df['type'] == 'EARNINGS'].copy();
            earn_raw['val'] *= factor
            r1_c1, r1_c2 = st.columns(2)
            with r1_c1:
                e_type = earn_raw.groupby('sub_type')['val'].sum().reset_index()
                st.plotly_chart(charts.plot_allocation(e_type, 'sub_type', 'val', is_usd, texts['chart_earn_type']),
                                use_container_width=True)
            with r1_c2:
                earn_raw['at_type'] = earn_raw['ticker'].apply(utils.detect_asset_type)
                e_asset = earn_raw.groupby('at_type')['val'].sum().reset_index()
                st.plotly_chart(
                    charts.plot_allocation(e_asset, 'at_type', 'val', is_usd, texts['chart_earn_asset_type']),
                    use_container_width=True)

            st.divider();
            st.subheader(texts['earnings_audit_title'])
            audit_df = earn_raw.rename(
                columns={'date': texts['col_date'], 'ticker': texts['col_ticker'], 'val': texts['col_earnings'],
                         'sub_type': texts['col_earning_type'], 'inst': texts['col_inst']})
            st.dataframe(audit_df[[texts['col_date'], texts['col_ticker'], texts['col_inst'], texts['col_earning_type'],
                                   texts['col_earnings']]].style.format(
                {texts['col_date']: lambda x: x.strftime('%d/%m/%Y'), texts['col_earnings']: fmt_reg}),
                use_container_width=True, hide_index=True)
else:
    st.info(texts['welcome_sub'])
