import streamlit as st

import charts
import tables
import utils
from langs import LANGUAGES

st.set_page_config(page_title="B3 Master", layout="wide", page_icon="📈")

# Initialization of Session State
if 'raw_df' not in st.session_state:
    st.session_state.raw_df = None
if 'import_stats' not in st.session_state:
    st.session_state.import_stats = None

# Sidebar Controls
lang_choice = st.sidebar.selectbox("🌐 Idioma", ["Português (Brasil)", "English"])
texts = LANGUAGES[lang_choice]

st.sidebar.divider()
currency_choice = st.sidebar.radio(texts['currency_label'], ["BRL (R$)", "USD ($)"])

# Market refresh (manual + optional auto)
from streamlit_autorefresh import st_autorefresh

# Keep the label short to avoid wrapping in the sidebar.
auto_refresh = st.sidebar.toggle("⏱️ Auto refresh", value=False, help="Auto refresh market prices on a timer")

refresh_count = None
refresh_interval_ms = None

if auto_refresh:
    refresh_interval_label = st.sidebar.selectbox(
        "Refresh interval",
        ["30s", "1m", "5m"],
        index=1,
        help="How often to refresh market prices and FX rate",
    )
    refresh_interval_ms = {"30s": 30_000, "1m": 60_000, "5m": 300_000}[refresh_interval_label]
    refresh_count = st_autorefresh(interval=refresh_interval_ms, key="auto_market_refresh")

# Sidebar CSS: prevent toggle labels from wrapping.
st.sidebar.markdown(
    """
<style>
/* Avoid wrapped toggle labels in the sidebar */
section[data-testid="stSidebar"] .stToggle label p { white-space: nowrap; }
</style>
""",
    unsafe_allow_html=True,
)

# Market Refresh Logic
manual_refresh = st.sidebar.button("🔄 Refresh Market Prices")

# Clear caches when the user clicks the button OR when the autorefresh ticks.
# st_autorefresh returns an incrementing counter; use it to detect actual ticks.
if 'last_auto_refresh_count' not in st.session_state:
    st.session_state.last_auto_refresh_count = None

auto_tick = (
    auto_refresh
    and refresh_count is not None
    and refresh_count != st.session_state.last_auto_refresh_count
)

if manual_refresh or auto_tick:
    utils.fetch_market_prices.clear()  # Clears the cache for prices
    utils.get_exchange_rate.clear()  # Clears the cache for USD rate
    if auto_tick:
        st.session_state.last_auto_refresh_count = refresh_count
    st.toast("Updating live market data...", icon="⏳")

rate = utils.get_exchange_rate()
st.sidebar.metric(label=texts['exchange_rate_msg'], value=f"R$ {rate:.2f}")

st.sidebar.divider()
uploaded_files = st.sidebar.file_uploader(texts['upload_msg'], type=['xlsx'], accept_multiple_files=True)

if uploaded_files:
    # Processing only occurs when new files are uploaded
    st.session_state.raw_df, st.session_state.import_stats = utils.load_and_process_files(uploaded_files)

# Import summary
if st.session_state.import_stats is not None and not st.session_state.import_stats.empty:
    with st.sidebar.expander("📄 Import summary", expanded=False):
        st.dataframe(st.session_state.import_stats, width="stretch", hide_index=True)

# Option to clear session data
if st.sidebar.button("🗑️ Clear All Data"):
    st.session_state.raw_df = None
    st.session_state.import_stats = None
    st.rerun()

is_usd = currency_choice == "USD ($)"
sym, factor = ("$", 1 / rate) if is_usd else ("R$", 1.0)


def fmt_reg(v):
    return f"{sym} {v:.2f}".replace('.', ',' if not is_usd else '.')


PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}


