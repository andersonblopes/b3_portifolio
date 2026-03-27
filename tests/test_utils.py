import io
import pytest
from types import SimpleNamespace

import pandas as pd

import src.utils as utils


def _xlsx_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()


def _uploaded_file(df: pd.DataFrame, name: str):
    """Mimic Streamlit UploadedFile (file-like + .name)."""
    b = _xlsx_bytes(df)
    bio = io.BytesIO(b)
    bio.name = name  # pandas may use this; utils uses getattr(file, "name", ...)
    return bio


def test_clean_ticker_handles_fractional_and_noise():
    assert utils.clean_ticker("KLBN4F") == "KLBN4"
    assert utils.clean_ticker("  petr4 ") == "PETR4"
    assert utils.clean_ticker("ABCD11 - FUNDO") == "ABCD11"


def test_clean_ticker_bdr_34_suffix_not_truncated():
    # regression: regex order bug caused VERZ34 to be parsed as VERZ3
    assert utils.clean_ticker("VERZ34 - VERIZON COMMUNICATIONS INC.") == "VERZ34"
    assert utils.clean_ticker("AAPL34") == "AAPL34"
    assert utils.clean_ticker("MSFT34") == "MSFT34"


def test_detect_asset_type_basic():
    assert utils.detect_asset_type("HGLG11") == "FII/ETF"
    assert utils.detect_asset_type("AAPL34") == "BDR"
    assert utils.detect_asset_type("PETR4") == "Ação"


def test_detect_asset_type_pn2_shares():
    # *2 tickers (e.g. BMGB2) were classified as 'Outro' before the fix
    assert utils.detect_asset_type("BMGB2") == "Ação"
    assert utils.detect_asset_type("VALE7") == "Ação"
    assert utils.detect_asset_type("PETR8") == "Ação"


def test_load_and_process_negociacao_parses_buy_sell_and_audit_ignore():
    df = pd.DataFrame(
        {
            "Data do Negócio": ["01/02/2026", "01/02/2026", "01/02/2026"],
            "Código de Negociação": ["PETR4", "VALE3", "ITUB4"],
            "Quantidade": [10, 5, 1],
            "Valor": [100.0, 200.0, 999.0],
            "Instituição": ["XP", "XP", "XP"],
            "Tipo de Movimentação": ["COMPRA", "VENDA", "ALGO DESCONHECIDO"],
        }
    )

    main_df, stats_df, audit_df = utils.load_and_process_files([_uploaded_file(df, "neg.xlsx")])

    # main only has BUY/SELL (IGNORE goes to audit)
    assert set(main_df["type"].unique()) == {"BUY", "SELL"}
    assert (audit_df["type"] == "IGNORE").all()

    row = stats_df.iloc[0].to_dict()
    assert row["detected"] == "NEG"
    assert row["rows_total"] == 3
    assert row["rows_buy"] == 1
    assert row["rows_sell"] == 1
    assert row["rows_ignored"] == 1


def test_load_and_process_movimentacao_applies_sign_and_classification():
    df = pd.DataFrame(
        {
            "Data": ["01/02/2026", "02/02/2026", "03/02/2026"],
            "Produto": ["HGLG11", "HGLG11", "HGLG11"],
            "Instituição": ["BTG", "BTG", "BTG"],
            "Quantidade": [148.0, 0.0, 0.0],
            "Valor da Operação": [10.0, 1.0, 7.0],
            "Movimentação": ["RENDIMENTO", "TAXA DE CUSTÓDIA", "TRANSFERÊNCIA"],
            "Entrada/Saída": ["Crédito", "Débito", "Crédito"],
        }
    )

    main_df, stats_df, audit_df = utils.load_and_process_files([_uploaded_file(df, "mov.xlsx")])

    # Only earnings are kept in main
    assert set(main_df["type"].unique()) == {"EARNINGS"}
    assert main_df["val"].iloc[0] == 10.0

    # qty is now extracted from the Quantidade column
    assert main_df["qty"].iloc[0] == 148.0

    # Fees/transfer go to audit; fee is negative due to Débito
    assert set(audit_df["type"].unique()) == {"FEES", "TRANSFER"}
    fee_val = audit_df.loc[audit_df["type"] == "FEES", "val"].iloc[0]
    assert fee_val == -1.0

    row = stats_df.iloc[0].to_dict()
    assert row["detected"] == "MOV"
    assert row["rows_total"] == 3
    assert row["rows_earnings"] == 1
    assert row["rows_fees"] == 1
    assert row["rows_transfer"] == 1


