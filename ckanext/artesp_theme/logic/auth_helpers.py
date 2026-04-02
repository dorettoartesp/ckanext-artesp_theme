from __future__ import annotations

import ckan.authz as authz
import ckan.model as model
import ckan.plugins.toolkit as tk


DEFAULT_ARTESP_ORG_IDENTIFIER = u"artesp"
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


def is_artesp_owner_org(owner_org):
    if not owner_org:
        return False

    org = get_artesp_org()
    if not org:
        return False

    return owner_org in (org.id, org.name)


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
    user_identifier = data_dict.get("user_id")
    if not user_identifier:
        return None
    return model.User.get(user_identifier)


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
