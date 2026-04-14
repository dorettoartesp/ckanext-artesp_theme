"""Tests for helpers.py."""

import ckanext.artesp_theme.helpers as helpers


def test_artesp_theme_hello():
    assert helpers.artesp_theme_hello() == "Hello, artesp_theme!"


def test_get_dashboard_statistics_delegates_to_dashboard_module(monkeypatch):
    captured = {}

    def fake_get_dashboard_statistics(data_dict=None):
        captured["data_dict"] = dict(data_dict or {})
        return {"ok": True}

    monkeypatch.setattr(
        helpers.dashboard_statistics,
        "get_dashboard_statistics",
        fake_get_dashboard_statistics,
    )

    assert helpers.get_dashboard_statistics({"period": "6m"}) == {"ok": True}
    assert captured["data_dict"] == {"period": "6m"}


def test_clear_dashboard_statistics_cache_delegates_to_dashboard_module(monkeypatch):
    captured = {"called": False}

    def fake_clear():
        captured["called"] = True

    monkeypatch.setattr(
        helpers.dashboard_statistics,
        "clear_dashboard_statistics_cache",
        fake_clear,
    )

    helpers.clear_dashboard_statistics_cache()

    assert captured["called"] is True
