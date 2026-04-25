import uuid

import ckan.model as model
import ckan.plugins.toolkit as toolkit
import pytest
from ckan.tests import factories, helpers as test_helpers

from ckanext.artesp_theme.logic import auth as artesp_auth


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.ckan_config("ckan.auth.allow_dataset_collaborators", True),
    pytest.mark.ckan_config("ckan.auth.allow_admin_collaborators", True),
    pytest.mark.ckan_config(
        "ckanext.artesp_theme.default_dataset_collaborator_capacity", "editor"
    ),
    pytest.mark.usefixtures("with_plugins", "clean_db"),
]


def _unique_name(prefix):
    return "{}-{}".format(prefix, uuid.uuid4().hex[:8])


def _action_context(user=None):
    if isinstance(user, dict):
        user = user["name"]
    return {"user": user or ""}


def _auth_context(user=None):
    context = _action_context(user)
    context["model"] = model
    return context


def _call_action_as(user, action_name, **data_dict):
    return toolkit.get_action(action_name)(_action_context(user), data_dict)


def _assert_action_denied(user, action_name, **data_dict):
    with pytest.raises(toolkit.NotAuthorized):
        _call_action_as(user, action_name, **data_dict)


def _assert_auth_denied(user, auth_name, **data_dict):
    with pytest.raises(toolkit.NotAuthorized):
        test_helpers.call_auth(auth_name, context=_auth_context(user), **data_dict)


def _assert_auth_allowed(user, auth_name, **data_dict):
    assert test_helpers.call_auth(auth_name, context=_auth_context(user), **data_dict)


def _create_dataset_as(user, owner_org, **extra_data):
    payload = {
        "name": _unique_name("dataset"),
        "title": _unique_name("Dataset"),
        "owner_org": owner_org,
    }
    payload.update(extra_data)
    return _call_action_as(user, "package_create", **payload)


def _patch_dataset_as(user, package, **changes):
    payload = {"id": package["id"]}
    payload.update(changes)
    return _call_action_as(user, "package_patch", **payload)


def _create_resource_as(user, package, **extra_data):
    payload = {
        "package_id": package["id"],
        "name": _unique_name("resource"),
        "url": "https://example.com/{}.csv".format(uuid.uuid4().hex[:8]),
    }
    payload.update(extra_data)
    return _call_action_as(user, "resource_create", **payload)


def _patch_resource_as(user, resource, **changes):
    payload = {"id": resource["id"]}
    payload.update(changes)
    return _call_action_as(user, "resource_patch", **payload)


def _add_collaborator_as(user, package, collaborator, capacity):
    return _call_action_as(
        user,
        "package_collaborator_create",
        id=package["id"],
        user_id=collaborator["id"],
        capacity=capacity,
    )


def _list_collaborators_as(user, package, **extra_data):
    payload = {"id": package["id"]}
    payload.update(extra_data)
    return _call_action_as(user, "package_collaborator_list", **payload)


def _delete_collaborator_as(user, package, collaborator):
    return _call_action_as(
        user,
        "package_collaborator_delete",
        id=package["id"],
        user_id=collaborator["id"],
    )


def _collaborator_capacities(package):
    collaborators = test_helpers.call_action(
        "package_collaborator_list",
        id=package["id"],
    )
    return {row["user_id"]: row["capacity"] for row in collaborators}


def test_package_create_rules_for_sysadmin_and_regular_users():
    artesp_org = factories.Organization(name="artesp")
    sysadmin = factories.Sysadmin()
    regular_user = factories.User()

    sysadmin_dataset = _create_dataset_as(sysadmin, artesp_org["id"])
    assert sysadmin_dataset["owner_org"] == artesp_org["id"]

    user_dataset = _create_dataset_as(regular_user, artesp_org["id"])
    assert user_dataset["owner_org"] == artesp_org["id"]

    _assert_action_denied(
        regular_user,
        "package_create",
        name=_unique_name("missing-owner-org"),
        title="Missing owner_org",
    )
    _assert_action_denied(
        regular_user,
        "package_create",
        name=_unique_name("wrong-org"),
        title="Wrong org",
        owner_org="other-org",
    )


