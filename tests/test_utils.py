import io
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


def test_detect_asset_type_basic():
    assert utils.detect_asset_type("HGLG11") == "FII/ETF"
    assert utils.detect_asset_type("AAPL34") == "BDR"
    assert utils.detect_asset_type("PETR4") == "Ação"


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
            "Valor da Operação": [10.0, 1.0, 7.0],
            "Movimentação": ["RENDIMENTO", "TAXA DE CUSTÓDIA", "TRANSFERÊNCIA"],
            "Entrada/Saída": ["Crédito", "Débito", "Crédito"],
        }
    )

    main_df, stats_df, audit_df = utils.load_and_process_files([_uploaded_file(df, "mov.xlsx")])

    # Only earnings are kept in main
    assert set(main_df["type"].unique()) == {"EARNINGS"}
    assert main_df["val"].iloc[0] == 10.0

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


def test_dedup_across_multiple_uploads_adds_summary_row():
    df = pd.DataFrame(
        {
            "Data": ["01/02/2026"],
            "Produto": ["HGLG11"],
            "Instituição": ["BTG"],
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


def test_get_exchange_rate_fallback_on_yahoo_error(monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError("yahoo down")

    monkeypatch.setattr(utils.yf, "download", boom)

    # Bypass Streamlit cache wrapper
    assert utils.get_exchange_rate.__wrapped__("USD") == 5.45
    assert utils.get_exchange_rate.__wrapped__("EUR") == 5.90