def test_load_and_process_movimentacao_classifies_emprestimo_and_leilao():
    df = pd.DataFrame(
        {
            "Data": ["01/02/2026", "02/02/2026", "03/02/2026"],
            "Produto": ["PETR4", "MGLU3", "VALE3"],
            "Instituição": ["BTG", "BTG", "BTG"],
            "Quantidade": [0.0, 0.0, 0.0],
            "Valor da Operação": [5.0, 2.0, 1.0],
            "Movimentação": ["Empréstimo", "Leilão de Fração", "Reembolso"],
            "Entrada/Saída": ["Credito", "Credito", "Credito"],
        }
    )

    main_df, stats_df, audit_df = utils.load_and_process_files([_uploaded_file(df, "mov.xlsx")])

    # all three should flow into EARNINGS, not IGNORE
    assert len(main_df) == 3
    assert (main_df["type"] == "EARNINGS").all()


def test_dedup_across_multiple_uploads_adds_summary_row():
    df = pd.DataFrame(
        {
            "Data": ["01/02/2026"],
            "Produto": ["HGLG11"],
            "Instituição": ["BTG"],
            "Quantidade": [10.0],
            "Valor da Operação": [10.0],
            "Movimentação": ["RENDIMENTO"],
            "Entrada/Saída": ["Crédito"],
        }
    )

    main_df, stats_df, audit_df = utils.load_and_process_files(
        [_uploaded_file(df, "mov-1.xlsx"), _uploaded_file(df, "mov-2.xlsx")]
    )

    # Without dedup we'd have 2 identical earnings rows
    assert len(main_df) == 1
    assert audit_df.empty

    dedup_rows = stats_df[stats_df["detected"] == "DEDUP"]
    assert len(dedup_rows) == 1
    assert int(dedup_rows["dedup_removed_main"].iloc[0]) == 1


def test_calculate_portfolio_clamps_sell_bigger_than_position():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-02-01", "2026-02-02"]),
            "ticker": ["PETR4", "PETR4"],
            "type": ["BUY", "SELL"],
            "qty": [10, 999],
            "val": [100.0, 0.0],
        }
    )

    out = utils.calculate_portfolio(df)
    # Position should not go negative; clamped to zero
    assert out.empty


def test_calculate_portfolio_skips_discontinued_tickers():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "ticker": ["LSPA11", "PETR4"],
            "type": ["BUY", "BUY"],
            "qty": [100, 10],
            "val": [5000.0, 100.0],
        }
    )

    out = utils.calculate_portfolio(df)
    # LSPA11 is in DISCONTINUED_TICKERS; only PETR4 should appear
    assert list(out["ticker"]) == ["PETR4"]


def test_ticker_remap_maps_brit3_to_brst3():
    assert utils.TICKER_REMAP["BRIT3"]["new"] == "BRST3"
    assert "note" in utils.TICKER_REMAP["BRIT3"]


def test_discontinued_tickers_is_dict_with_reasons():
    assert isinstance(utils.DISCONTINUED_TICKERS, dict)
    # every entry must have a non-empty reason string
    for ticker, reason in utils.DISCONTINUED_TICKERS.items():
        assert isinstance(reason, str) and reason


def test_get_exchange_rate_uses_yfinance_response(monkeypatch):
    import pandas as pd

    data = pd.DataFrame({"Close": [5.20]})
    monkeypatch.setattr(utils.yf, "download", lambda *a, **kw: data)

    result = utils.get_exchange_rate.__wrapped__("USD")
    assert result == 5.20


