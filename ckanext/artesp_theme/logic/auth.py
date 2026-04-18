import ckan.plugins.toolkit as tk

from ckanext.artesp_theme.logic import auth_helpers


@tk.auth_allow_anonymous_access
def artesp_theme_get_sum(context, data_dict):
    return {"success": True}


@tk.auth_allow_anonymous_access
def artesp_theme_dashboard_statistics(context, data_dict=None):
    return {"success": True}


def request_reset(context, data_dict=None):
    if _ldap_password_reset_disabled():
        return auth_helpers.deny(
            "Password reset is disabled for LDAP users. Use the institutional password recovery flow."
        )
    return auth_helpers.allow()


def user_reset(context, data_dict=None):
    if _ldap_password_reset_disabled():
        return auth_helpers.deny(
            "Password reset is disabled for LDAP users. Use the institutional password recovery flow."
        )
    return auth_helpers.allow()


def _deny_if_external(context):
    user = auth_helpers.get_authenticated_user(context)
    if auth_helpers.is_external_user(user):
        return auth_helpers.deny("External users cannot perform write operations.")
    return None


def package_create(context, data_dict=None):
    if (guard := _deny_if_external(context)):
        return guard
    if auth_helpers.is_sysadmin(context):
        return auth_helpers.allow()

    user = auth_helpers.get_authenticated_user(context)
    if not auth_helpers.is_valid_user(user):
        return auth_helpers.deny("Authentication is required to create datasets.")

    artesp_org = auth_helpers.get_artesp_org()
    if not artesp_org:
        return auth_helpers.deny("The ARTESP organization is not available.")

    data_dict = data_dict or {}

    if not data_dict:
        return auth_helpers.allow()

    if "owner_org" not in data_dict or not data_dict.get("owner_org"):
        return auth_helpers.deny("Datasets must define owner_org.")

    if not auth_helpers.is_artesp_owner_org(data_dict.get("owner_org")):
        return auth_helpers.deny(
            "Datasets can only be created in the ARTESP organization."
        )

    return auth_helpers.allow()


def organization_create(context, data_dict=None):
    return _sysadmin_only_management_operation(
        context,
        "Only sysadmins can create organizations.",
    )


def organization_update(context, data_dict=None):
    return _sysadmin_only_management_operation(
        context,
        "Only sysadmins can update organizations.",
    )


def organization_delete(context, data_dict=None):
    return _sysadmin_only_management_operation(
        context,
        "Only sysadmins can delete organizations.",
    )


def group_create(context, data_dict=None):
    return _sysadmin_only_management_operation(
        context,
        "Only sysadmins can create groups.",
    )


def group_update(context, data_dict=None):
    return _sysadmin_only_management_operation(
        context,
        "Only sysadmins can update groups.",
    )


def group_delete(context, data_dict=None):
    return _sysadmin_only_management_operation(
        context,
        "Only sysadmins can delete groups.",
    )


def _sysadmin_only_management_operation(context, message):
    if (guard := _deny_if_external(context)):
        return guard
    if auth_helpers.is_sysadmin(context):
        return auth_helpers.allow()

    user = auth_helpers.get_authenticated_user(context)
    if not auth_helpers.is_valid_user(user):
        return auth_helpers.deny(message)

    return auth_helpers.deny(message)


def package_update(context, data_dict=None):
    return _authorize_package_operation(
        context,
        data_dict,
        operation_label="edit",
        missing_identifier_message="A dataset id is required to edit a dataset.",
    )


def package_delete(context, data_dict=None):
    return _authorize_package_operation(
        context,
        data_dict,
        operation_label="delete",
        missing_identifier_message="A dataset id is required to delete a dataset.",
    )


def resource_create(context, data_dict=None):
    return _authorize_resource_operation(
        context,
        data_dict,
        operation_label="create",
        action_noun="resources on",
        resource_must_exist=False,
    )


