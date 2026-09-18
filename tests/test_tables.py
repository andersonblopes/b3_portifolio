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


def test_render_portfolio_table_selectable_returns_event(monkeypatch):
    events = {}

    class FakeEvent:
        selection = type("Sel", (), {"rows": []})()

    def fake_dataframe(arg, **kwargs):
        events["kwargs"] = kwargs
        return FakeEvent()

    class FakeColumnConfig:
        class TextColumn:
            def __init__(self, *a, **kw):
                pass

        class ImageColumn:
            def __init__(self, *a, **kw):
                pass

    monkeypatch.setattr(tables.st, "dataframe", fake_dataframe)
    monkeypatch.setattr(tables.st, "column_config", FakeColumnConfig())

    df = pd.DataFrame(
        {
            "ticker": ["VALE3"],
            "qty": [20],
            "avg_price": [50.0],
            "total_cost": [1000.0],
            "p_atual": [55.0],
            "v_mercado": [1100.0],
            "pnl": [100.0],
            "yield": [10.0],
            "status": ["✅"],
            "earnings": [5.0],
        }
    )

    result = tables.render_portfolio_table(
        df, _texts(), lambda v: f"{v:.2f}", selectable=True, table_key="test_key"
    )

    # returns the event object (not None)
    assert result is not None
    # on_select and selection_mode must be set
    assert events["kwargs"]["on_select"] == "rerun"
    assert events["kwargs"]["selection_mode"] == "single-row"
    assert events["kwargs"]["key"] == "test_key"
    # the hint column must be present in the styled dataframe
    # verify the "📊" column was inserted into the dataframe passed to st.dataframe
    # (it's the first positional arg, not in kwargs for this fake)
    # recheck via monkeypatched capture
    captured_pos = {}

    def fake_df2(arg, **kw):
        captured_pos["styler"] = arg
        return FakeEvent()

    monkeypatch.setattr(tables.st, "dataframe", fake_df2)
    tables.render_portfolio_table(
        df, _texts(), lambda v: f"{v:.2f}", selectable=True, table_key="k2"
    )
    assert "📊" in captured_pos["styler"].data.columns


def test_render_portfolio_table_with_logos_adds_image_column(monkeypatch):
    captured = {}

    def fake_dataframe(arg, **kwargs):
        captured["arg"] = arg
        captured["kwargs"] = kwargs

    class FakeColumnConfig:
        class ImageColumn:
            def __init__(self, *a, **kw):
                pass

    monkeypatch.setattr(tables.st, "dataframe", fake_dataframe)
    monkeypatch.setattr(tables.st, "column_config", FakeColumnConfig())

    df = pd.DataFrame(
        {
            "ticker": ["PETR4", "HGLG11"],
            "qty": [10, 5],
            "avg_price": [10.0, 100.0],
            "total_cost": [100.0, 500.0],
            "p_atual": [11.0, 105.0],
            "v_mercado": [110.0, 525.0],
            "pnl": [10.0, 25.0],
            "yield": [10.0, 5.0],
            "status": ["✅", "✅"],
            "earnings": [1.0, 2.0],
        }
    )

    logos = {"PETR4": "https://icons.brapi.dev/icons/PETR4.svg", "HGLG11": None}
    tables.render_portfolio_table(df, _texts(), lambda v: f"{v:.2f}", logos=logos)

    styler = captured["arg"]
    logo_col = _texts().get("col_logo", "🏢")
    assert logo_col in styler.data.columns
    assert styler.data[logo_col].iloc[0] == "https://icons.brapi.dev/icons/PETR4.svg"
    assert pd.isna(styler.data[logo_col].iloc[1])
    assert logo_col in captured["kwargs"]["column_config"]


def test_render_portfolio_table_without_logos_has_no_logo_column(monkeypatch):
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

    styler = captured["arg"]
    logo_col = _texts().get("col_logo", "🏢")
    assert logo_col not in styler.data.columns
    assert captured["kwargs"]["column_config"] is None