def test_get_exchange_rate_fallback_on_yfinance_error(monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError("yfinance down")

    monkeypatch.setattr(utils.yf, "download", boom)

    assert utils.get_exchange_rate.__wrapped__("USD") == 5.45
    assert utils.get_exchange_rate.__wrapped__("EUR") == 5.90


def test_fetch_market_prices_uses_yfinance_response(monkeypatch):
    import pandas as pd
    from unittest.mock import MagicMock

    # multi-ticker return: top-level keys are ticker symbols
    close_petr4 = pd.Series([38.50], name="Close")
    close_vale3 = pd.Series([65.10], name="Close")
    data = pd.DataFrame(
        {("PETR4.SA", "Close"): [38.50], ("VALE3.SA", "Close"): [65.10]}
    )
    data.columns = pd.MultiIndex.from_tuples(data.columns)

    monkeypatch.setattr(utils.yf, "download", lambda *a, **kw: data)

    result = utils.fetch_market_prices.__wrapped__(["PETR4", "VALE3"])
    assert result["PETR4"] == {"p": 38.50, "live": True}
    assert result["VALE3"] == {"p": 65.10, "live": True}


def test_fetch_market_prices_fallback_on_yfinance_error(monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError("yfinance down")

    monkeypatch.setattr(utils.yf, "download", boom)

    result = utils.fetch_market_prices.__wrapped__(["PETR4"])
    assert result["PETR4"] == {"p": None, "live": False}


def test_fetch_market_prices_returns_empty_for_no_tickers():
    assert utils.fetch_market_prices.__wrapped__([]) == {}


def test_load_and_process_movimentacao_routes_corporate_actions_to_main_df():
    df = pd.DataFrame(
        {
            "Data": ["28/05/2024", "28/05/2024", "31/05/2024", "02/01/2026"],
            "Produto": ["MGLU3", "MGLU3", "MGLU3", "MGLU3"],
            "Instituição": ["XP", "XP", "XP", "XP"],
            "Quantidade": [4.8, 0.0, 0.8, 0.2],
            "Valor da Operação": [0.0, 5.0, 0.0, 0.0],
            "Movimentação": ["Grupamento", "Dividendo", "Fração em Ativos", "Bonificação em Ativos"],
            "Entrada/Saída": ["Credito", "Credito", "Debito", "Credito"],
        }
    )

    main_df, _, audit_df = utils.load_and_process_files([_uploaded_file(df, "mov.xlsx")])

    main_types = set(main_df["type"].unique())
    # all three corporate action types must reach main_df
    assert "REVERSE_SPLIT" in main_types
    assert "SELL" in main_types
    assert "SPLIT" in main_types
    assert "EARNINGS" in main_types
    # none of them should leak into audit
    assert "REVERSE_SPLIT" not in set(audit_df["type"].unique())
    assert "SPLIT" not in set(audit_df["type"].unique())


def test_calculate_portfolio_applies_reverse_split_correctly():
    # simulate: buy 48 shares, then 10:1 grupamento credits 4.8 new shares
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-05-24", "2024-05-28"]),
            "ticker": ["MGLU3", "MGLU3"],
            "type": ["BUY", "REVERSE_SPLIT"],
            "qty": [48.0, 4.8],
            "val": [65.28, 0.0],
        }
    )

    out = utils.calculate_portfolio(df)
    row = out[out["ticker"] == "MGLU3"].iloc[0]

    # qty must reflect the post-grupamento count
    assert row["qty"] == pytest.approx(4.8, abs=0.01)
    # total cost is preserved by the grupamento
    assert row["avg_price"] == pytest.approx(65.28 / 4.8, abs=0.01)


def test_calculate_portfolio_applies_split_correctly():
    # simulate: buy 10 shares, then 1:4 desdobramento adds 30 more
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2019-08-01", "2019-08-05"]),
            "ticker": ["MGLU3", "MGLU3"],
            "type": ["BUY", "SPLIT"],
            "qty": [10.0, 30.0],
            "val": [100.0, 0.0],
        }
    )

    out = utils.calculate_portfolio(df)
    row = out[out["ticker"] == "MGLU3"].iloc[0]

    assert row["qty"] == pytest.approx(40.0, abs=0.01)
    # total cost unchanged; avg cost quartered
    assert row["avg_price"] == pytest.approx(2.50, abs=0.01)