def resource_update(context, data_dict=None):
    return _authorize_resource_operation(
        context,
        data_dict,
        operation_label="edit",
        action_noun="this resource in",
        resource_must_exist=True,
    )


def resource_delete(context, data_dict=None):
    return _authorize_resource_operation(
        context,
        data_dict,
        operation_label="delete",
        action_noun="this resource from",
        resource_must_exist=True,
    )


def package_collaborator_list(context, data_dict=None):
    return _authorize_collaborator_operation(
        context,
        data_dict,
        operation_label="list",
        require_target_user=False,
        validate_requested_capacity=False,
    )


def package_collaborator_create(context, data_dict=None):
    return _authorize_collaborator_operation(
        context,
        data_dict,
        operation_label="manage",
        require_target_user=True,
        validate_requested_capacity=True,
    )


def package_collaborator_delete(context, data_dict=None):
    return _authorize_collaborator_operation(
        context,
        data_dict,
        operation_label="manage",
        require_target_user=True,
        validate_requested_capacity=False,
        require_existing_collaborator=True,
        guard_self_removal=True,
    )


def get_auth_functions():
    return {
        "artesp_theme_dashboard_statistics": artesp_theme_dashboard_statistics,
        "artesp_theme_get_sum": artesp_theme_get_sum,
        "request_reset": request_reset,
        "user_reset": user_reset,
        "organization_create": organization_create,
        "organization_update": organization_update,
        "organization_delete": organization_delete,
        "group_create": group_create,
        "group_update": group_update,
        "group_delete": group_delete,
        "package_create": package_create,
        "package_update": package_update,
        "package_delete": package_delete,
        "resource_create": resource_create,
        "resource_update": resource_update,
        "resource_delete": resource_delete,
        "package_collaborator_list": package_collaborator_list,
        "package_collaborator_create": package_collaborator_create,
        "package_collaborator_delete": package_collaborator_delete,
    }


def _ldap_password_reset_disabled():
    return bool(tk.config.get("ckanext.ldap.uri", ""))


def _authorize_package_operation(
    context,
    data_dict,
    operation_label,
    missing_identifier_message,
):
    data_dict = data_dict or {}

    if (guard := _deny_if_external(context)):
        return guard
    if auth_helpers.is_sysadmin(context):
        return auth_helpers.allow()

    user = auth_helpers.get_authenticated_user(context)
    if not auth_helpers.is_valid_user(user):
        return auth_helpers.deny(
            "Authentication is required to {} datasets.".format(operation_label)
        )

    if not data_dict or not (
        data_dict.get("id") or data_dict.get("name") or data_dict.get("package_id")
    ):
        return auth_helpers.deny(missing_identifier_message)

    package = auth_helpers.get_package(data_dict)
    if not package:
        return auth_helpers.deny("Dataset not found.")

    if not auth_helpers.dataset_belongs_to_artesp(package):
        return auth_helpers.deny(
            "Only datasets owned by the ARTESP organization can be managed."
        )

    if "owner_org" in data_dict and not auth_helpers.is_artesp_owner_org(
        data_dict.get("owner_org")
    ):
        return auth_helpers.deny(
            "Datasets cannot be moved outside the ARTESP organization."
        )

    if auth_helpers.user_can_edit_package(package, user):
        return auth_helpers.allow()

    return auth_helpers.deny(
        "You are not allowed to {} this dataset.".format(operation_label)
    )


