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
    group_id=None,
):
    groups = []
    if group_name:
        group = {"name": group_name, "title": group_title}
        if group_id:
            group["id"] = group_id
        groups.append(group)

    return {
        "name": name,
        "title": title,
        "groups": groups,
        "resources": resources,
        "metadata_created": created,
        "metadata_modified": created,
    }


def _install_fake_actions(monkeypatch, datasets, groups=None):
    groups = groups or [
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


def test_dashboard_statistics_canonicalizes_stale_group_labels(monkeypatch):
    groups = [
        {"id": "theme-road", "name": "rodovias", "title": "Rodovias"},
    ]
    datasets = [
        _dataset(
            "ds-transp",
            "Transporte antigo",
            "transp-rodoviario",
            "Transp. Rodoviário",
            "2026-03-01T00:00:00",
            [{"format": "CSV", "state": "active"}] * 2,
            group_id="theme-road",
        ),
        _dataset(
            "ds-rodo",
            "Rodoviário intermediário",
            "rodoviario",
            "Rodoviário",
            "2026-03-02T00:00:00",
            [{"format": "CSV", "state": "active"}] * 3,
            group_id="theme-road",
        ),
        _dataset(
            "ds-rodovias",
            "Rodovias atual",
            "rodovias",
            "Rodovias",
            "2026-03-03T00:00:00",
            [{"format": "CSV", "state": "active"}],
            group_id="theme-road",
        ),
    ]
    _install_fake_actions(monkeypatch, datasets, groups=groups)

    payload = dashboard_statistics.get_dashboard_statistics(
        {"theme": "rodovias", "period": "all"}
    )

    assert payload["kpis"]["dataset_count"] == 3
    assert payload["kpis"]["resource_count"] == 6
    assert payload["filters"]["available_themes"] == [
        {"value": "all", "label": "Todos os temas"},
        {"value": "rodovias", "label": "Rodovias"},
    ]
    assert payload["charts"]["resources_by_theme"] == [
        {"label": "Rodovias", "value": 6, "percent": 100.0}
    ]
    assert payload["charts"]["datasets_by_theme"] == [
        {"label": "Rodovias", "value": 3, "percent": 100.0}
    ]
    assert {row["theme"] for row in payload["table_rows"]} == {"Rodovias"}


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


# ── Rating stats ────────────────────────────────────────────────────────────


def _fake_rating(package_id, overall_rating, criteria=None):
    class _R:
        pass
    r = _R()
    r.package_id = package_id
    r.overall_rating = overall_rating
    r.criteria = criteria or {}
    return r


def _install_fake_session(monkeypatch, ratings):
    import ckan.model as ckan_model

    class _Q:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return ratings

    class _S:
        @staticmethod
        def query(cls):
            return _Q()

    monkeypatch.setattr(ckan_model, "Session", _S)


def test_rating_stats_empty_when_no_ratings(monkeypatch):
    _install_fake_session(monkeypatch, [])
    result = dashboard_statistics._get_rating_stats(["pkg1"], {"pkg1": {"name": "ds1", "title": "DS1", "groups": []}})
    assert result["total_ratings"] == 0
    assert result["average"] is None
    assert result["average_label"] == "—"
    assert result["rated_dataset_count"] == 0
    assert result["top_rated"] == []


def test_rating_stats_empty_when_no_package_ids(monkeypatch):
    _install_fake_session(monkeypatch, [])
    result = dashboard_statistics._get_rating_stats([], {})
    assert result["total_ratings"] == 0
    assert result["average"] is None


def test_rating_average_and_count(monkeypatch):
    ratings = [
        _fake_rating("pkg1", 4),
        _fake_rating("pkg1", 2),
    ]
    _install_fake_session(monkeypatch, ratings)
    ds_lookup = {"pkg1": {"id": "pkg1", "name": "ds1", "title": "DS1", "groups": []}}
    result = dashboard_statistics._get_rating_stats(["pkg1"], ds_lookup)
    assert result["total_ratings"] == 2
    assert result["average"] == 3.0
    assert result["rated_dataset_count"] == 1


def test_rating_criteria_pct(monkeypatch):
    ratings = [
        _fake_rating("pkg1", 5, {"links_work": True}),
        _fake_rating("pkg2", 3, {"links_work": False}),
    ]
    _install_fake_session(monkeypatch, ratings)
    ds_lookup = {
        "pkg1": {"id": "pkg1", "name": "ds1", "title": "DS1", "groups": []},
        "pkg2": {"id": "pkg2", "name": "ds2", "title": "DS2", "groups": []},
    }
    result = dashboard_statistics._get_rating_stats(["pkg1", "pkg2"], ds_lookup)
    assert result["criteria"]["links_work"] == 50.0


def test_rating_criteria_none_when_no_votes(monkeypatch):
    ratings = [_fake_rating("pkg1", 3, {})]
    _install_fake_session(monkeypatch, ratings)
    ds_lookup = {"pkg1": {"id": "pkg1", "name": "ds1", "title": "DS1", "groups": []}}
    result = dashboard_statistics._get_rating_stats(["pkg1"], ds_lookup)
    assert result["criteria"]["links_work"] is None
    assert result["criteria"]["up_to_date"] is None
    assert result["criteria"]["well_structured"] is None


def test_rating_top_rated_order(monkeypatch):
    ratings = [
        _fake_rating("pkg1", 2),
        _fake_rating("pkg2", 5),
        _fake_rating("pkg3", 4),
    ]
    _install_fake_session(monkeypatch, ratings)
    ds_lookup = {
        "pkg1": {"id": "pkg1", "name": "ds1", "title": "DS1", "groups": []},
        "pkg2": {"id": "pkg2", "name": "ds2", "title": "DS2", "groups": []},
        "pkg3": {"id": "pkg3", "name": "ds3", "title": "DS3", "groups": []},
    }
    result = dashboard_statistics._get_rating_stats(["pkg1", "pkg2", "pkg3"], ds_lookup)
    averages = [item["average"] for item in result["top_rated"]]
    assert averages == sorted(averages, reverse=True)
    assert result["top_rated"][0]["name"] == "ds2"


def test_rating_respects_theme_filter(monkeypatch):
    datasets = [
        _dataset("ds-rodo", "Rodo", "rodoviario", "Rodoviário", "2026-03-01T00:00:00",
                 [{"format": "CSV", "state": "active"}]),
        _dataset("ds-leg", "Leg", "legislacao", "Legislação", "2026-03-01T00:00:00",
                 [{"format": "PDF", "state": "active"}]),
    ]

    rodo_pkg_id = "rodo-id"
    leg_pkg_id = "leg-id"
    datasets[0]["id"] = rodo_pkg_id
    datasets[1]["id"] = leg_pkg_id

    _install_fake_actions(monkeypatch, datasets)

    ratings_seen = []

    class _Q:
        def filter(self, condition):
            # capture which package_ids were queried
            return self
        def all(self):
            return ratings_seen

    class _S:
        @staticmethod
        def query(cls):
            return _Q()

    import ckan.model as ckan_model
    monkeypatch.setattr(ckan_model, "Session", _S)

    payload = dashboard_statistics.get_dashboard_statistics({"theme": "rodoviario", "period": "all"})
    assert payload["rating"]["total_ratings"] == 0
    assert "rating" in payload


def test_rating_included_in_payload(monkeypatch):
    datasets = [
        _dataset("ds1", "Dataset 1", "rodoviario", "Rodoviário", "2026-03-01T00:00:00",
                 [{"format": "CSV", "state": "active"}]),
    ]
    datasets[0]["id"] = "pkg-id-1"
    _install_fake_actions(monkeypatch, datasets)

    ratings = [_fake_rating("pkg-id-1", 4)]

    import ckan.model as ckan_model

    class _Q:
        def filter(self, *a, **kw):
            return self
        def all(self):
            return ratings

    class _S:
        @staticmethod
        def query(cls):
            return _Q()

    monkeypatch.setattr(ckan_model, "Session", _S)

    payload = dashboard_statistics.get_dashboard_statistics({"theme": "all", "period": "all"})
    assert "rating" in payload
    assert payload["rating"]["total_ratings"] == 1
    assert payload["rating"]["average"] == 4.0
    assert payload["kpis"]["average_rating_label"] == "4,0"