def test_package_create_auth_allows_ui_preflight_for_authenticated_users():
    factories.Organization(name="artesp")
    regular_user = factories.User()

    assert test_helpers.call_auth(
        "package_create",
        context=_auth_context(regular_user),
    )

    _assert_action_denied(
        regular_user,
        "package_create",
        name=_unique_name("missing-owner-org"),
        title="Missing owner_org on submission",
    )


def test_only_sysadmin_can_create_organizations():
    sysadmin = factories.Sysadmin()
    regular_user = factories.User()

    created_org = _call_action_as(
        sysadmin,
        "organization_create",
        name=_unique_name("org"),
        title="Org created by sysadmin",
    )
    assert created_org["name"].startswith("org-")

    _assert_action_denied(
        regular_user,
        "organization_create",
        name=_unique_name("org"),
        title="Org blocked for user",
    )
    _assert_auth_denied(regular_user, "organization_create")


def test_only_sysadmin_can_update_and_delete_organizations():
    sysadmin = factories.Sysadmin()
    regular_user = factories.User()

    organization = _call_action_as(
        sysadmin,
        "organization_create",
        name=_unique_name("org-manage"),
        title="Org managed by sysadmin",
    )

    updated_org = _call_action_as(
        sysadmin,
        "organization_update",
        id=organization["id"],
        name=organization["name"],
        title="Updated org title",
    )
    assert updated_org["title"] == "Updated org title"

    _assert_action_denied(
        regular_user,
        "organization_update",
        id=organization["id"],
        name=organization["name"],
        title="Blocked org title",
    )
    _assert_auth_denied(regular_user, "organization_update", id=organization["id"])

    _assert_action_denied(
        regular_user,
        "organization_delete",
        id=organization["id"],
    )
    _assert_auth_denied(regular_user, "organization_delete", id=organization["id"])

    _call_action_as(sysadmin, "organization_delete", id=organization["id"])


def test_only_sysadmin_can_create_groups():
    sysadmin = factories.Sysadmin()
    regular_user = factories.User()

    created_group = _call_action_as(
        sysadmin,
        "group_create",
        name=_unique_name("group"),
        title="Group created by sysadmin",
    )
    assert created_group["name"].startswith("group-")

    _assert_action_denied(
        regular_user,
        "group_create",
        name=_unique_name("group"),
        title="Group blocked for user",
    )
    _assert_auth_denied(regular_user, "group_create")


def test_only_sysadmin_can_update_and_delete_groups():
    sysadmin = factories.Sysadmin()
    regular_user = factories.User()

    group = _call_action_as(
        sysadmin,
        "group_create",
        name=_unique_name("group-manage"),
        title="Group managed by sysadmin",
    )

    updated_group = _call_action_as(
        sysadmin,
        "group_update",
        id=group["id"],
        name=group["name"],
        title="Updated group title",
    )
    assert updated_group["title"] == "Updated group title"

    _assert_action_denied(
        regular_user,
        "group_update",
        id=group["id"],
        name=group["name"],
        title="Blocked group title",
    )
    _assert_auth_denied(regular_user, "group_update", id=group["id"])

    _assert_action_denied(
        regular_user,
        "group_delete",
        id=group["id"],
    )
    _assert_auth_denied(regular_user, "group_delete", id=group["id"])

    _call_action_as(sysadmin, "group_delete", id=group["id"])


def test_package_update_and_delete_follow_creator_collaborator_and_sysadmin_rules():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    other_user = factories.User()
    editor = factories.User()
    sysadmin = factories.Sysadmin()

    package = _create_dataset_as(creator, artesp_org["id"])

    _assert_auth_allowed(creator, "package_update", id=package["id"])
    _assert_auth_allowed(creator, "package_delete", id=package["id"])

    _assert_auth_denied(other_user, "package_update", id=package["id"])
    _assert_auth_denied(other_user, "package_delete", id=package["id"])

    _add_collaborator_as(creator, package, editor, "editor")

    _assert_auth_allowed(editor, "package_update", id=package["id"])
    _assert_auth_allowed(editor, "package_delete", id=package["id"])

    _assert_auth_allowed(sysadmin, "package_update", id=package["id"])
    _assert_auth_allowed(sysadmin, "package_delete", id=package["id"])


