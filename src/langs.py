# src/langs.py
# Centralized UI copy / i18n strings.
#
# Organization rule:
# - Keep the same key order across languages.
# - Keys currently used by the app come first.
# - Unused/legacy keys (kept for future use) are grouped at the bottom.

LANGUAGES = {
    'English': {
        # --- Sidebar ---
        'currency_label': 'Display currency',
        'upload_msg': 'Import B3 statements (Trading / Movements)',
        'exchange_rate_msg': 'USD/BRL FX rate',
        'refresh_button': '🔄 Refresh market data',
        'refresh_toast': 'Updating market data...',
        'auto_refresh_label': '⏱️ Auto refresh',
        'auto_refresh_help': 'Refresh market prices and FX rate on a timer',
        'refresh_interval_label': 'Refresh interval',
        'refresh_interval_help': 'How often to refresh prices and FX rate',
        'sidebar_settings': '⚙️ Settings',
        'sidebar_market': '📈 Market data',
        'sidebar_import': '📄 Import',
        'import_summary_label': 'Import summary',
        'clear_data_button': '🗑️ Clear session data',
        'yahoo_unavailable_warning': (
            'Yahoo Finance unavailable for {missing}/{total} tickers. Using average cost as fallback.'
        ),
        'missing_prices_expander': 'Tickers without live price',
        'dedup_summary': 'Duplicates removed: {removed} rows (from {before} to {after})',

        # --- Pagination ---
        'pagination_page_size': 'Rows per page',
        'pagination_prev': '◀ Prev',
        'pagination_next': 'Next ▶',
        'pagination_showing': 'Showing {start}-{end} of {total}',

        # --- KPIs ---
        'total_invested': 'Invested capital',
        'market_value': 'Market value',
        'gross_pnl': 'Unrealized P/L',
        'total_earnings': 'Cash dividends / earnings',
        'kpi_earnings_net': 'Net earnings',

        # --- Tabs ---
        'tab_visuals': 'Dashboard',
        'tab_data': 'Data Lab',
        'tab_earnings': 'Earnings history',
        'tab_audit': 'Audit',

        # --- Audit ---
        'audit_fees': 'Fees / taxes',
        'audit_transfers': 'Transfers / settlements',
        'audit_ignored': 'Ignored rows',

        # --- Charts ---
        'chart_evolution': 'Net cash flow (cumulative)',
        'chart_allocation': 'Allocation by asset type',
        'chart_earn_monthly': 'Earnings by month',
        'chart_earn_type': 'Earnings by type',
        'chart_earn_asset_type': 'Earnings by asset type',
        'chart_asset_inst': 'Allocation by broker',

        # --- Tables / columns ---
        'col_ticker': 'Asset',
        'col_earning_type': 'Earning type',
        'col_qty': 'Qty',
        'col_avg_price': 'Avg cost',
        'col_total_cost': 'Cost basis',
        'col_curr_price': 'Last price',
        'col_yield': 'Return %',
        'col_pnl': 'P/L',
        'col_earnings': 'Earnings',
        'col_status': 'Price status',
        'col_date': 'Date',
        'col_inst': 'Broker',

        # --- Copy ---
        'status_legend': '💡 ✅ Live price | ⚠️ Fallback to average cost',
        'assets_count': 'assets',
        'earnings_audit_title': 'Earnings ledger',

        # --- Welcome ---
        'welcome_title': 'Welcome to B3 Master Portfolio',
        'welcome_subheader': 'A local dashboard to track your portfolio and cash flow.',
        'quick_start_title': '🚀 Quick start',
        'quick_start_step1': '1. Download your B3 XLSX statements from the Investor Portal.',
        'quick_start_step2': '2. Upload Trading and Movements files in the sidebar.',
        'quick_start_step3': '3. Explore Dashboard, Data Lab and Earnings history.',

        # --- Legacy / currently unused (kept to avoid churn) ---
        'lang_label': 'Language',
        'pagination_page': 'Page {page}/{pages}',
        'weight_label': 'weight',
        'col_type': 'Asset type',
        'chart_earn_ticker': 'Top payers (assets)',
        'chart_earn_inst': 'Earnings by broker',
    },

    'Português (Brasil)': {
        # --- Sidebar ---
        'currency_label': 'Moeda de exibição',
        'upload_msg': 'Importar extratos B3 (Negociação / Movimentação)',
        'exchange_rate_msg': 'Câmbio USD/BRL',
        'refresh_button': '🔄 Atualizar mercado',
        'refresh_toast': 'Atualizando dados de mercado...',
        'auto_refresh_label': '⏱️ Auto',
        'auto_refresh_help': 'Atualiza cotações e câmbio automaticamente',
        'refresh_interval_label': 'Intervalo',
        'refresh_interval_help': 'Frequência de atualização de cotação e câmbio',
        'sidebar_settings': '⚙️ Ajustes',
        'sidebar_market': '📈 Mercado',
        'sidebar_import': '📄 Importação',
        'import_summary_label': 'Resumo da importação',
        'clear_data_button': '🗑️ Limpar dados da sessão',
        'yahoo_unavailable_warning': (
            'Yahoo Finance indisponível para {missing}/{total} tickers. Usando preço médio como fallback.'
        ),
        'missing_prices_expander': 'Tickers sem cotação ao vivo',
        'dedup_summary': 'Duplicatas removidas: {removed} linhas (de {before} para {after})',

        # --- Pagination ---
        'pagination_page_size': 'Linhas por página',
        'pagination_prev': '◀ Anterior',
        'pagination_next': 'Próxima ▶',
        'pagination_showing': 'Mostrando {start}-{end} de {total}',

        # --- KPIs ---
        'total_invested': 'Capital investido',
        'market_value': 'Valor de mercado',
        'gross_pnl': 'Lucro/Prejuízo (não realizado)',
        'total_earnings': 'Proventos (caixa)',
        'kpi_earnings_net': 'Proventos líquidos',

        # --- Tabs ---
        'tab_visuals': 'Painel visual',
        'tab_data': 'Laboratório de dados',
        'tab_earnings': 'Histórico de proventos',
        'tab_audit': 'Auditoria',

        # --- Audit ---
        'audit_fees': 'Taxas / impostos',
        'audit_transfers': 'Transferências / liquidações',
        'audit_ignored': 'Linhas ignoradas',

        # --- Charts ---
        'chart_evolution': 'Fluxo de caixa líquido (acumulado)',
        'chart_allocation': 'Alocação por tipo de ativo',
        'chart_earn_monthly': 'Proventos por mês',
        'chart_earn_type': 'Proventos por tipo',
        'chart_earn_asset_type': 'Proventos por tipo de ativo',
        'chart_asset_inst': 'Alocação por corretora',

        # --- Tables / columns ---
        'col_ticker': 'Ativo',
        'col_earning_type': 'Tipo de provento',
        'col_qty': 'Qtd',
        'col_avg_price': 'Preço médio',
        'col_total_cost': 'Custo total',
        'col_curr_price': 'Cotação',
        'col_yield': 'Red..',
        'col_pnl': 'Resultado',
        'col_earnings': 'Proventos',
        'col_status': 'Status',
        'col_date': 'Data',
        'col_inst': 'Corretora',

        # --- Copy ---
        'status_legend': '💡 ✅ Cotação ao vivo | ⚠️ Fallback para preço médio',
        'assets_count': 'ativos',
        'earnings_audit_title': 'Razão de proventos',

        # --- Welcome ---
        'welcome_title': 'Bem-vindo ao B3 Master Portfolio',
        'welcome_subheader': 'Um dashboard local para acompanhar portfólio e fluxo de caixa.',
        'quick_start_title': '🚀 Guia rápido',
        'quick_start_step1': '1. Baixe seus extratos XLSX no Portal do Investidor B3.',
        'quick_start_step2': '2. Envie Negociação e Movimentação na barra lateral.',
        'quick_start_step3': '3. Explore Painel visual, Laboratório de dados e Histórico de proventos.',

        # --- Legacy / currently unused (kept to avoid churn) ---
        'lang_label': 'Idioma',
        'pagination_page': 'Página {page}/{pages}',
        'weight_label': 'peso',
        'col_type': 'Tipo de ativo',
        'chart_earn_ticker': 'Maiores pagadores (ativos)',
        'chart_earn_inst': 'Proventos por corretora',
    },
}
