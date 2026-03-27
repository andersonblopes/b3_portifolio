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
