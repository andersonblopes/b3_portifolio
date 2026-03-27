# src/langs.py
# Centralized UI copy / i18n strings.
#
# Organization rule:
# - Keep the same key order across languages.
# - Keys currently used by the app come first.
# - Unused/legacy keys (kept for future use) are grouped at the bottom.

# NOTE: When adding a new language, keep the exact same keys and ordering.

LANGUAGES = {
    'English': {
        # --- Sidebar ---
        'currency_label': 'Display currency',
        'upload_msg': 'Import B3 statements (Trading / Movements)',
        'fx_rate_msg': '{base}/BRL FX rate',
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
            'Live prices unavailable for {missing}/{total} tickers. Using average cost as fallback.'
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
        'tab_ticker_changes': 'Ticker changes',

        # --- Ticker changes tab ---
        'ticker_changes_remap_title': 'Renamed tickers',
        'ticker_changes_remap_desc': 'These tickers appear in your B3 export files under their old code. The app automatically maps them to their current active code when fetching prices from Yahoo Finance.',
        'ticker_changes_remap_col_old': 'Old code (in your exports)',
        'ticker_changes_remap_col_new': 'Current active code',
        'ticker_changes_remap_col_note': 'Notes',
        'ticker_changes_discontinued_title': 'Discontinued tickers',
        'ticker_changes_discontinued_desc': 'These tickers are excluded from all portfolio calculations because they are no longer traded (delisted, liquidated, or converted to a private entity). Their historical transactions are still present in the raw data.',
        'ticker_changes_discontinued_col_ticker': 'Ticker',
        'ticker_changes_discontinued_col_reason': 'Reason',
        'ticker_changes_no_data': 'Import a B3 statement to see which of these tickers appear in your portfolio.',

        # --- Ticker changes: corporate actions section ---
        'ticker_changes_corp_title': 'Corporate actions in your portfolio',
        'ticker_changes_corp_desc': 'Split and reverse-split events sourced from Yahoo Finance for the tickers in your portfolio. These are applied automatically to keep quantities and cost basis accurate.',
        'ticker_changes_corp_no_data': 'No corporate action history found for your portfolio tickers.',
        'ticker_changes_corp_col_ticker': 'Ticker',
        'ticker_changes_corp_col_date': 'Effective date',
        'ticker_changes_corp_col_type': 'Type',
        'ticker_changes_corp_col_ratio': 'Ratio',
        'ticker_changes_corp_col_effect': 'Effect on shares',
        'ticker_changes_corp_type_split': 'Forward split',
        'ticker_changes_corp_type_reverse': 'Reverse split',

        # --- Ticker changes: possibly discontinued section ---
        'ticker_changes_possibly_disc_title': 'No live price — possibly discontinued',
        'ticker_changes_possibly_disc_desc': 'These tickers are in your portfolio but returned no live price from Yahoo Finance. They may be delisted, merged, or renamed. If they are no longer tradeable, add them to DISCONTINUED_TICKERS in utils.py to exclude them from calculations.',
        'ticker_changes_possibly_disc_no_data': 'All active portfolio tickers returned a live price.',
        'ticker_changes_possibly_disc_col_ticker': 'Ticker',
        'ticker_changes_possibly_disc_col_last_tx': 'Last transaction date',

        # --- Position analysis ---
        'analysis_btn': 'Analyze',
        'analysis_title': 'Position analysis',
        'analysis_scenario_gain': '🟢 Gaining position',
        'analysis_scenario_loss': '🔴 Losing position',
        'analysis_scenario_flat': '⚪ Flat / breakeven',
        'analysis_current_return': 'Unrealised return',
        'analysis_breakeven': 'Effective breakeven (after earnings)',
        'analysis_trailing_stop': 'Suggested trailing stop',
        'analysis_targets_title': 'Profit-taking targets',
        'analysis_target_20pct': '+20% target — sell 25% of position',
        'analysis_target_50pct': '+50% target — sell 33% of position',
        'analysis_target_double': '2× cost target — sell 50% of position',
        'analysis_dca_title': 'Dollar-cost averaging (DCA)',
        'analysis_dca_topup': 'Top-up — add 50% more shares at current price',
        'analysis_dca_50pct_recovery': 'Reduce loss by 50% — buy at current price',
        'analysis_dca_5pct_above': 'Minimal recovery target — buy at current price',
        'analysis_dca_add_qty': 'Shares to buy',
        'analysis_dca_at_price': 'At price',
        'analysis_dca_new_avg': 'New avg cost',
        'analysis_dca_new_total': 'Additional capital required',
        'analysis_no_targets': 'All profit-taking targets already surpassed.',
        'analysis_no_dca': 'No DCA suggested at current price level.',
        'analysis_note_high_gain': '⚠️ Position is up >50 — consider locking in partial profits.',
        'analysis_note_earnings_offset': 'ℹ️ Dividends already received offset part of the cost basis.',
        'analysis_note_deep_loss': '⚠️ Position is down >30 — review thesis before adding more.',
        'analysis_no_data': 'No live price available — analysis requires a current quote.',
        'analysis_select_label': 'Select an asset to analyse',
        'analysis_select_placeholder': 'Choose a ticker…',
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
        'fx_rate_msg': 'Câmbio {base}/BRL',
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
            'Cotações indisponíveis para {missing}/{total} tickers. Usando preço médio como fallback.'
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
        'tab_ticker_changes': 'Mudanças de tickers',

        # --- Ticker changes tab ---
        'ticker_changes_remap_title': 'Tickers renomeados',
        'ticker_changes_remap_desc': 'Estes tickers aparecem nos seus arquivos exportados da B3 com o código antigo. O aplicativo os mapeia automaticamente para o código atual ao buscar cotações no Yahoo Finance.',
        'ticker_changes_remap_col_old': 'Código antigo (nos seus extratos)',
        'ticker_changes_remap_col_new': 'Código ativo atual',
        'ticker_changes_remap_col_note': 'Observações',
        'ticker_changes_discontinued_title': 'Tickers descontinuados',
        'ticker_changes_discontinued_desc': 'Estes tickers são excluídos de todos os cálculos de portfólio pois não são mais negociados (cancelados, liquidados ou convertidos em empresa fechada). As transações históricas permanecem nos dados brutos.',
        'ticker_changes_discontinued_col_ticker': 'Ticker',
        'ticker_changes_discontinued_col_reason': 'Motivo',
        'ticker_changes_no_data': 'Importe um extrato B3 para ver quais destes tickers aparecem no seu portfólio.',

        # --- Ticker changes: corporate actions section ---
        'ticker_changes_corp_title': 'Eventos corporativos no seu portfólio',
        'ticker_changes_corp_desc': 'Desdobramentos e grupamentos obtidos do Yahoo Finance para os tickers do seu portfólio. Esses eventos são aplicados automaticamente para manter quantidades e custo médio corretos.',
        'ticker_changes_corp_no_data': 'Nenhum histórico de evento corporativo encontrado para os tickers do seu portfólio.',
        'ticker_changes_corp_col_ticker': 'Ticker',
        'ticker_changes_corp_col_date': 'Data efetiva',
        'ticker_changes_corp_col_type': 'Tipo',
        'ticker_changes_corp_col_ratio': 'Fator',
        'ticker_changes_corp_col_effect': 'Efeito nas ações',
        'ticker_changes_corp_type_split': 'Desdobramento',
        'ticker_changes_corp_type_reverse': 'Grupamento',

        # --- Ticker changes: possibly discontinued section ---
        'ticker_changes_possibly_disc_title': 'Sem cotação ao vivo — possivelmente descontinuados',
        'ticker_changes_possibly_disc_desc': 'Esses tickers estão no seu portfólio mas não retornaram cotação ao vivo do Yahoo Finance. Podem estar cancelados, incorporados ou renomeados. Se não forem mais negociados, adicione-os em DISCONTINUED_TICKERS em utils.py para excluí-los dos cálculos.',
        'ticker_changes_possibly_disc_no_data': 'Todos os tickers ativos do portfólio retornaram cotação ao vivo.',
        'ticker_changes_possibly_disc_col_ticker': 'Ticker',
        'ticker_changes_possibly_disc_col_last_tx': 'Última data de transação',

        # --- Position analysis ---
        'analysis_btn': 'Analisar',
        'analysis_title': 'Análise da posição',
        'analysis_scenario_gain': '🟢 Posição lucrativa',
        'analysis_scenario_loss': '🔴 Posição com prejuízo',
        'analysis_scenario_flat': '⚪ Empatado / no ponto de equilíbrio',
        'analysis_current_return': 'Retorno não realizado',
        'analysis_breakeven': 'Ponto de equilíbrio efetivo (após proventos)',
        'analysis_trailing_stop': 'Stop móvel sugerido',
        'analysis_targets_title': 'Alvos de realização de lucro',
        'analysis_target_20pct': 'Alvo +20 — vender 25% da posição',
        'analysis_target_50pct': 'Alvo +50 — vender 33% da posição',
        'analysis_target_double': 'Alvo 2× custo — vender 50% da posição',
        'analysis_dca_title': 'Aportes adicionais (DCA)',
        'analysis_dca_topup': 'Reforço — adicionar 50% mais ações ao preço atual',
        'analysis_dca_50pct_recovery': 'Reduzir prejuízo em 50 — comprar ao preço atual',
        'analysis_dca_5pct_above': 'Meta de recuperação mínima — comprar ao preço atual',
        'analysis_dca_add_qty': 'Ações a comprar',
        'analysis_dca_at_price': 'Ao preço',
        'analysis_dca_new_avg': 'Novo preço médio',
        'analysis_dca_new_total': 'Capital adicional necessário',
        'analysis_no_targets': 'Todos os alvos de realização já foram superados.',
        'analysis_no_dca': 'Nenhum DCA sugerido no nível de preço atual.',
        'analysis_note_high_gain': '⚠️ Posição valorizada >50 — considere realizar lucros parciais.',
        'analysis_note_earnings_offset': 'ℹ️ Os proventos recebidos já compensam parte do custo.',
        'analysis_note_deep_loss': '⚠️ Posição com queda >30 — revise a tese antes de aportar mais.',
        'analysis_no_data': 'Sem cotação ao vivo — a análise requer preço atual.',
        'analysis_select_label': 'Selecione um ativo para analisar',
        'analysis_select_placeholder': 'Escolha um ticker…',
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

    'Español': {
        # --- Sidebar ---
        'currency_label': 'Moneda de visualización',
        'upload_msg': 'Importar extractos B3 (Negociación / Movimientos)',
        'fx_rate_msg': 'Tipo de cambio {base}/BRL',
        'refresh_button': '🔄 Actualizar mercado',
        'refresh_toast': 'Actualizando datos de mercado...',
        'auto_refresh_label': '⏱️ Auto',
        'auto_refresh_help': 'Actualiza cotizaciones y tipo de cambio automáticamente',
        'refresh_interval_label': 'Intervalo',
        'refresh_interval_help': 'Frecuencia de actualización de cotizaciones y tipo de cambio',
        'sidebar_settings': '⚙️ Ajustes',
        'sidebar_market': '📈 Mercado',
        'sidebar_import': '📄 Importación',
        'import_summary_label': 'Resumen de importación',
        'clear_data_button': '🗑️ Limpiar datos de la sesión',
        'yahoo_unavailable_warning': (
            'Cotizaciones no disponibles para {missing}/{total} tickers. Usando costo promedio como alternativa.'
        ),
        'missing_prices_expander': 'Tickers sin cotización en vivo',
        'dedup_summary': 'Duplicados eliminados: {removed} filas (de {before} a {after})',

        # --- Pagination ---
        'pagination_page_size': 'Filas por página',
        'pagination_prev': '◀ Anterior',
        'pagination_next': 'Siguiente ▶',
        'pagination_showing': 'Mostrando {start}-{end} de {total}',

        # --- KPIs ---
        'total_invested': 'Capital invertido',
        'market_value': 'Valor de mercado',
        'gross_pnl': 'Ganancia/Pérdida (no realizada)',
        'total_earnings': 'Dividendos / proventos (caja)',
        'kpi_earnings_net': 'Proventos netos',

        # --- Tabs ---
        'tab_visuals': 'Panel',
        'tab_data': 'Laboratorio de datos',
        'tab_earnings': 'Historial de proventos',
        'tab_audit': 'Auditoria',
        'tab_ticker_changes': 'Cambios de tickers',

        # --- Ticker changes tab ---
        'ticker_changes_remap_title': 'Tickers renombrados',
        'ticker_changes_remap_desc': 'Estos tickers aparecen en sus archivos exportados de B3 con el código antiguo. La aplicación los convierte automáticamente al código vigente al obtener cotizaciones de Yahoo Finance.',
        'ticker_changes_remap_col_old': 'Código antiguo (en sus extractos)',
        'ticker_changes_remap_col_new': 'Código activo actual',
        'ticker_changes_remap_col_note': 'Observaciones',
        'ticker_changes_discontinued_title': 'Tickers descontinuados',
        'ticker_changes_discontinued_desc': 'Estos tickers están excluidos de todos los cálculos de cartera porque ya no se negocian (retirados, liquidados o convertidos a empresa privada). Las transacciones históricas permanecen en los datos originales.',
        'ticker_changes_discontinued_col_ticker': 'Ticker',
        'ticker_changes_discontinued_col_reason': 'Motivo',
        'ticker_changes_no_data': 'Importe un extracto B3 para ver cuáles de estos tickers aparecen en su cartera.',

        # --- Ticker changes: corporate actions section ---
        'ticker_changes_corp_title': 'Eventos corporativos en su cartera',
        'ticker_changes_corp_desc': 'Divisiones y consolidaciones de acciones obtenidas de Yahoo Finance para los tickers de su cartera. Estos eventos se aplican automáticamente para mantener cantidades y precio promedio correctos.',
        'ticker_changes_corp_no_data': 'No se encontró historial de eventos corporativos para los tickers de su cartera.',
        'ticker_changes_corp_col_ticker': 'Ticker',
        'ticker_changes_corp_col_date': 'Fecha efectiva',
        'ticker_changes_corp_col_type': 'Tipo',
        'ticker_changes_corp_col_ratio': 'Factor',
        'ticker_changes_corp_col_effect': 'Efecto en acciones',
        'ticker_changes_corp_type_split': 'División de acciones',
        'ticker_changes_corp_type_reverse': 'Consolidación (agrupamiento)',

        # --- Ticker changes: possibly discontinued section ---
        'ticker_changes_possibly_disc_title': 'Sin precio en vivo — posiblemente descontinuados',
        'ticker_changes_possibly_disc_desc': 'Estos tickers están en su cartera pero no devolvieron precio en vivo de Yahoo Finance. Pueden estar retirados, fusionados o renombrados. Si ya no se negocian, agréguelos a DISCONTINUED_TICKERS en utils.py para excluirlos de los cálculos.',
        'ticker_changes_possibly_disc_no_data': 'Todos los tickers activos de la cartera devolvieron precio en vivo.',
        'ticker_changes_possibly_disc_col_ticker': 'Ticker',
        'ticker_changes_possibly_disc_col_last_tx': 'Fecha de última transacción',

        # --- Position analysis ---
        'analysis_btn': 'Analizar',
        'analysis_title': 'Análisis de posición',
        'analysis_scenario_gain': '🟢 Posición ganadora',
        'analysis_scenario_loss': '🔴 Posición con pérdida',
        'analysis_scenario_flat': '⚪ Equilibrada / en punto muerto',
        'analysis_current_return': 'Retorno no realizado',
        'analysis_breakeven': 'Punto de equilibrio efectivo (después de dividendos)',
        'analysis_trailing_stop': 'Stop móvil sugerido',
        'analysis_targets_title': 'Objetivos de toma de ganancias',
        'analysis_target_20pct': 'Objetivo +20 — vender 25% de la posición',
        'analysis_target_50pct': 'Objetivo +50 — vender 33% de la posición',
        'analysis_target_double': 'Objetivo 2× costo — vender 50% de la posición',
        'analysis_dca_title': 'Promediado de costos (DCA)',
        'analysis_dca_topup': 'Refuerzo — añadir 50% más al precio actual',
        'analysis_dca_50pct_recovery': 'Reducir pérdida al 50 — comprar al precio actual',
        'analysis_dca_5pct_above': 'Meta de recuperación mínima — comprar al precio actual',
        'analysis_dca_add_qty': 'Acciones a comprar',
        'analysis_dca_at_price': 'Al precio',
        'analysis_dca_new_avg': 'Nuevo precio promedio',
        'analysis_dca_new_total': 'Capital adicional requerido',
        'analysis_no_targets': 'Todos los objetivos de ganancia ya fueron superados.',
        'analysis_no_dca': 'Ningún DCA sugerido al nivel de precio actual.',
        'analysis_note_high_gain': '⚠️ Posición >50 — considere tomar ganancias parciales.',
        'analysis_note_earnings_offset': 'ℹ️ Los dividendos recibidos ya compensan parte del costo.',
        'analysis_note_deep_loss': '⚠️ Posición en baja >30 — revise la tesis antes de añadir más.',
        'analysis_no_data': 'Sin precio en vivo — el análisis requiere cotización actual.',
        'analysis_select_label': 'Seleccione un activo para analizar',
        'analysis_select_placeholder': 'Elija un ticker…',
        'audit_fees': 'Comisiones / impuestos',
        'audit_transfers': 'Transferencias / liquidaciones',
        'audit_ignored': 'Filas ignoradas',

        # --- Charts ---
        'chart_evolution': 'Flujo de caja neto (acumulado)',
        'chart_allocation': 'Asignación por tipo de activo',
        'chart_earn_monthly': 'Proventos por mes',
        'chart_earn_type': 'Proventos por tipo',
        'chart_earn_asset_type': 'Proventos por tipo de activo',
        'chart_asset_inst': 'Asignación por corredor',

        # --- Tables / columns ---
        'col_ticker': 'Activo',
        'col_earning_type': 'Tipo de provento',
        'col_qty': 'Cant.',
        'col_avg_price': 'Costo promedio',
        'col_total_cost': 'Costo total',
        'col_curr_price': 'Cotización',
        'col_yield': 'Rend.',
        'col_pnl': 'Resultado',
        'col_earnings': 'Proventos',
        'col_status': 'Estado',
        'col_date': 'Fecha',
        'col_inst': 'Broker',

        # --- Copy ---
        'status_legend': '💡 ✅ Cotización en vivo | ⚠️ Alternativa: costo promedio',
        'assets_count': 'activos',
        'earnings_audit_title': 'Libro mayor de proventos',

        # --- Welcome ---
        'welcome_title': 'Bienvenido a B3 Master Portfolio',
        'welcome_subheader': 'Un dashboard local para acompañar tu cartera y flujo de caja.',
        'quick_start_title': '🚀 Guía rápida',
        'quick_start_step1': '1. Descarga tus extractos XLSX en el Portal del Inversor B3.',
        'quick_start_step2': '2. Sube archivos de Negociación y Movimientos en la barra lateral.',
        'quick_start_step3': '3. Explora Panel, Laboratorio de datos e Historial de proventos.',

        # --- Legacy / currently unused (kept to avoid churn) ---
        'lang_label': 'Idioma',
        'pagination_page': 'Página {page}/{pages}',
        'weight_label': 'peso',
        'col_type': 'Tipo de activo',
        'chart_earn_ticker': 'Mayores pagadores (activos)',
        'chart_earn_inst': 'Proventos por broker',
    },

    'Français': {
        # --- Sidebar ---
        'currency_label': 'Devise d\'affichage',
        'upload_msg': 'Importer des relevés B3 (Transactions / Mouvements)',
        'fx_rate_msg': 'Taux de change {base}/BRL',
        'refresh_button': '🔄 Actualiser le marché',
        'refresh_toast': 'Mise à jour des données de marché...',
        'auto_refresh_label': '⏱️ Auto',
        'auto_refresh_help': 'Met à jour automatiquement les cours et le taux de change',
        'refresh_interval_label': 'Intervalle',
        'refresh_interval_help': 'Fréquence de mise à jour des cours et du taux de change',
        'sidebar_settings': '⚙️ Paramètres',
        'sidebar_market': '📈 Marché',
        'sidebar_import': '📄 Import',
        'import_summary_label': 'Résumé d\'importation',
        'clear_data_button': '🗑️ Effacer les données de session',
        'yahoo_unavailable_warning': (
            'Cours indisponibles pour {missing}/{total} tickers. Utilisation du coût moyen comme solution.'
        ),
        'missing_prices_expander': 'Tickers sans prix en direct',
        'dedup_summary': 'Doublons supprimés : {removed} lignes (de {before} à {after})',

        # --- Pagination ---
        'pagination_page_size': 'Lignes par page',
        'pagination_prev': '◀ Précédent',
        'pagination_next': 'Suivant ▶',
        'pagination_showing': 'Affichage {start}-{end} sur {total}',

        # --- KPIs ---
        'total_invested': 'Capital investi',
        'market_value': 'Valeur de marché',
        'gross_pnl': 'P/L (non réalisé)',
        'total_earnings': 'Dividendes / revenus (cash)',
        'kpi_earnings_net': 'Revenus nets',

        # --- Tabs ---
        'tab_visuals': 'Tableau de bord',
        'tab_data': 'Laboratoire de données',
        'tab_earnings': 'Historique des revenus',
        'tab_audit': 'Audit',
        'tab_ticker_changes': 'Changements de tickers',

        # --- Ticker changes tab ---
        'ticker_changes_remap_title': 'Tickers renommés',
        'ticker_changes_remap_desc': 'Ces tickers figurent dans vos fichiers exportés B3 sous leur ancien code. L’application les convertit automatiquement vers le code actif actuel lors de la récupération des cours sur Yahoo Finance.',
        'ticker_changes_remap_col_old': 'Ancien code (dans vos relevés)',
        'ticker_changes_remap_col_new': 'Code actif actuel',
        'ticker_changes_remap_col_note': 'Notes',
        'ticker_changes_discontinued_title': 'Tickers abandonnés',
        'ticker_changes_discontinued_desc': 'Ces tickers sont exclus de tous les calculs de portefeuille car ils ne sont plus négociés (retraités, liquidés ou convertis en société privée). Les transactions historiques restent présentes dans les données brutes.',
        'ticker_changes_discontinued_col_ticker': 'Ticker',
        'ticker_changes_discontinued_col_reason': 'Raison',
        'ticker_changes_no_data': 'Importez un relevé B3 pour voir lesquels de ces tickers figurent dans votre portefeuille.',

        # --- Ticker changes: corporate actions section ---
        'ticker_changes_corp_title': 'Événements corporatifs dans votre portefeuille',
        'ticker_changes_corp_desc': 'Divisions et regroupements d\u2019actions issus de Yahoo Finance pour les tickers de votre portefeuille. Ces événements sont appliqués automatiquement pour maintenir des quantités et un coût moyen corrects.',
        'ticker_changes_corp_no_data': 'Aucun historique d\u2019événement corporatif trouvé pour les tickers de votre portefeuille.',
        'ticker_changes_corp_col_ticker': 'Ticker',
        'ticker_changes_corp_col_date': 'Date effective',
        'ticker_changes_corp_col_type': 'Type',
        'ticker_changes_corp_col_ratio': 'Facteur',
        'ticker_changes_corp_col_effect': 'Effet sur les actions',
        'ticker_changes_corp_type_split': 'Division d\u2019actions',
        'ticker_changes_corp_type_reverse': 'Regroupement d\u2019actions',

        # --- Ticker changes: possibly discontinued section ---
        'ticker_changes_possibly_disc_title': 'Pas de cours en direct — possiblement abandonnés',
        'ticker_changes_possibly_disc_desc': 'Ces tickers sont dans votre portefeuille mais n\u2019ont retourné aucun cours en direct de Yahoo Finance. Ils peuvent être retirés, fusionnés ou renommés. S\u2019ils ne sont plus négociables, ajoutez-les à DISCONTINUED_TICKERS dans utils.py pour les exclure des calculs.',
        'ticker_changes_possibly_disc_no_data': 'Tous les tickers actifs du portefeuille ont retourné un cours en direct.',
        'ticker_changes_possibly_disc_col_ticker': 'Ticker',
        'ticker_changes_possibly_disc_col_last_tx': 'Date de dernière transaction',

        # --- Position analysis ---
        'analysis_btn': 'Analyser',
        'analysis_title': 'Analyse de position',
        'analysis_scenario_gain': '🟢 Position gagnante',
        'analysis_scenario_loss': '🔴 Position perdante',
        'analysis_scenario_flat': '⚪ À l’équilibre',
        'analysis_current_return': 'Retour non réalisé',
        'analysis_breakeven': 'Seuil de rentabilité effectif (après dividendes)',
        'analysis_trailing_stop': 'Stop suiveur suggéré',
        'analysis_targets_title': 'Objectifs de prise de profit',
        'analysis_target_20pct': 'Objectif +20 — vendre 25 % de la position',
        'analysis_target_50pct': 'Objectif +50 — vendre 33 % de la position',
        'analysis_target_double': 'Objectif 2× coût — vendre 50 % de la position',
        'analysis_dca_title': 'Apports complémentaires (DCA)',
        'analysis_dca_topup': 'Renforcement — ajouter 50 % de plus au prix actuel',
        'analysis_dca_50pct_recovery': 'Réduire la perte de 50 — acheter au prix actuel',
        'analysis_dca_5pct_above': 'Objectif minimal — acheter au prix actuel',
        'analysis_dca_add_qty': 'Actions à acheter',
        'analysis_dca_at_price': 'Au prix',
        'analysis_dca_new_avg': 'Nouveau prix moyen',
        'analysis_dca_new_total': 'Capital supplémentaire requis',
        'analysis_no_targets': 'Tous les objectifs de profit ont déjà été dépassés.',
        'analysis_no_dca': 'Aucun DCA suggéré au niveau de prix actuel.',
        'analysis_note_high_gain': '⚠️ Position >50 — envisagez de prendre des profits partiels.',
        'analysis_note_earnings_offset': 'ℹ️ Les dividendes reçus compensent une partie du coût.',
        'analysis_note_deep_loss': '⚠️ Position en baisse >30 — réexaminez la thèse avant d’investir davantage.',
        'analysis_no_data': 'Pas de cours en direct — l’analyse nécessite une cotation actuelle.',
        'analysis_select_label': 'Choisissez un actif à analyser',
        'analysis_select_placeholder': 'Choisir un ticker…',
        'audit_fees': 'Frais / impôts',
        'audit_transfers': 'Transferts / règlements',
        'audit_ignored': 'Lignes ignorées',

        # --- Charts ---
        'chart_evolution': 'Flux de trésorerie net (cumulé)',
        'chart_allocation': 'Répartition par type d\'actif',
        'chart_earn_monthly': 'Revenus par mois',
        'chart_earn_type': 'Revenus par type',
        'chart_earn_asset_type': 'Revenus par type d\'actif',
        'chart_asset_inst': 'Répartition par courtier',

        # --- Tables / columns ---
        'col_ticker': 'Actif',
        'col_earning_type': 'Type de revenu',
        'col_qty': 'Qté',
        'col_avg_price': 'Coût moyen',
        'col_total_cost': 'Coût total',
        'col_curr_price': 'Cours',
        'col_yield': 'Rend.',
        'col_pnl': 'Résultat',
        'col_earnings': 'Revenus',
        'col_status': 'Statut',
        'col_date': 'Date',
        'col_inst': 'Courtier',

        # --- Copy ---
        'status_legend': '💡 ✅ Prix en direct | ⚠️ Solution : coût moyen',
        'assets_count': 'actifs',
        'earnings_audit_title': 'Grand livre des revenus',

        # --- Welcome ---
        'welcome_title': 'Bienvenue sur B3 Master Portfolio',
        'welcome_subheader': 'Un dashboard local pour suivre votre portefeuille et votre trésorerie.',
        'quick_start_title': '🚀 Démarrage rapide',
        'quick_start_step1': '1. Téléchargez vos relevés XLSX sur le portail investisseur B3.',
        'quick_start_step2': '2. Importez les fichiers Transactions et Mouvements dans la barre latérale.',
        'quick_start_step3': '3. Explorez le tableau de bord, les données et l\'historique des revenus.',

        # --- Legacy / currently unused (kept to avoid churn) ---
        'lang_label': 'Langue',
        'pagination_page': 'Page {page}/{pages}',
        'weight_label': 'poids',
        'col_type': 'Type d\'actif',
        'chart_earn_ticker': 'Principaux payeurs (actifs)',
        'chart_earn_inst': 'Revenus par courtier',
    },
}
