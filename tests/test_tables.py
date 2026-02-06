import pandas as pd

import src.tables as tables
from src.langs import LANGUAGES


def _texts():
    return LANGUAGES["English"]


def test_render_portfolio_table_calls_streamlit_dataframe(monkeypatch):
    captured = {}

    def fake_dataframe(arg, **kwargs):
        captured["arg"] = arg
        captured["kwargs"] = kwargs

    monkeypatch.setattr(tables.st, "dataframe", fake_dataframe)

    df = pd.DataFrame(
        {
            "ticker": ["PETR4"],
            "qty": [10],
            "avg_price": [10.0],
            "total_cost": [100.0],
            "p_atual": [11.0],
            "v_mercado": [110.0],
            "pnl": [10.0],
            "yield": [10.0],
            "status": ["✅"],
            "earnings": [1.0],
        }
    )

    tables.render_portfolio_table(df, _texts(), lambda v: f"{v:.2f}")

    assert "arg" in captured
    assert captured["kwargs"]["width"] == "stretch"
    assert captured["kwargs"]["hide_index"] is True

    # The argument should be a Styler with renamed columns
    styler = captured["arg"]
    assert hasattr(styler, "data")
    assert "Asset" in styler.data.columns


def test_render_earnings_log_calls_streamlit_dataframe(monkeypatch):
    captured = {}

    def fake_dataframe(arg, **kwargs):
        captured["arg"] = arg
        captured["kwargs"] = kwargs

    monkeypatch.setattr(tables.st, "dataframe", fake_dataframe)

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-02-01"]),
            "ticker": ["HGLG11"],
            "val": [10.0],
            "sub_type": ["Income"],
            "inst": ["XP"],
        }
    )

    tables.render_earnings_log(df, _texts(), lambda v: f"{v:.2f}")

    assert "arg" in captured
    assert captured["kwargs"]["width"] == "stretch"
    assert captured["kwargs"]["hide_index"] is True

    styler = captured["arg"]
    assert hasattr(styler, "data")
    assert set(styler.data.columns) == {"Date", "Asset", "Broker", "Earning type", "Earnings"}