def test_calculate_portfolio_full_mglu3_corporate_action_sequence():
    # reproduces the MGLU3 scenario: buy 48 pre-grupamento, grupamento 10:1,
    # fractional sell 0.8, bonificação adds 0.2, fractional sell 0.2
    df = pd.DataFrame(
        {
            "date": pd.to_datetime([
                "2024-05-24",  # buy 48 @ 1.36
                "2024-05-28",  # grupamento → 4.8
                "2024-05-31",  # fração em ativos sell 0.8
                "2026-01-02",  # bonificação +0.2
                "2026-02-09",  # fração em ativos sell 0.2
            ]),
            "ticker": ["MGLU3"] * 5,
            "type": ["BUY", "REVERSE_SPLIT", "SELL", "SPLIT", "SELL"],
            "qty": [48.0, 4.8, 0.8, 0.2, 0.2],
            "val": [65.28, 0.0, 0.0, 0.0, 0.0],
        }
    )

    out = utils.calculate_portfolio(df)
    row = out[out["ticker"] == "MGLU3"].iloc[0]

    # after all corporate actions: 4.0 shares remaining
    assert row["qty"] == pytest.approx(4.0, abs=0.01)
    # cost basis must be positive and less than the original R$65.28
    assert 0 < row["avg_price"] * row["qty"] < 65.28


def test_fetch_split_history_returns_events_for_known_ticker(monkeypatch):
    import pandas as pd

    # mock yfinance returning one forward split and one reverse split
    mock_splits = pd.Series(
        [4.0, 0.1],
        index=pd.to_datetime(["2020-10-14", "2024-05-27"]).tz_localize("America/Sao_Paulo"),
    )

    class MockTicker:
        def __init__(self, _symbol):
            self.splits = mock_splits

    monkeypatch.setattr(utils.yf, "Ticker", MockTicker)

    result = utils.fetch_split_history.__wrapped__(("MGLU3",))
    assert "MGLU3" in result
    events = result["MGLU3"]
    assert len(events) == 2
    # check dates are tz-naive
    assert events[0]["date"].tzinfo is None
    assert events[0]["ratio"] == pytest.approx(4.0)
    assert events[1]["ratio"] == pytest.approx(0.1)


def test_fetch_split_history_returns_empty_for_no_data(monkeypatch):
    import pandas as pd

    class MockTicker:
        def __init__(self, _symbol):
            self.splits = pd.Series([], dtype=float)

    monkeypatch.setattr(utils.yf, "Ticker", MockTicker)

    result = utils.fetch_split_history.__wrapped__(("UNKNOWN99",))
    assert result == {}


def test_calculate_portfolio_uses_yfinance_splits_when_no_mov(monkeypatch):
    # NEG-only scenario: buy 48 MGLU3 at R$1.36, no MOV corporate action rows.
    # split_history provides the 10:1 reverse split (ratio=0.1) and 5% bonus (1.05).
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-05-24"]),
            "ticker": ["MGLU3"],
            "type": ["BUY"],
            "qty": [48.0],
            "val": [65.28],
        }
    )

    split_history = {
        "MGLU3": [
            {"date": pd.Timestamp("2024-05-27"), "ratio": 0.1},   # grupamento 10:1
            {"date": pd.Timestamp("2025-12-30"), "ratio": 1.05},  # bonificação 5%
        ]
    }

    out = utils.calculate_portfolio(df, split_history=split_history)
    row = out[out["ticker"] == "MGLU3"].iloc[0]

    # after 10:1 reverse (48→4.8) then 5% bonus (4.8→5.04)
    assert row["qty"] == pytest.approx(5.04, abs=0.01)
    # cost is preserved; avg_price rises from R$1.36 to ~R$12.95
    assert row["avg_price"] == pytest.approx(65.28 / 5.04, abs=0.01)


def test_calculate_portfolio_yfinance_splits_not_applied_when_mov_exists():
    # if MOV data already provides REVERSE_SPLIT rows, yfinance splits must be skipped
    # entirely to avoid double-applying the same corporate action.
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-05-24", "2024-05-28"]),
            "ticker": ["MGLU3", "MGLU3"],
            "type": ["BUY", "REVERSE_SPLIT"],
            "qty": [48.0, 4.8],
            "val": [65.28, 0.0],
            "source": ["NEG", "MOV"],
        }
    )

    # even if split_history is provided, it must not be applied because MOV data exists
    split_history = {
        "MGLU3": [{"date": pd.Timestamp("2024-05-27"), "ratio": 0.1}]
    }

    out = utils.calculate_portfolio(df, split_history=split_history)
    row = out[out["ticker"] == "MGLU3"].iloc[0]

    # qty should be the MOV grupamento value (4.8), not double-applied
    assert row["qty"] == pytest.approx(4.8, abs=0.01)