# Main UI Logic
if st.session_state.raw_df is not None:
    raw_df = st.session_state.raw_df
    portfolio = utils.calculate_portfolio(raw_df)
    has_earnings = not raw_df[raw_df['type'] == 'EARNINGS'].empty
    portfolio_main = portfolio[portfolio['qty'] > 0].copy()

    # Fetch fresh prices using the cached function
    tickers = portfolio_main['ticker'].unique().tolist()
    prices = utils.fetch_market_prices(tickers)

    live_count = sum(1 for t in tickers if prices.get(t, {}).get('live'))
    if tickers and live_count < len(tickers):
        st.sidebar.warning(
            f"Yahoo Finance unavailable for {len(tickers) - live_count}/{len(tickers)} tickers. "
            "Using average price as fallback for those assets."
        )

    res = portfolio_main['ticker'].apply(
        lambda t: (prices.get(t, {}).get('p', 0) * factor, "✅" if prices.get(t, {}).get('live') else "⚠️"))

    portfolio_main['p_atual'] = [
        x[0] if x[0] > 0 else portfolio_main.loc[portfolio_main['ticker'] == t, 'avg_price'].values[0] * factor
        for t, x in zip(portfolio_main['ticker'], res)]
    portfolio_main['status'] = [x[1] for x in res]

    for c in ['avg_price', 'total_cost', 'earnings']: portfolio_main[c] *= factor
    portfolio_main['v_mercado'] = portfolio_main['p_atual'] * portfolio_main['qty']
    portfolio_main['pnl'] = portfolio_main['v_mercado'] - portfolio_main['total_cost']
    portfolio_main['yield'] = (portfolio_main['pnl'] / portfolio_main['total_cost'] * 100)
    mkt_total = portfolio_main['v_mercado'].sum()

    # KPIs
    inv_total, earn_total = portfolio_main['total_cost'].sum(), portfolio_main['earnings'].sum()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(texts['total_invested'], fmt_reg(inv_total))
    k2.metric(texts['market_value'], fmt_reg(mkt_total), f"{(mkt_total / inv_total - 1) * 100:.2f}%")
    k3.metric(texts['gross_pnl'], fmt_reg(mkt_total - inv_total))
    if has_earnings: k4.metric(texts['total_earnings'], fmt_reg(earn_total))

    tabs = st.tabs(
        [f"📊 {texts['tab_visuals']}", f"📝 {texts['tab_data']}", f"💰 {texts['tab_earnings']}"] if has_earnings else [
            f"📊 {texts['tab_visuals']}", f"📝 {texts['tab_data']}"])

    with tabs[0]:  # Dashboard Global
        c1, c2 = st.columns(2)
        df_ev = raw_df[raw_df['source'] == 'NEG'].copy()
        if not df_ev.empty:
            ev = df_ev.sort_values('date').groupby('date')['val'].sum().cumsum().reset_index()
            ev['val'] *= factor
            c1.plotly_chart(
                charts.plot_evolution(ev.rename(columns={'val': 'flow'}), sym, is_usd, texts['chart_evolution']),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )
        c2.plotly_chart(
            charts.plot_allocation(portfolio_main, 'asset_type', 'v_mercado', is_usd, texts['chart_allocation']),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )

        st.divider()
        c3, c4 = st.columns(2)
        df_inst = raw_df[raw_df['source'] == 'NEG'].groupby('inst')['val'].sum().reset_index()
        df_inst['val'] *= factor
        c3.plotly_chart(
            charts.plot_allocation(df_inst, 'inst', 'val', is_usd, texts['chart_asset_inst']),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )

        if has_earnings:
            earn_raw = raw_df[raw_df['type'] == 'EARNINGS'].copy()
            earn_raw['val'] *= factor
            res_m = earn_raw.copy()
            res_m['month_year'] = res_m['date'].dt.strftime('%Y-%m')
            res_m = res_m.groupby('month_year')['val'].sum().reset_index().sort_values('month_year')
            c4.plotly_chart(
                charts.plot_earnings_evolution(res_m, sym, is_usd, texts['chart_earn_monthly']),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

    with tabs[1]:  # Data Lab
        st.write(texts['status_legend'])
        types = sorted(portfolio_main['asset_type'].unique())
        for t in types:
            sub_df = portfolio_main[portfolio_main['asset_type'] == t].copy()
            # Sort by yield ("Red.." / "Yield") descending
            sub_df = sub_df.sort_values('yield', ascending=False)
            t_mkt = sub_df['v_mercado'].sum()
            weight = (t_mkt / mkt_total) * 100 if mkt_total > 0 else 0
            label_assets = texts['assets_count']
            title = f"📁 {t} | {len(sub_df)} {label_assets} | {fmt_reg(t_mkt)} ({weight:.2f}%)"
            with st.expander(title, expanded=True):
                tables.render_portfolio_table(sub_df, texts, fmt_reg)

    if has_earnings:
        with tabs[2]:  # Earnings
            earn_raw = raw_df[raw_df['type'] == 'EARNINGS'].copy()
            earn_raw['val'] *= factor
            r1_c1, r1_c2 = st.columns(2)
            with r1_c1:
                st.plotly_chart(
                    charts.plot_allocation(
                        earn_raw.groupby('sub_type')['val'].sum().reset_index(),
                        'sub_type',
                        'val',
                        is_usd,
                        texts['chart_earn_type'],
                    ),
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                )
            with r1_c2:
                earn_raw['at_type'] = earn_raw['ticker'].apply(utils.detect_asset_type)
                st.plotly_chart(
                    charts.plot_allocation(
                        earn_raw.groupby('at_type')['val'].sum().reset_index(),
                        'at_type',
                        'val',
                        is_usd,
                        texts['chart_earn_asset_type'],
                    ),
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                )
            st.divider()
            st.subheader(texts['earnings_audit_title'])
            tables.render_earnings_log(earn_raw, texts, fmt_reg)
else:
    # Display the Welcome guide from image_5345f4.png
    st.title("Bem-vindo ao B3 Master Portfolio")
    st.subheader("Seu painel profissional de gestão de patrimônio.")
    st.markdown("### 🚀 Guia de Início Rápido")
    st.info("1. Acesse o [Portal do Investidor B3](https://www.investidor.b3.com.br/login)")
    st.info("2. Baixe seus arquivos XLSX de **Negociação** e **Movimentação**.")
    st.info("3. Arraste todos os arquivos para a barra lateral.")