def test_resource_rules_follow_parent_dataset_permissions():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    other_user = factories.User()
    editor = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])
    resource = _create_resource_as(creator, package)

    _assert_auth_allowed(creator, "resource_create", package_id=package["id"])
    _assert_auth_allowed(creator, "resource_update", id=resource["id"])
    _assert_auth_allowed(creator, "resource_delete", id=resource["id"])

    _assert_auth_denied(
        other_user,
        "resource_create",
        package_id=package["id"],
    )
    _assert_auth_denied(
        other_user,
        "resource_update",
        id=resource["id"],
    )
    _assert_auth_denied(other_user, "resource_delete", id=resource["id"])

    _add_collaborator_as(creator, package, editor, "editor")

    _assert_auth_allowed(editor, "resource_create", package_id=package["id"])
    _assert_auth_allowed(editor, "resource_update", id=resource["id"])
    _assert_auth_allowed(editor, "resource_delete", id=resource["id"])


def test_creator_can_list_add_update_and_remove_collaborators_on_own_dataset():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    random_user = factories.User()
    member_user = factories.User()
    editor_user = factories.User()
    admin_user = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])

    assert _list_collaborators_as(creator, package) == []

    _call_action_as(
        creator,
        "package_collaborator_create",
        id=package["id"],
        user_id=member_user["id"],
    )
    _call_action_as(
        creator,
        "package_collaborator_create",
        id=package["id"],
        user_id=editor_user["id"],
    )

    collaborators = _list_collaborators_as(creator, package)
    capacities = {row["user_id"]: row["capacity"] for row in collaborators}
    assert capacities[editor_user["id"]] == "editor"
    assert capacities[member_user["id"]] == "editor"

    _assert_action_denied(
        creator,
        "package_collaborator_create",
        id=package["id"],
        user_id=admin_user["id"],
        capacity="member",
    )
    _assert_action_denied(
        creator,
        "package_collaborator_create",
        id=package["id"],
        user_id=member_user["id"],
        capacity="member",
    )

    _delete_collaborator_as(creator, package, editor_user)
    collaborators = _list_collaborators_as(creator, package)
    collaborator_ids = {row["user_id"] for row in collaborators}
    assert editor_user["id"] not in collaborator_ids

    _assert_action_denied(random_user, "package_collaborator_list", id=package["id"])
    _assert_action_denied(
        random_user,
        "package_collaborator_create",
        id=package["id"],
        user_id=editor_user["id"],
        capacity="member",
    )
    _assert_action_denied(
        random_user,
        "package_collaborator_delete",
        id=package["id"],
        user_id=member_user["id"],
    )


def test_editor_can_edit_but_cannot_manage_collaborators():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    editor = factories.User()
    other_user = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])
    resource = _create_resource_as(creator, package)
    _add_collaborator_as(creator, package, editor, "editor")

    _assert_auth_allowed(editor, "package_update", id=package["id"])
    _assert_auth_allowed(editor, "resource_update", id=resource["id"])

    _assert_auth_denied(editor, "package_collaborator_list", id=package["id"])
    _assert_auth_denied(
        editor,
        "package_collaborator_create",
        id=package["id"],
        user_id=other_user["id"],
        capacity="member",
    )
    _assert_auth_denied(
        editor,
        "package_collaborator_delete",
        id=package["id"],
        user_id=editor["id"],
    )


