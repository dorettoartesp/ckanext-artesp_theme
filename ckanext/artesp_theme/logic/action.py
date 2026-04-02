import ckan.plugins.toolkit as tk
from ckan.logic.action.create import package_create as core_package_create

import ckanext.artesp_theme.logic.schema as schema


@tk.side_effect_free
def artesp_theme_get_sum(context, data_dict):
    tk.check_access("artesp_theme_get_sum", context, data_dict)
    data, errors = tk.navl_validate(data_dict, schema.artesp_theme_get_sum(), context)

    if errors:
        raise tk.ValidationError(errors)

    return {
        "left": data["left"],
        "right": data["right"],
        "sum": data["left"] + data["right"],
    }


def package_create(context, data_dict):
    tk.check_access("package_create", context, data_dict)

    action_context = dict(context)
    action_context["ignore_auth"] = True

    return core_package_create(action_context, dict(data_dict or {}))


def get_actions():
    return {
        "package_create": package_create,
        "artesp_theme_get_sum": artesp_theme_get_sum,
    }