def _authorize_resource_operation(
    context,
    data_dict,
    operation_label,
    action_noun,
    resource_must_exist,
):
    data_dict = data_dict or {}

    if (guard := _deny_if_external(context)):
        return guard
    if auth_helpers.is_sysadmin(context):
        return auth_helpers.allow()

    user = auth_helpers.get_authenticated_user(context)
    if not auth_helpers.is_valid_user(user):
        return auth_helpers.deny(
            "Authentication is required to {} resources.".format(operation_label)
        )

    if not data_dict:
        return auth_helpers.deny("Resource operations require a payload.")

    if resource_must_exist:
        resource = auth_helpers.get_resource(data_dict)
        if not resource:
            return auth_helpers.deny("Resource not found.")
        package = auth_helpers.get_package_from_resource({"id": resource.id})
    else:
        package = auth_helpers.get_package_from_resource(data_dict)

    if not package:
        return auth_helpers.deny("The parent dataset could not be resolved.")

    if not auth_helpers.dataset_belongs_to_artesp(package):
        return auth_helpers.deny(
            "Resources can only be managed for datasets owned by the ARTESP organization."
        )

    if auth_helpers.user_can_edit_package(package, user):
        return auth_helpers.allow()

    return auth_helpers.deny(
        "You are not allowed to {} {} dataset {}.".format(
            operation_label,
            action_noun,
            package.name,
        )
    )


def _authorize_collaborator_operation(
    context,
    data_dict,
    operation_label,
    require_target_user,
    validate_requested_capacity,
    require_existing_collaborator=False,
    guard_self_removal=False,
):
    data_dict = data_dict or {}

    if auth_helpers.is_sysadmin(context):
        return auth_helpers.allow()

    user = auth_helpers.get_authenticated_user(context)
    if not auth_helpers.is_valid_user(user):
        return auth_helpers.deny(
            "Authentication is required to {} dataset collaborators.".format(
                operation_label
            )
        )

    if not auth_helpers.is_dataset_collaborators_enabled():
        return auth_helpers.deny("Dataset collaborators are disabled.")

    if not data_dict or not data_dict.get("id"):
        return auth_helpers.deny("A dataset id is required to manage collaborators.")

    package = auth_helpers.get_package(data_dict)
    if not package:
        return auth_helpers.deny("Dataset not found.")

    if not auth_helpers.dataset_belongs_to_artesp(package):
        return auth_helpers.deny(
            "Collaborators can only be managed on ARTESP datasets."
        )

    if not auth_helpers.user_can_manage_collaborators(package, user):
        return auth_helpers.deny(
            "You are not allowed to manage collaborators for this dataset."
        )

    if validate_requested_capacity:
        capacity = data_dict.get("capacity")
        if not capacity and auth_helpers.is_sysadmin(context):
            return auth_helpers.deny("A collaborator capacity is required.")
        if not capacity:
            capacity = auth_helpers.get_default_dataset_collaborator_capacity()
        if not auth_helpers.requested_capacity_is_allowed(capacity):
            if capacity == auth_helpers.ADMIN_CAPACITY:
                return auth_helpers.deny("Admin collaborators are disabled.")
            return auth_helpers.deny("Invalid collaborator capacity.")
        if (
            not auth_helpers.is_sysadmin(context)
            and capacity != auth_helpers.get_default_dataset_collaborator_capacity()
        ):
            return auth_helpers.deny("Only sysadmins can change collaborator roles.")

    target_user = None
    if require_target_user:
        target_user = auth_helpers.get_target_user(data_dict)
        if not target_user:
            return auth_helpers.deny("Collaborator user not found.")

    if (
        validate_requested_capacity
        and target_user
        and not auth_helpers.is_sysadmin(context)
    ):
        collaborator = auth_helpers.get_collaborator_by_user_id(package, target_user.id)
        if collaborator:
            return auth_helpers.deny("Only sysadmins can change collaborator roles.")

    if require_existing_collaborator:
        collaborator = auth_helpers.get_collaborator_by_user_id(package, target_user.id)
        if not collaborator:
            return auth_helpers.deny("Collaborator membership not found.")

    if (
        guard_self_removal
        and target_user
        and target_user.id == user.id
        and not auth_helpers.package_belongs_to_user(package, user)
        and auth_helpers.would_orphan_collaborator_governance(package, target_user.id)
    ):
        return auth_helpers.deny(
            "You cannot remove your own collaborator role from this dataset."
        )

    return auth_helpers.allow()
