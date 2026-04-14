"""Tests for dashboard statistics aggregation."""

import datetime

import pytest
import ckan.plugins.toolkit as tk

from ckanext.artesp_theme.logic import dashboard_statistics


def _dataset(
    name,
    title,
    group_name,
    group_title,
    created,
    resources,
):
    groups = []
    if group_name:
        groups.append({"name": group_name, "title": group_title})

    return {
        "name": name,
        "title": title,
        "groups": groups,
        "resources": resources,
        "metadata_created": created,
        "metadata_modified": created,
    }


def _install_fake_actions(monkeypatch, datasets):
    groups = [
        {"name": "rodoviario", "title": "Rodoviário"},
        {"name": "legislacao", "title": "Legislação"},
        {"name": "aeroportuario", "title": "Aeroportuário"},
    ]
    organizations = ["artesp"]
    calls = {"package_search": []}

    def fake_get_action(name):
        if name == "package_search":
            def _package_search(context, data_dict):
                calls["package_search"].append(dict(data_dict))
                start = data_dict.get("start", 0)
                rows = data_dict.get("rows", 500)
                return {
                    "count": len(datasets),
                    "results": datasets[start:start + rows],
                }
            return _package_search
        if name == "group_list":
            return lambda context, data_dict: groups
        if name == "organization_list":
            return lambda context, data_dict: organizations
        raise AssertionError("Unexpected action: {0}".format(name))

    monkeypatch.setattr(
        dashboard_statistics.toolkit,
        "config",
        {"ckanext.artesp_theme.dashboard_cache_seconds": 0},
        raising=False,
    )
    monkeypatch.setattr(dashboard_statistics.toolkit, "get_action", fake_get_action)
    monkeypatch.setattr(
        dashboard_statistics,
        "_now",
        lambda: datetime.datetime(2026, 4, 14, 12, 0),
    )
    dashboard_statistics.clear_dashboard_statistics_cache()
    return calls


def test_dashboard_statistics_filters_by_theme_and_period(monkeypatch):
    datasets = [
        _dataset(
            "acidentes-2026",
            "Acidentes 2026",
            "rodoviario",
            "Rodoviário",
            "2026-03-10T00:00:00",
            [{"format": "CSV", "state": "active"}],
        ),
        _dataset(
            "pedagios-2025",
            "Pedágios 2025",
            "rodoviario",
            "Rodoviário",
            "2025-08-10T00:00:00",
            [{"format": "PDF", "state": "active"}],
        ),
        _dataset(
            "portarias-2026",
            "Portarias 2026",
            "legislacao",
            "Legislação",
            "2026-03-11T00:00:00",
            [{"format": "PDF", "state": "active"}],
        ),
        _dataset(
            "rodovias-antigo",
            "Rodovias antigo",
            "rodoviario",
            "Rodoviário",
            "2024-01-10T00:00:00",
            [{"format": "XLSX", "state": "active"}],
        ),
        _dataset(
            "sem-grupo",
            "Sem grupo",
            None,
            None,
            "2026-02-10T00:00:00",
            [{"format": "ZIP", "state": "active"}],
        ),
    ]
    _install_fake_actions(monkeypatch, datasets)

    payload = dashboard_statistics.get_dashboard_statistics(
        {"theme": "rodoviario", "period": "12m"}
    )

    assert payload["filters"]["theme"] == "rodoviario"
    assert payload["filters"]["theme_label"] == "Rodoviário"
    assert payload["filters"]["period"] == "12m"
    assert payload["filters"]["period_label"] == "Últimos 12 meses"
    assert payload["kpis"]["dataset_count"] == 2
    assert payload["kpis"]["resource_count"] == 2
    assert payload["kpis"]["datasets_without_theme_count"] == 0
    assert payload["charts"]["formats"] == [
        {"label": "CSV", "value": 1, "percent": 100.0},
        {"label": "PDF", "value": 1, "percent": 100.0},
    ]
    assert [row["name"] for row in payload["table_rows"]] == [
        "acidentes-2026",
        "pedagios-2025",
    ]
    assert {item["value"] for item in payload["filters"]["available_themes"]} >= {
        "all",
        "rodoviario",
        "legislacao",
        "__ungrouped__",
    }


def test_dashboard_statistics_supports_ungrouped_and_all_period(monkeypatch):
    datasets = [
        _dataset(
            "sem-grupo",
            "Sem grupo",
            None,
            None,
            "2024-01-10T00:00:00",
            [{"format": "application/zip", "state": "active"}],
        )
    ]
    _install_fake_actions(monkeypatch, datasets)

    payload = dashboard_statistics.get_dashboard_statistics(
        {"theme": "__ungrouped__", "period": "all"}
    )

    assert payload["filters"]["theme_label"] == "Sem grupo"
    assert payload["filters"]["period_label"] == "Todo o período"
    assert payload["kpis"]["dataset_count"] == 1
    assert payload["charts"]["formats"] == [
        {"label": "ZIP", "value": 1, "percent": 100.0}
    ]


def test_dashboard_statistics_cache_is_scoped_by_filter(monkeypatch):
    datasets = []
    calls = _install_fake_actions(monkeypatch, datasets)
    monkeypatch.setattr(
        dashboard_statistics.toolkit,
        "config",
        {"ckanext.artesp_theme.dashboard_cache_seconds": 300},
        raising=False,
    )

    dashboard_statistics.get_dashboard_statistics({"theme": "all", "period": "6m"})
    dashboard_statistics.get_dashboard_statistics({"theme": "all", "period": "6m"})
    dashboard_statistics.get_dashboard_statistics({"theme": "all", "period": "12m"})

    assert len(calls["package_search"]) == 2


@pytest.mark.parametrize(
    "data_dict,error_key",
    [
        ({"theme": "nao-existe", "period": "12m"}, "theme"),
        ({"theme": "all", "period": "36m"}, "period"),
    ],
)
def test_dashboard_statistics_rejects_invalid_filters(
    monkeypatch,
    data_dict,
    error_key,
):
    _install_fake_actions(monkeypatch, [])

    with pytest.raises(tk.ValidationError) as exc:
        dashboard_statistics.get_dashboard_statistics(data_dict)

    assert error_key in exc.value.error_dict
