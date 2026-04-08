from __future__ import annotations

import ckan.authz as authz
import ckan.model as model
import ckan.plugins.toolkit as tk


DEFAULT_ARTESP_ORG_IDENTIFIER = u"artesp"
DEFAULT_ARTESP_ORG_TITLE = u"ARTESP"
DEFAULT_DATASET_COLLABORATOR_CAPACITY = u"editor"
EDIT_CAPACITIES = ("editor", "admin")
ADMIN_CAPACITY = "admin"


def allow():
    return {"success": True}


def deny(message):
    return {"success": False, "msg": tk._(message)}


def get_authenticated_user(context):
    context = context or {}
    user_obj = context.get("auth_user_obj")
    if user_obj and getattr(user_obj, "id", None):
        return user_obj

    username = context.get("user")
    if not username:
        return None

    return model.User.get(username)


def get_user(user_identifier):
    if not user_identifier:
        return None

    return model.User.get(user_identifier)


def find_local_user_by_identifier(user_identifier):
    user = get_user(user_identifier)
    if user:
        return user

    if not user_identifier:
        return None

    return (
        model.Session.query(model.User)
        .filter(model.User.email == user_identifier)
        .filter(model.User.state == "active")
        .one_or_none()
    )


def is_valid_user(user):
    return bool(user and getattr(user, "id", None))


def is_sysadmin(context):
    user = get_authenticated_user(context)
    return bool(user and user.sysadmin)


def get_artesp_org_identifier():
    configured_identifier = dict(tk.config).get("ckanext.ldap.organization.id")
    if configured_identifier:
        return configured_identifier.strip()
    return DEFAULT_ARTESP_ORG_IDENTIFIER


def get_artesp_org():
    identifiers = [get_artesp_org_identifier()]
    if DEFAULT_ARTESP_ORG_IDENTIFIER not in identifiers:
        identifiers.append(DEFAULT_ARTESP_ORG_IDENTIFIER)

    for identifier in identifiers:
        org = model.Group.get(identifier)
        if org and getattr(org, "is_organization", False) and org.state == "active":
            return org

    return None


def get_artesp_org_title():
    configured_title = dict(tk.config).get("ckanext.ldap.organization.title")
    if configured_title:
        return configured_title.strip()
    return DEFAULT_ARTESP_ORG_TITLE


def get_artesp_org_display_name():
    org = get_artesp_org()
    configured_title = get_artesp_org_title()

    if configured_title:
        return configured_title
    if not org:
        return None

    return org.display_name or org.title or org.name


def should_reconcile_ldap_login():
    configured_value = dict(tk.config).get(
        "ckanext.artesp_theme.reconcile_ldap_login"
    )
    return tk.asbool(configured_value)


def get_default_dataset_collaborator_capacity():
    configured_capacity = dict(tk.config).get(
        "ckanext.artesp_theme.default_dataset_collaborator_capacity"
    )
    capacity = (configured_capacity or DEFAULT_DATASET_COLLABORATOR_CAPACITY).strip().lower()

    if capacity not in ("member", "editor"):
        return DEFAULT_DATASET_COLLABORATOR_CAPACITY

    return capacity


def is_artesp_owner_org(owner_org):
    if not owner_org:
        return False

    org = get_artesp_org()
    if not org:
        return False

    return owner_org in (org.id, org.name)


def ensure_user_membership_in_artesp(user_identifier):
    user = get_user(user_identifier)
    org = get_artesp_org()

    if not is_valid_user(user) or not org:
        return False

    desired_capacity = tk.config.get("ckanext.ldap.organization.role", "member")

    membership = (
        model.Session.query(model.Member)
        .filter(model.Member.table_name == "user")
        .filter(model.Member.table_id == user.id)
        .filter(model.Member.group_id == org.id)
        .order_by(model.Member.state.asc())
        .first()
    )

    if (
        membership
        and membership.state == "active"
        and membership.capacity == desired_capacity
    ):
        return True

    tk.get_action("member_create")(
        context={"ignore_auth": True},
        data_dict={
            "id": org.id,
            "object": user.name,
            "object_type": "user",
            "capacity": desired_capacity,
        },
    )
    return True


def ensure_artesp_org_state():
    organization_id = get_artesp_org_identifier()
    organization_title = get_artesp_org_title()
    action_context = {"ignore_auth": True}

    try:
        organization = tk.get_action("organization_show")(
            action_context,
            {"id": organization_id},
        )
    except tk.ObjectNotFound:
        tk.get_action("organization_create")(
            action_context,
            {
                "name": organization_id,
                "title": organization_title,
            },
        )
        return get_artesp_org()

    patch_data = {"id": organization["id"]}
    needs_patch = False

    current_title = organization.get("title") or organization.get("display_name")
    if current_title != organization_title:
        patch_data["title"] = organization_title
        needs_patch = True

    if organization.get("state") and organization.get("state") != "active":
        patch_data["state"] = "active"
        needs_patch = True

    if needs_patch:
        tk.get_action("organization_patch")(action_context, patch_data)

    return get_artesp_org()


def dataset_belongs_to_artesp(package):
    return bool(package and package.owner_org and is_artesp_owner_org(package.owner_org))


def get_package(data_dict):
    data_dict = data_dict or {}
    identifier = data_dict.get("id") or data_dict.get("name") or data_dict.get("package_id")
    if not identifier:
        return None
    return model.Package.get(identifier)


