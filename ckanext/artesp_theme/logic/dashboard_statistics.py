import copy
import datetime
import re
import time
from collections import Counter

import ckan.plugins.toolkit as toolkit


DEFAULT_PERIOD = "12m"
DEFAULT_THEME = "all"
UNGROUPED_THEME = "__ungrouped__"

PERIODS = {
    "6m": {"label": "Últimos 6 meses", "months": 6},
    "12m": {"label": "Últimos 12 meses", "months": 12},
    "24m": {"label": "Últimos 24 meses", "months": 24},
    "all": {"label": "Todo o período", "months": None},
}

_DASHBOARD_CACHE = {}


def clear_dashboard_statistics_cache():
    _DASHBOARD_CACHE.clear()


def get_dashboard_statistics(data_dict=None):
    data_dict = data_dict or {}
    cache_key = _requested_cache_key(data_dict)
    cache_seconds = _get_dashboard_cache_seconds()
    monotonic_now = time.monotonic()
    cached = _DASHBOARD_CACHE.get(cache_key)

    if (
        cache_seconds > 0
        and cached is not None
        and cached["expires_at"] > monotonic_now
    ):
        return copy.deepcopy(cached["payload"])

    datasets = _get_all_public_datasets()
    groups = toolkit.get_action("group_list")(
        {}, {"all_fields": True, "include_datasets": False}
    )
    organizations = toolkit.get_action("organization_list")({}, {"all_fields": False})
    filters = _normalize_filters(data_dict, groups, datasets)
    cache_key = (filters["theme"], filters["period"])
    payload = _build_dashboard_statistics_payload(
        datasets=datasets,
        groups=groups,
        organizations=organizations,
        filters=filters,
        now=_now(),
    )

    if cache_seconds > 0:
        _DASHBOARD_CACHE[cache_key] = {
            "expires_at": monotonic_now + cache_seconds,
            "payload": copy.deepcopy(payload),
        }

    return payload


def _requested_cache_key(data_dict):
    theme = (data_dict.get("theme") or DEFAULT_THEME).strip() or DEFAULT_THEME
    period = (data_dict.get("period") or DEFAULT_PERIOD).strip() or DEFAULT_PERIOD
    return (theme, period)


def _now():
    return datetime.datetime.now()


def _get_dashboard_cache_seconds():
    value = toolkit.config.get("ckanext.artesp_theme.dashboard_cache_seconds", 300)
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 300


def _get_all_public_datasets(page_size=500):
    datasets = []
    start = 0
    total = None
    package_search = toolkit.get_action("package_search")

    while total is None or start < total:
        result = package_search(
            {},
            {
                "rows": page_size,
                "start": start,
                "include_private": False,
                "sort": "metadata_created asc",
            },
        )
        results = result.get("results", [])
        total = result.get("count", len(results))
        if not results:
            break

        datasets.extend(results)
        start += len(results)
        if len(results) < page_size:
            break

    return datasets


def _normalize_filters(data_dict, groups, datasets):
    theme = (data_dict.get("theme") or DEFAULT_THEME).strip() or DEFAULT_THEME
    period = (data_dict.get("period") or DEFAULT_PERIOD).strip() or DEFAULT_PERIOD
    available_themes = _available_theme_options(groups, datasets)
    available_theme_values = {option["value"] for option in available_themes}

    errors = {}
    if period not in PERIODS:
        errors["period"] = ["Período inválido."]
    if theme not in available_theme_values:
        errors["theme"] = ["Tema inválido."]
    if errors:
        raise toolkit.ValidationError(errors)

    theme_label = next(
        option["label"] for option in available_themes if option["value"] == theme
    )
    return {
        "theme": theme,
        "theme_label": theme_label,
        "period": period,
        "period_label": PERIODS[period]["label"],
        "available_themes": available_themes,
        "available_periods": [
            {"value": value, "label": config["label"]}
            for value, config in PERIODS.items()
        ],
    }


def _available_theme_options(groups, datasets):
    options = [{"value": DEFAULT_THEME, "label": "Todos os temas"}]
    seen_values = {DEFAULT_THEME}

    for group in sorted(groups, key=lambda item: (_group_label(item) or "").lower()):
        value = group.get("name")
        label = _group_label(group)
        if value and label and value not in seen_values:
            options.append({"value": value, "label": label})
            seen_values.add(value)

    if any(not dataset.get("groups") for dataset in datasets):
        options.append({"value": UNGROUPED_THEME, "label": "Sem grupo"})

    return options