def test_admin_collaborator_can_manage_only_their_dataset():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    dataset_admin = factories.User()
    target_user = factories.User()
    sysadmin = factories.Sysadmin()

    owned_package = _create_dataset_as(creator, artesp_org["id"])
    other_package = _create_dataset_as(creator, artesp_org["id"])

    _add_collaborator_as(sysadmin, owned_package, dataset_admin, "admin")

    _list_collaborators_as(dataset_admin, owned_package)
    _call_action_as(
        dataset_admin,
        "package_collaborator_create",
        id=owned_package["id"],
        user_id=target_user["id"],
    )
    _delete_collaborator_as(dataset_admin, owned_package, target_user)

    _assert_action_denied(dataset_admin, "package_collaborator_list", id=other_package["id"])
    _assert_action_denied(
        dataset_admin,
        "package_collaborator_create",
        id=other_package["id"],
        user_id=target_user["id"],
        capacity="member",
    )


def test_sysadmin_can_manage_collaborators_on_any_dataset():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    sysadmin = factories.Sysadmin()
    collaborator = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])

    _add_collaborator_as(sysadmin, package, collaborator, "member")
    collaborators = _list_collaborators_as(sysadmin, package)
    collaborator_ids = {row["user_id"] for row in collaborators}
    assert collaborator["id"] in collaborator_ids

    _delete_collaborator_as(sysadmin, package, collaborator)
    collaborators = _list_collaborators_as(sysadmin, package)
    collaborator_ids = {row["user_id"] for row in collaborators}
    assert collaborator["id"] not in collaborator_ids


def test_sysadmin_can_define_and_update_collaborator_roles():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    sysadmin = factories.Sysadmin()
    collaborator = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])

    _add_collaborator_as(sysadmin, package, collaborator, "member")
    capacities = _collaborator_capacities(package)
    assert capacities[collaborator["id"]] == "member"

    _add_collaborator_as(sysadmin, package, collaborator, "admin")
    capacities = _collaborator_capacities(package)
    assert capacities[collaborator["id"]] == "admin"


def test_admin_collaborator_assignment_requires_config_flag():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    sysadmin = factories.Sysadmin()
    collaborator = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])
    previous_value = toolkit.config.get("ckan.auth.allow_admin_collaborators")
    toolkit.config["ckan.auth.allow_admin_collaborators"] = False

    try:
        with pytest.raises(toolkit.ValidationError):
            _call_action_as(
                sysadmin,
                "package_collaborator_create",
                id=package["id"],
                user_id=collaborator["id"],
                capacity="admin",
            )
    finally:
        toolkit.config["ckan.auth.allow_admin_collaborators"] = previous_value


def test_anonymous_requests_are_denied_for_relevant_operations():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])
    resource = _create_resource_as(creator, package)

    _assert_action_denied(
        None,
        "package_create",
        name=_unique_name("anon"),
        title="Anonymous dataset",
        owner_org=artesp_org["id"],
    )
    _assert_action_denied(None, "package_patch", id=package["id"], notes="anon")
    _assert_action_denied(
        None,
        "resource_create",
        package_id=package["id"],
        name=_unique_name("anon-resource"),
        url="https://example.com/anon.csv",
    )
    _assert_action_denied(None, "package_collaborator_list", id=package["id"])
    _assert_action_denied(None, "resource_patch", id=resource["id"], description="anon")


def test_direct_auth_functions_handle_missing_context_and_payload_safely():
    artesp_org = factories.Organization(name="artesp")
    package = test_helpers.call_action(
        "package_create",
        name=_unique_name("safe-direct-package"),
        title="Safe direct package",
        owner_org=artesp_org["id"],
    )
    resource = test_helpers.call_action(
        "resource_create",
        package_id=package["id"],
        name=_unique_name("safe-direct-resource"),
        url="https://example.com/direct.csv",
    )

    assert artesp_auth.package_create({"model": model}, {"owner_org": artesp_org["id"]})[
        "success"
    ] is False
    assert artesp_auth.package_create(
        {"model": model, "user": "missing-user"},
        {"owner_org": artesp_org["id"]},
    )["success"] is False
    assert artesp_auth.package_update({"model": model, "user": ""}, {"id": package["id"]})[
        "success"
    ] is False
    assert artesp_auth.resource_create({"model": model, "user": ""}, {"package_id": package["id"]})[
        "success"
    ] is False
    assert artesp_auth.package_collaborator_create(
        {"model": model, "user": ""},
        {"id": package["id"], "user_id": "missing-user", "capacity": "member"},
    )["success"] is False
    assert artesp_auth.resource_update({"model": model, "user": ""}, {"id": resource["id"]})[
        "success"
    ] is False