def get_resource(data_dict):
    data_dict = data_dict or {}
    identifier = data_dict.get("id") or data_dict.get("resource_id")
    if not identifier:
        return None
    return model.Resource.get(identifier)


def get_package_from_resource(data_dict):
    data_dict = data_dict or {}

    resource = get_resource(data_dict)
    if resource and resource.package_id:
        return model.Package.get(resource.package_id)

    package_id = data_dict.get("package_id")
    if not package_id:
        return None

    return model.Package.get(package_id)


def package_belongs_to_user(package, user):
    return bool(
        package
        and user
        and package.creator_user_id
        and package.creator_user_id == user.id
    )


def package_has_valid_creator(package):
    return bool(
        package
        and package.creator_user_id
        and model.User.get(package.creator_user_id)
    )


def get_target_user(data_dict):
    data_dict = data_dict or {}
    user_identifier = data_dict.get("user_id") or data_dict.get("username")
    if not user_identifier:
        return None
    return find_local_user_by_identifier(user_identifier)


def resolve_or_create_collaborator_user(user_identifier):
    user = find_local_user_by_identifier(user_identifier)
    if user:
        return user

    try:
        from ckanext.ldap.lib.exceptions import MultipleMatchError, UserConflictError
        from ckanext.ldap.lib.search import find_ldap_user
        from ckanext.ldap.routes import _helpers
    except ImportError:
        return None

    try:
        ldap_user_dict = find_ldap_user(user_identifier)
    except MultipleMatchError as exc:
        raise tk.ValidationError({"username": [tk._(str(exc))]})

    if not ldap_user_dict:
        return None

    try:
        user_name = _helpers.get_or_create_ldap_user(ldap_user_dict)
    except UserConflictError as exc:
        raise tk.ValidationError({"username": [tk._(str(exc))]})

    ensure_user_membership_in_artesp(user_name)
    return find_local_user_by_identifier(user_name)


def get_collaborator(package, user):
    if not package or not user:
        return None

    return (
        model.Session.query(model.PackageMember)
        .filter(model.PackageMember.package_id == package.id)
        .filter(model.PackageMember.user_id == user.id)
        .one_or_none()
    )


def get_collaborator_by_user_id(package, user_id):
    if not package or not user_id:
        return None

    return (
        model.Session.query(model.PackageMember)
        .filter(model.PackageMember.package_id == package.id)
        .filter(model.PackageMember.user_id == user_id)
        .one_or_none()
    )


def is_dataset_collaborators_enabled():
    return tk.asbool(tk.config.get("ckan.auth.allow_dataset_collaborators", False))


def is_admin_collaborators_enabled():
    return tk.asbool(tk.config.get("ckan.auth.allow_admin_collaborators", False))


def requested_capacity_is_allowed(capacity):
    if not capacity:
        return False
    return capacity in authz.get_collaborator_capacities()


def user_has_edit_collaborator_capacity(package, user):
    if not is_dataset_collaborators_enabled():
        return False

    collaborator = get_collaborator(package, user)
    return bool(collaborator and collaborator.capacity in EDIT_CAPACITIES)


def user_can_edit_package(package, user):
    if package_belongs_to_user(package, user):
        return True
    return user_has_edit_collaborator_capacity(package, user)


def user_can_manage_collaborators(package, user):
    if not package or not user or not is_dataset_collaborators_enabled():
        return False

    if package_belongs_to_user(package, user):
        return True

    if not is_admin_collaborators_enabled():
        return False

    collaborator = get_collaborator(package, user)
    return bool(collaborator and collaborator.capacity == ADMIN_CAPACITY)


def normalize_package_collaborator_create_data(context, data_dict):
    payload = dict(data_dict or {})
    target_identifier = payload.get("user_id") or payload.get("username")
    if not target_identifier:
        raise tk.ValidationError({"username": [tk._("A collaborator username is required.")]})

    target_user = resolve_or_create_collaborator_user(target_identifier)
    if not target_user:
        raise tk.ObjectNotFound(tk._("User not found."))

    payload["user_id"] = target_user.id
    payload.pop("username", None)

    requester = get_authenticated_user(context)
    if requester and requester.sysadmin:
        if not payload.get("capacity"):
            raise tk.ValidationError(
                {"capacity": [tk._("A collaborator capacity is required.")]}
            )
        return payload

    default_capacity = get_default_dataset_collaborator_capacity()
    requested_capacity = payload.get("capacity")

    if requested_capacity and requested_capacity != default_capacity:
        raise tk.NotAuthorized(tk._("Only sysadmins can change collaborator roles."))

    package = get_package(payload)
    existing_collaborator = get_collaborator_by_user_id(package, target_user.id)
    if existing_collaborator:
        raise tk.NotAuthorized(tk._("Only sysadmins can change collaborator roles."))

    payload["capacity"] = default_capacity
    return payload


def would_orphan_collaborator_governance(package, removed_user_id):
    if not package or not removed_user_id:
        return False

    if package_has_valid_creator(package):
        return False

    other_admin_exists = (
        model.Session.query(model.PackageMember)
        .filter(model.PackageMember.package_id == package.id)
        .filter(model.PackageMember.capacity == ADMIN_CAPACITY)
        .filter(model.PackageMember.user_id != removed_user_id)
        .count()
    )

    return other_admin_exists == 0