# --- analyze_position ---

def test_analyze_position_returns_none_for_invalid_inputs():
    assert utils.analyze_position("X3", qty=0, avg_price=10, total_cost=0, current_price=10, earnings=0, asset_type="Ação") is None
    assert utils.analyze_position("X3", qty=10, avg_price=10, total_cost=100, current_price=0, earnings=0, asset_type="Ação") is None


def test_analyze_position_gain_scenario_basic():
    # 30% gain on 100 shares bought at R$10
    result = utils.analyze_position(
        ticker="PETR4",
        qty=100,
        avg_price=10.0,
        total_cost=1000.0,
        current_price=13.0,
        earnings=0.0,
        asset_type="Ação",
    )
    assert result is not None
    assert result['scenario'] == 'gain'
    assert result['yield_pct'] == pytest.approx(30.0)
    # breakeven equals avg_price when earnings=0
    assert result['breakeven'] == pytest.approx(10.0)
    # trailing stop: 15% below current = 13 * 0.85 = 11.05; above breakeven so kept
    assert result['trailing_stop'] == pytest.approx(13.0 * 0.85, abs=0.01)
    # targets: +20% and +50% are above current (13.0 * 1.2 = 12 < 13 → only +50% and 2× remain)
    prices_above_current = [t['price'] for t in result['targets']]
    for p in prices_above_current:
        assert p > 13.0


def test_analyze_position_gain_targets_content():
    result = utils.analyze_position(
        ticker="VALE3",
        qty=200,
        avg_price=50.0,
        total_cost=10000.0,
        current_price=55.0,  # only +10%, all targets still ahead
        earnings=0.0,
        asset_type="Ação",
    )
    labels = [t['label'] for t in result['targets']]
    assert 'target_20pct' in labels   # 50 * 1.20 = 60 > 55
    assert 'target_50pct' in labels   # 50 * 1.50 = 75 > 55
    assert 'target_double' in labels  # 50 * 2.00 = 100 > 55
    # sell quantities follow the fractions: 25%, 33%, 50% of qty=200
    qty_map = {t['label']: t['qty_to_sell'] for t in result['targets']}
    assert qty_map['target_20pct'] == 50    # 200 * 0.25
    assert qty_map['target_50pct'] == 66    # 200 * 0.33 rounded
    assert qty_map['target_double'] == 100  # 200 * 0.50


def test_analyze_position_all_targets_surpassed():
    # current_price is already above 2× avg_price — no targets left
    result = utils.analyze_position(
        ticker="MGLU3",
        qty=100,
        avg_price=10.0,
        total_cost=1000.0,
        current_price=25.0,  # 150% gain, above 2× cost
        earnings=0.0,
        asset_type="Ação",
    )
    assert result['targets'] == []
    assert 'note_high_gain' in result['notes']


def test_analyze_position_loss_scenario_dca():
    # 40% loss: avg=20, current=12 → DCA suggestions must be present
    result = utils.analyze_position(
        ticker="MGLU3",
        qty=100,
        avg_price=20.0,
        total_cost=2000.0,
        current_price=12.0,
        earnings=0.0,
        asset_type="Ação",
    )
    assert result['scenario'] == 'loss'
    assert result['yield_pct'] == pytest.approx(-40.0)
    assert 'note_deep_loss' in result['notes']
    assert len(result['dca']) > 0
    # verify DCA formula: for midpoint target = (20+12)/2 = 16
    # add_qty = (2000 - 16*100) / (16 - 12) = (2000-1600)/4 = 100
    midpoint_dca = next(d for d in result['dca'] if d['label'] == 'dca_50pct_recovery')
    assert midpoint_dca['add_qty'] == pytest.approx(100.0, abs=0.5)
    # new_avg after buying 100 more at 12: (2000 + 100*12) / 200 = 3200/200 = 16
    assert midpoint_dca['new_avg'] == pytest.approx(16.0, abs=0.05)


