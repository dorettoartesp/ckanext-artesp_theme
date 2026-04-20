import ckan.plugins.toolkit as tk


def artesp_theme_get_sum():
    not_empty = tk.get_validator("not_empty")
    convert_int = tk.get_validator("convert_int")

    return {
        "left": [not_empty, convert_int],
        "right": [not_empty, convert_int]
    }


def dataset_rating_upsert_schema():
    not_empty = tk.get_validator("not_empty")
    ignore_missing = tk.get_validator("ignore_missing")
    rating_overall = tk.get_validator("rating_overall_validator")
    rating_criteria = tk.get_validator("rating_criteria_validator")
    rating_comment = tk.get_validator("rating_comment_validator")

    return {
        "package_id": [not_empty],
        "overall_rating": [not_empty, rating_overall],
        "criteria": [ignore_missing, rating_criteria],
        "comment": [ignore_missing, rating_comment],
    }


def dataset_rating_show_schema():
    not_empty = tk.get_validator("not_empty")
    return {"package_id": [not_empty]}


def dataset_rating_summary_schema():
    not_empty = tk.get_validator("not_empty")
    return {"package_id": [not_empty]}
