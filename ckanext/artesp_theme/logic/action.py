import ckan.plugins.toolkit as tk
from ckan.logic.action.create import (
    package_collaborator_create as core_package_collaborator_create,
)
from ckan.logic.action.create import package_create as core_package_create

import ckanext.artesp_theme.logic.schema as schema
from ckanext.artesp_theme.logic import auth_helpers


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

    if not data_dict or not data_dict.get("owner_org"):
        raise tk.NotAuthorized(tk._("Datasets must define owner_org."))

    if not auth_helpers.is_artesp_owner_org(data_dict.get("owner_org")):
        raise tk.NotAuthorized(
            tk._("Datasets can only be created in the ARTESP organization.")
        )

    action_context = dict(context)
    action_context["ignore_auth"] = True

    return core_package_create(action_context, dict(data_dict or {}))


def package_collaborator_create(context, data_dict):
    normalized_data = auth_helpers.normalize_package_collaborator_create_data(
        context, data_dict
    )
    tk.check_access("package_collaborator_create", context, normalized_data)

    action_context = dict(context)
    action_context["ignore_auth"] = True

    return core_package_collaborator_create(action_context, normalized_data)


def get_actions():
    return {
        "package_create": package_create,
        "package_collaborator_create": package_collaborator_create,
        "artesp_theme_get_sum": artesp_theme_get_sum,
    }