def test_analyze_position_flat_scenario():
    # yield between 0% and 0.5% → flat
    result = utils.analyze_position(
        ticker="ABEV3",
        qty=100,
        avg_price=10.0,
        total_cost=1000.0,
        current_price=10.01,
        earnings=0.0,
        asset_type="Ação",
    )
    assert result['scenario'] == 'flat'


def test_analyze_position_fii_trailing_stop_8pct():
    result = utils.analyze_position(
        ticker="KNRI11",
        qty=50,
        avg_price=100.0,
        total_cost=5000.0,
        current_price=120.0,
        earnings=0.0,
        asset_type="FII/ETF",
    )
    # FII uses 8% trail: 120 * 0.92 = 110.4; above breakeven (100), so kept
    assert result['trailing_stop'] == pytest.approx(120.0 * 0.92, abs=0.01)


def test_analyze_position_bdr_trailing_stop_12pct():
    result = utils.analyze_position(
        ticker="AAPL34",
        qty=10,
        avg_price=400.0,
        total_cost=4000.0,
        current_price=500.0,
        earnings=0.0,
        asset_type="BDR",
    )
    # BDR uses 12% trail: 500 * 0.88 = 440; above breakeven (400), so kept
    assert result['trailing_stop'] == pytest.approx(500.0 * 0.88, abs=0.01)


def test_analyze_position_trailing_stop_floored_at_breakeven():
    # current_price barely above avg_price: trailing stop would go below cost → floor at breakeven
    result = utils.analyze_position(
        ticker="PETR4",
        qty=100,
        avg_price=10.0,
        total_cost=1000.0,
        current_price=10.5,    # only +5%; 15% trail = 8.925 < breakeven 10.0
        earnings=0.0,
        asset_type="Ação",
    )
    assert result['trailing_stop'] == pytest.approx(10.0, abs=0.01)


def test_analyze_position_earnings_reduce_breakeven():
    # R$200 of earnings on a R$1000 position → effective cost = R$800 → breakeven = R$8
    result = utils.analyze_position(
        ticker="ITUB4",
        qty=100,
        avg_price=10.0,
        total_cost=1000.0,
        current_price=11.0,
        earnings=200.0,
        asset_type="Ação",
    )
    assert result['breakeven'] == pytest.approx(8.0)
    assert 'note_earnings_offset' in result['notes']


def test_analyze_position_dca_top_up_only_when_yield_below_20():
    # 10% gain — below the 20% threshold, so DCA top-up must be suggested
    result_low = utils.analyze_position(
        ticker="VALE3",
        qty=100,
        avg_price=50.0,
        total_cost=5000.0,
        current_price=55.0,
        earnings=0.0,
        asset_type="Ação",
    )
    assert result_low['dca'] is not None
    assert len(result_low['dca']) > 0
    assert result_low['dca'][0]['label'] == 'dca_topup'

    # 25% gain — above threshold, no DCA suggested
    result_high = utils.analyze_position(
        ticker="VALE3",
        qty=100,
        avg_price=50.0,
        total_cost=5000.0,
        current_price=62.5,
        earnings=0.0,
        asset_type="Ação",
    )
    assert result_high['dca'] == [] or result_high['dca'] is None


# --- recommendation engine ---

def test_analyze_position_has_recommendation_field():
    result = utils.analyze_position(
        ticker="PETR4", qty=100, avg_price=30.0, total_cost=3000.0,
        current_price=32.0, earnings=0.0, asset_type="Ação",
    )
    assert 'recommendation' in result
    assert result['recommendation'] in ('exit', 'trim', 'hold', 'dca')


def test_analyze_position_exit_when_below_stop():
    # price just above avg but below the trailing stop floor at breakeven
    # avg=30, earnings=0, breakeven=30, current=25 (below stop)
    result = utils.analyze_position(
        ticker="PETR4", qty=100, avg_price=30.0, total_cost=3000.0,
        current_price=25.0, earnings=0.0, asset_type="Ação",
    )
    assert result['price_below_stop'] is True
    assert result['recommendation'] == 'exit'