def _build_dashboard_statistics_payload(datasets, groups, organizations, filters, now):
    filtered_datasets = [
        dataset for dataset in datasets if _dataset_matches_filters(dataset, filters, now)
    ]
    theme_metrics = {}

    for group in groups:
        label = _group_label(group)
        if label:
            theme_metrics[label] = {
                "label": label,
                "dataset_count": 0,
                "resource_count": 0,
            }

    total_resources = 0
    format_counts = Counter()
    timeline_counts = Counter()
    table_rows = []
    datasets_without_theme = 0

    for dataset in filtered_datasets:
        groups_for_dataset = dataset.get("groups", [])
        sorted_groups = sorted(
            filter(None, (_group_label(group) for group in groups_for_dataset)),
            key=lambda value: value.lower(),
        )
        theme_label = sorted_groups[0] if sorted_groups else "Sem grupo"

        if theme_label == "Sem grupo":
            datasets_without_theme += 1

        theme_metrics.setdefault(
            theme_label,
            {"label": theme_label, "dataset_count": 0, "resource_count": 0},
        )

        active_resources = [
            resource
            for resource in dataset.get("resources", [])
            if resource.get("state", "active") == "active"
        ]
        resource_count = len(active_resources)

        theme_metrics[theme_label]["dataset_count"] += 1
        theme_metrics[theme_label]["resource_count"] += resource_count
        total_resources += resource_count

        for resource in active_resources:
            format_label = _resource_format_label(resource)
            if format_label:
                format_counts[format_label] += 1

        created = _parse_datetime(
            dataset.get("metadata_created") or dataset.get("metadata_modified")
        )
        if created:
            timeline_counts[_month_key(created)] += 1

        dataset_formats = sorted(
            {
                label
                for label in (
                    _resource_format_label(resource) for resource in active_resources
                )
                if label
            }
        )
        table_rows.append(
            {
                "name": dataset.get("name"),
                "title": dataset.get("title") or dataset.get("name"),
                "theme": theme_label,
                "resource_count": resource_count,
                "formats_label": ", ".join(dataset_formats[:3]) or "Sem recursos",
                "modified_label": _format_datetime_label(
                    dataset.get("metadata_modified") or dataset.get("metadata_created")
                ),
            }
        )

    dataset_count = len(filtered_datasets)
    theme_count = len([_group_label(group) for group in groups if _group_label(group)])
    empty_theme_count = sum(
        1
        for label, metrics in theme_metrics.items()
        if label != "Sem grupo" and metrics["dataset_count"] == 0
    )
    average_resources = (
        float(total_resources) / float(dataset_count) if dataset_count else 0.0
    )
    resources_by_theme = sorted(
        [
            {"label": item["label"], "value": item["resource_count"]}
            for item in theme_metrics.values()
            if item["resource_count"] > 0
        ],
        key=lambda item: (-item["value"], item["label"].lower()),
    )
    datasets_by_theme = sorted(
        [
            {"label": item["label"], "value": item["dataset_count"]}
            for item in theme_metrics.values()
            if item["dataset_count"] > 0
        ],
        key=lambda item: (-item["value"], item["label"].lower()),
    )
    format_series = sorted(
        [{"label": label, "value": value} for label, value in format_counts.items()],
        key=lambda item: (-item["value"], item["label"].lower()),
    )
    timeline_series = [
        {
            "label": month_info["label"],
            "value": timeline_counts.get(month_info["key"], 0),
        }
        for month_info in _timeline_window(filters["period"], now, filtered_datasets)
    ]

    table_rows.sort(key=lambda row: (-row["resource_count"], row["title"].lower()))
    for index, row in enumerate(table_rows, start=1):
        share_percent = (
            (float(row["resource_count"]) / float(total_resources)) * 100.0
            if total_resources
            else 0.0
        )
        row["rank"] = index
        row["share_label"] = _format_decimal_label(share_percent)
        row["share_percent"] = round(share_percent, 1)

    top_datasets = [
        {"label": row["title"], "value": row["resource_count"]}
        for row in table_rows[:10]
        if row["resource_count"] > 0
    ]
    dominant_theme = resources_by_theme[0] if resources_by_theme else None
    largest_dataset = table_rows[0] if table_rows else None
    top_format = format_series[0] if format_series else None
    topic_labels = [
        label
        for label in sorted(theme_metrics, key=lambda value: value.lower())
        if label != "Sem grupo"
    ]
    if datasets_without_theme:
        topic_labels.append("Sem grupo")

    return {
        "generated_at_label": now.strftime("%d/%m/%Y %H:%M"),
        "has_data": dataset_count > 0,
        "filters": filters,
        "kpis": {
            "dataset_count": dataset_count,
            "resource_count": total_resources,
            "theme_count": theme_count,
            "format_count": len(format_series),
            "organization_count": len(organizations),
            "average_resources_per_dataset": average_resources,
            "average_resources_per_dataset_label": _format_decimal_label(
                average_resources
            ),
            "empty_theme_count": empty_theme_count,
            "datasets_without_theme_count": datasets_without_theme,
        },
        "topic_labels": topic_labels,
        "insights": _build_insights(dominant_theme, largest_dataset, top_format),
        "charts": {
            "resources_by_theme": _with_percent(
                _limit_chart_items(resources_by_theme, max_items=10)
            ),
            "datasets_by_theme": _with_percent(
                _limit_chart_items(datasets_by_theme, max_items=10)
            ),
            "timeline": _with_percent(timeline_series),
            "top_datasets": _with_percent(top_datasets),
            "formats": _with_percent(_limit_chart_items(format_series, max_items=8)),
        },
        "table_rows": table_rows[:20],
        "table_total_count": len(table_rows),
    }