def test_nonexistent_dataset_resource_and_incomplete_payloads_are_denied_safely():
    user = factories.User()

    _assert_auth_denied(user, "package_update", id="missing-dataset-id")
    _assert_auth_denied(user, "package_delete", id="missing-dataset-id")
    _assert_auth_denied(user, "resource_update", id="missing-resource-id")
    _assert_auth_denied(user, "resource_delete", id="missing-resource-id")
    _assert_auth_denied(user, "resource_create")
    _assert_auth_denied(user, "package_collaborator_list", id="missing-dataset-id")
    _assert_auth_denied(
        user,
        "package_collaborator_create",
        id="missing-dataset-id",
        user_id=user["id"],
        capacity="member",
    )
    _assert_auth_denied(
        user,
        "package_collaborator_delete",
        id="missing-dataset-id",
        user_id=user["id"],
    )


def test_legacy_dataset_with_invalid_creator_is_handled_safely():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    other_user = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])
    package_obj = model.Package.get(package["id"])
    package_obj.creator_user_id = "deleted-or-legacy-user"
    model.Session.add(package_obj)
    model.Session.commit()

    _assert_auth_denied(other_user, "package_update", id=package["id"])
    _assert_auth_denied(creator, "package_update", id=package["id"])

    _add_collaborator_as(
        factories.Sysadmin(),
        package,
        creator,
        "editor",
    )

    _assert_auth_allowed(creator, "package_update", id=package["id"])


def test_self_removal_is_blocked_when_it_would_orphan_collaborator_governance():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    collaborator_admin = factories.User()
    sysadmin = factories.Sysadmin()

    package = _create_dataset_as(creator, artesp_org["id"])
    package_obj = model.Package.get(package["id"])
    package_obj.creator_user_id = None
    model.Session.add(package_obj)
    model.Session.commit()

    _add_collaborator_as(sysadmin, package, collaborator_admin, "admin")

    _assert_action_denied(
        collaborator_admin,
        "package_collaborator_delete",
        id=package["id"],
        user_id=collaborator_admin["id"],
    )


# ---------------------------------------------------------------------------
# Additional coverage for missing branches
# ---------------------------------------------------------------------------

def test_package_create_sysadmin_is_allowed_directly():
    """Line 43: sysadmin allow path in package_create."""
    factories.Organization(name="artesp")
    sysadmin = factories.Sysadmin()

    result = test_helpers.call_auth(
        "package_create",
        context=_auth_context(sysadmin),
    )
    assert result  # call_auth returns True or dict with success


def test_package_create_denied_when_artesp_org_missing(monkeypatch):
    """Line 51: deny when ARTESP org does not exist."""
    from ckanext.artesp_theme.logic import auth as artesp_auth
    from ckanext.artesp_theme.logic import auth_helpers

    regular_user = factories.User()
    user_obj = model.User.get(regular_user["name"])

    monkeypatch.setattr(auth_helpers, "get_artesp_org", lambda: None)

    result = artesp_auth.package_create(
        {"model": model, "auth_user_obj": user_obj},
        {"owner_org": "artesp"},
    )
    assert result["success"] is False
    assert "ARTESP" in result["msg"] or "organization" in result["msg"].lower()


def test_sysadmin_only_management_operation_denies_valid_non_sysadmin():
    """Line 119: _sysadmin_only_management_operation denies a regular (valid) user."""
    regular_user = factories.User()
    _assert_auth_denied(regular_user, "organization_create")