def test_analyze_position_hold_overrides_exit_when_high_dividend():
    # price below stop but yield-on-cost >= 8% — dividend cushion keeps the hold
    result = utils.analyze_position(
        ticker="BBAS3", qty=100, avg_price=30.0, total_cost=3000.0,
        current_price=25.0, earnings=300.0, asset_type="Ação",
    )
    # earnings/total_cost = 10% >= 8% → dividend override
    assert result['yield_on_cost'] >= 8.0
    assert result['price_below_stop'] is True
    assert result['recommendation'] == 'hold'


def test_analyze_position_trim_at_50pct_gain():
    result = utils.analyze_position(
        ticker="VALE3", qty=100, avg_price=20.0, total_cost=2000.0,
        current_price=32.0, earnings=0.0, asset_type="Ação",
    )
    assert result['yield_pct'] >= 50
    assert result['recommendation'] == 'trim'


def test_analyze_position_hold_for_moderate_gain():
    # +10% gain, no stop triggered — should be hold
    result = utils.analyze_position(
        ticker="VALE3", qty=100, avg_price=20.0, total_cost=2000.0,
        current_price=22.0, earnings=0.0, asset_type="Ação",
    )
    assert result['scenario'] in ('gain', 'flat')
    assert result['recommendation'] == 'hold'


def test_analyze_position_dca_recommended_on_loss():
    # 5% loss; earnings reduce breakeven below current_price so stop is not triggered;
    # yield-on-cost is 6% (< 8%) so no dividend cushion → lands on DCA
    result = utils.analyze_position(
        ticker="MGLU3", qty=100, avg_price=10.0, total_cost=1000.0,
        current_price=9.5, earnings=60.0, asset_type="Ação",
        portfolio_total_value=500_000.0,
    )
    assert result['scenario'] == 'loss'
    assert result['price_below_stop'] is False
    assert result['yield_on_cost'] < 8.0
    assert result['recommendation'] == 'dca'
    assert any(not d['concentration_risk'] for d in result['dca'])


def test_analyze_position_dca_blocked_by_concentration():
    # same small-loss scenario but tiny portfolio forces every DCA above 10% weight
    result = utils.analyze_position(
        ticker="MGLU3", qty=100, avg_price=10.0, total_cost=1000.0,
        current_price=9.5, earnings=60.0, asset_type="Ação",
        portfolio_total_value=2000.0,   # mkt_value=950 already 47.5%; any DCA → > 10%
    )
    assert result['scenario'] == 'loss'
    assert result['price_below_stop'] is False
    assert result['dca']
    all_blocked = all(d['concentration_risk'] for d in result['dca'])
    assert all_blocked
    assert result['recommendation'] == 'hold'


def test_analyze_position_concentration_risk_flag_per_dca_entry():
    # with a very small portfolio, any additional purchase should flag concentration
    result = utils.analyze_position(
        ticker="MGLU3", qty=500, avg_price=20.0, total_cost=10000.0,
        current_price=15.0, earnings=0.0, asset_type="Ação",
        portfolio_total_value=20_000.0,
    )
    for d in result['dca']:
        assert 'concentration_risk' in d
        assert 'new_weight' in d
        assert isinstance(d['concentration_risk'], bool)
        assert isinstance(d['new_weight'], float)


def test_analyze_position_yield_on_cost_calculated():
    result = utils.analyze_position(
        ticker="BBSE3", qty=100, avg_price=30.0, total_cost=3000.0,
        current_price=32.0, earnings=240.0, asset_type="Ação",
    )
    # 240 / 3000 * 100 = 8.0
    assert result['yield_on_cost'] == pytest.approx(8.0)


def test_analyze_position_current_weight_calculated():
    result = utils.analyze_position(
        ticker="BBSE3", qty=100, avg_price=30.0, total_cost=3000.0,
        current_price=40.0, earnings=0.0, asset_type="Ação",
        portfolio_total_value=40_000.0,
    )
    # mkt_value = 4000, portfolio = 40000 → weight = 10%
    assert result['current_weight'] == pytest.approx(10.0)


def test_analyze_position_current_price_in_result():
    result = utils.analyze_position(
        ticker="PETR4", qty=100, avg_price=30.0, total_cost=3000.0,
        current_price=28.5, earnings=0.0, asset_type="Ação",
    )
    assert result['current_price'] == pytest.approx(28.5)