def _dataset_matches_filters(dataset, filters, now):
    if not _dataset_matches_theme(dataset, filters["theme"]):
        return False

    created = _parse_datetime(
        dataset.get("metadata_created") or dataset.get("metadata_modified")
    )
    period_start = _period_start(filters["period"], now)
    return period_start is None or (created is not None and created >= period_start)


def _dataset_matches_theme(dataset, theme):
    if theme == DEFAULT_THEME:
        return True
    if theme == UNGROUPED_THEME:
        return not dataset.get("groups")
    return any(group.get("name") == theme for group in dataset.get("groups", []))


def _period_start(period, now):
    months = PERIODS[period]["months"]
    if months is None:
        return None
    return _shift_month(now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), -(months - 1))


def _timeline_window(period, now, datasets):
    months = PERIODS[period]["months"]
    if months is not None:
        return _rolling_month_window(months=months, now=now)

    parsed_dates = [
        parsed
        for parsed in (
            _parse_datetime(
                dataset.get("metadata_created") or dataset.get("metadata_modified")
            )
            for dataset in datasets
        )
        if parsed
    ]
    if not parsed_dates:
        return _rolling_month_window(months=12, now=now)

    start = min(parsed_dates).replace(day=1)
    end = now.replace(day=1)
    months_count = ((end.year - start.year) * 12) + (end.month - start.month) + 1
    return _rolling_month_window(months=max(1, months_count), now=now)


def _rolling_month_window(months=12, now=None):
    if now is None:
        now = _now()

    return [
        {
            "key": "{:04d}-{:02d}".format(current.year, current.month),
            "label": _month_label(current.year, current.month),
        }
        for current in (
            _shift_month(now.replace(day=1), -offset)
            for offset in range(months - 1, -1, -1)
        )
    ]


def _shift_month(value, delta):
    month_index = (value.year * 12) + (value.month - 1) + delta
    year = month_index // 12
    month = (month_index % 12) + 1
    return value.replace(year=year, month=month)


def _build_insights(dominant_theme, largest_dataset, top_format):
    return [
        {
            "title": (
                "{label} concentra {value} recurso(s)".format(
                    label=dominant_theme["label"], value=dominant_theme["value"]
                )
                if dominant_theme
                else "Ainda não há recursos publicados"
            ),
            "description": (
                "Tema com maior volume de arquivos e links publicados."
                if dominant_theme
                else "Assim que houver recursos públicos, o painel exibirá a liderança temática."
            ),
        },
        {
            "title": (
                "{title} reúne {value} recurso(s)".format(
                    title=largest_dataset["title"],
                    value=largest_dataset["resource_count"],
                )
                if largest_dataset
                else "Nenhum conjunto de dados publicado até o momento"
            ),
            "description": (
                "Conjunto com maior volume de recursos públicos no catálogo."
                if largest_dataset
                else "A tabela resumida aparecerá assim que o catálogo tiver conjuntos públicos."
            ),
        },
        {
            "title": (
                "{label} é o formato mais recorrente".format(
                    label=top_format["label"]
                )
                if top_format
                else "Os formatos ainda não puderam ser consolidados"
            ),
            "description": (
                "Formato de publicação mais frequente entre os recursos ativos."
                if top_format
                else "Os formatos serão consolidados assim que houver recursos com metadados preenchidos."
            ),
        },
    ]


def _with_percent(items):
    if not items:
        return []
    max_value = max(item["value"] for item in items) or 1
    return [
        dict(item, percent=round((float(item["value"]) / float(max_value)) * 100.0, 1))
        for item in items
    ]


def _group_label(group_dict):
    if not group_dict:
        return None
    return (
        group_dict.get("display_name")
        or group_dict.get("title")
        or group_dict.get("name")
    )


def _resource_format_label(resource_dict):
    if not resource_dict:
        return None

    raw_value = (
        resource_dict.get("format")
        or resource_dict.get("mimetype")
        or resource_dict.get("mimetype_inner")
        or ""
    ).strip()
    if not raw_value:
        return None

    normalized = re.sub(r"\s+", " ", raw_value)
    if "/" in normalized:
        normalized = normalized.split("/", 1)[1]
    if "." in normalized and "/" not in raw_value:
        normalized = normalized.rsplit(".", 1)[-1]
    return normalized.upper()


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        return value
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_datetime_label(value):
    parsed = _parse_datetime(value)
    if not parsed:
        return "Sem registro"
    return parsed.strftime("%d/%m/%Y")


def _format_decimal_label(value, precision=1):
    format_string = "{:." + str(precision) + "f}"
    return format_string.format(value).replace(".", ",")


def _month_key(value):
    return value.strftime("%Y-%m")


def _month_label(year, month):
    return "{:02d}/{:04d}".format(month, year)


def _limit_chart_items(items, max_items=10):
    if len(items) <= max_items:
        return items

    head = items[:max_items]
    tail = items[max_items:]
    tail_total = sum(item["value"] for item in tail)
    if tail_total:
        head.append({"label": "Outros", "value": tail_total})
    return head