def test_dataset_rating_upsert_denies_anonymous():
    """Line 210: dataset_rating_upsert with no user context."""
    from ckanext.artesp_theme.logic import auth as artesp_auth

    result = artesp_auth.dataset_rating_upsert({"model": model})
    assert result["success"] is False


def test_authorize_package_operation_sysadmin_allowed():
    """Line 266: _authorize_package_operation allows sysadmin."""
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    sysadmin = factories.Sysadmin()

    package = _create_dataset_as(creator, artesp_org["id"])
    result = test_helpers.call_auth(
        "package_update",
        context=_auth_context(sysadmin),
        id=package["id"],
    )
    assert result  # sysadmin is allowed


def test_authorize_package_operation_denies_no_id():
    """Line 277: _authorize_package_operation with no data_dict id."""
    regular_user = factories.User()
    _assert_auth_denied(regular_user, "package_update")


def test_authorize_package_operation_denies_non_artesp_dataset():
    """Line 284: _authorize_package_operation when package not in artesp org."""
    factories.Organization(name="artesp")
    other_org = factories.Organization(name="other-org-x")
    creator = factories.User()

    # Create dataset at model level to bypass the custom action restriction
    other_org_obj = model.Group.get(other_org["id"])
    pkg = model.Package(
        name=_unique_name("other-ds"),
        title="Other org dataset",
        owner_org=other_org_obj.id,
        state="active",
    )
    model.Session.add(pkg)
    model.Session.commit()

    _assert_auth_denied(creator, "package_update", id=pkg.id)


def test_authorize_package_operation_denies_moving_outside_artesp():
    """Line 291: deny when owner_org is changed to non-artesp org."""
    artesp_org = factories.Organization(name="artesp")
    other_org = factories.Organization(name="other-move")
    creator = factories.User()
    package = _create_dataset_as(creator, artesp_org["id"])

    # creator tries to move to other org
    result = artesp_auth.package_update(
        {"model": model, "auth_user_obj": model.User.get(creator["name"])},
        {"id": package["id"], "owner_org": other_org["id"]},
    )
    assert result["success"] is False


def test_authorize_resource_operation_sysadmin_allowed():
    """Line 315: _authorize_resource_operation allows sysadmin."""
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    sysadmin = factories.Sysadmin()

    package = _create_dataset_as(creator, artesp_org["id"])
    resource = _create_resource_as(creator, package)

    result = test_helpers.call_auth(
        "resource_update",
        context=_auth_context(sysadmin),
        id=resource["id"],
    )
    assert result  # sysadmin is allowed


def test_authorize_resource_operation_denies_missing_parent_dataset(monkeypatch):
    """Line 335: deny when parent dataset cannot be resolved."""
    from ckanext.artesp_theme.logic import auth as artesp_auth
    from ckanext.artesp_theme.logic import auth_helpers

    regular_user = factories.User()
    user_obj = model.User.get(regular_user["name"])

    # resource_create path — package_id that resolves to nothing
    result = artesp_auth.resource_create(
        {"model": model, "auth_user_obj": user_obj},
        {"package_id": "nonexistent-package-id"},
    )
    assert result["success"] is False


def test_authorize_resource_operation_denies_non_artesp_resource():
    """Line 338: deny when resource belongs to non-artesp dataset."""
    factories.Organization(name="artesp")
    other_org = factories.Organization(name="other-res-org")
    creator = factories.User()

    # Create package at model level to bypass custom action restriction
    other_org_obj = model.Group.get(other_org["id"])
    pkg = model.Package(
        name=_unique_name("other-res-ds"),
        title="Other org dataset for resource",
        owner_org=other_org_obj.id,
        state="active",
    )
    model.Session.add(pkg)
    model.Session.commit()

    resource = toolkit.get_action("resource_create")(
        {"ignore_auth": True},
        {
            "package_id": pkg.id,
            "name": _unique_name("resource"),
            "url": "https://example.com/res.csv",
        },
    )

    _assert_auth_denied(creator, "resource_update", id=resource["id"])


def test_authorize_collaborator_operation_sysadmin_allowed():
    """Line 368: _authorize_collaborator_operation allows sysadmin."""
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    sysadmin = factories.Sysadmin()

    package = _create_dataset_as(creator, artesp_org["id"])

    result = test_helpers.call_auth(
        "package_collaborator_list",
        context=_auth_context(sysadmin),
        id=package["id"],
    )
    assert result  # sysadmin is allowed


def test_authorize_collaborator_operation_denies_no_id():
    """Line 382: deny when no dataset id."""
    regular_user = factories.User()
    _assert_auth_denied(regular_user, "package_collaborator_list")


def test_authorize_collaborator_operation_denies_non_artesp_dataset():
    """Line 389: deny when dataset not in artesp org."""
    factories.Organization(name="artesp")
    other_org = factories.Organization(name="other-collab-org")
    creator = factories.User()

    other_org_obj = model.Group.get(other_org["id"])
    pkg = model.Package(
        name=_unique_name("other-collab-ds"),
        title="Other org for collaborators",
        owner_org=other_org_obj.id,
        state="active",
    )
    model.Session.add(pkg)
    model.Session.commit()

    _assert_auth_denied(creator, "package_collaborator_list", id=pkg.id)


def test_validate_requested_capacity_sysadmin_no_capacity_is_denied():
    """Lines 401, 403: sysadmin with no capacity set → deny."""
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    sysadmin = factories.Sysadmin()
    collaborator = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])

    # sysadmin trying to add collaborator without capacity
    with pytest.raises(toolkit.ValidationError):
        _call_action_as(
            sysadmin,
            "package_collaborator_create",
            id=package["id"],
            user_id=collaborator["id"],
            # no capacity
        )


def test_validate_requested_capacity_invalid_capacity_is_denied():
    """Lines 405-407: invalid capacity string."""
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])
    other_user = factories.User()

    with pytest.raises((toolkit.NotAuthorized, toolkit.ValidationError)):
        _call_action_as(
            creator,
            "package_collaborator_create",
            id=package["id"],
            user_id=other_user["id"],
            capacity="superuser",  # invalid capacity
        )


def test_validate_requested_capacity_non_default_role_denied_for_non_sysadmin():
    """Line 412: non-sysadmin cannot change from default capacity."""
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    collaborator = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])

    # creator trying to add with non-default "member" capacity (default is "editor")
    with pytest.raises(toolkit.NotAuthorized):
        _call_action_as(
            creator,
            "package_collaborator_create",
            id=package["id"],
            user_id=collaborator["id"],
            capacity="member",
        )


def test_target_user_not_found_is_denied():
    """Line 418: target user not found — auth denies when target user doesn't exist."""
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])

    # Call auth directly (bypasses normalize which tries LDAP)
    result = artesp_auth.package_collaborator_create(
        _auth_context(creator),
        {"id": package["id"], "user_id": "nonexistent-user-id-xyz"},
    )
    assert result["success"] is False


def test_existing_collaborator_non_sysadmin_cannot_change_role():
    """Line 427: existing collaborator + non-sysadmin cannot change role."""
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    collaborator = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])
    # Add collaborator as default (editor)
    _call_action_as(
        creator,
        "package_collaborator_create",
        id=package["id"],
        user_id=collaborator["id"],
    )

    # Try to re-add (change role) — non-sysadmin cannot change
    with pytest.raises(toolkit.NotAuthorized):
        _call_action_as(
            creator,
            "package_collaborator_create",
            id=package["id"],
            user_id=collaborator["id"],
        )


def test_require_existing_collaborator_not_found_is_denied():
    """Line 432: require_existing_collaborator but collaborator not found."""
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    non_collaborator = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])

    # Try to delete a collaborator that doesn't exist
    with pytest.raises(toolkit.NotAuthorized):
        _call_action_as(
            creator,
            "package_collaborator_delete",
            id=package["id"],
            user_id=non_collaborator["id"],
        )
