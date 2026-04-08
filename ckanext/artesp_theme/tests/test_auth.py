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


def test_package_create_rules_for_sysadmin_and_regular_users():
    artesp_org = factories.Organization(name="artesp")
    other_org = factories.Organization(name="other-org")
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
        owner_org=other_org["id"],
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


def test_package_update_and_delete_follow_creator_collaborator_and_sysadmin_rules():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    other_user = factories.User()
    editor = factories.User()
    sysadmin = factories.Sysadmin()

    package = _create_dataset_as(creator, artesp_org["id"])
    creator_owned_package = _create_dataset_as(creator, artesp_org["id"])

    updated_by_creator = _patch_dataset_as(creator, package, notes="creator update")
    assert updated_by_creator["notes"] == "creator update"

    _call_action_as(creator, "package_delete", id=creator_owned_package["id"])
    creator_deleted_package = model.Session.query(model.Package).get(
        creator_owned_package["id"]
    )
    assert creator_deleted_package is not None
    assert creator_deleted_package.state == "deleted"

    _assert_action_denied(other_user, "package_patch", id=package["id"], notes="blocked")
    _assert_action_denied(other_user, "package_delete", id=package["id"])

    _add_collaborator_as(creator, package, editor, "editor")

    updated_by_editor = _patch_dataset_as(editor, package, notes="editor update")
    assert updated_by_editor["notes"] == "editor update"
    assert test_helpers.call_auth(
        "package_delete",
        context=_auth_context(editor),
        id=package["id"],
    )

    updated_by_sysadmin = _patch_dataset_as(
        sysadmin,
        package,
        notes="sysadmin update",
    )
    assert updated_by_sysadmin["notes"] == "sysadmin update"

    _call_action_as(sysadmin, "package_delete", id=package["id"])
    deleted_package = model.Session.query(model.Package).get(package["id"])
    assert deleted_package is not None
    assert deleted_package.state == "deleted"


def test_resource_rules_follow_parent_dataset_permissions():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    other_user = factories.User()
    editor = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])
    resource = _create_resource_as(creator, package)
    creator_owned_resource = _create_resource_as(creator, package)

    updated_resource = _patch_resource_as(creator, resource, description="creator update")
    assert updated_resource["description"] == "creator update"

    _call_action_as(creator, "resource_delete", id=creator_owned_resource["id"])

    _assert_action_denied(
        other_user,
        "resource_create",
        package_id=package["id"],
        name=_unique_name("blocked-resource"),
        url="https://example.com/blocked.csv",
    )
    _assert_action_denied(
        other_user,
        "resource_patch",
        id=resource["id"],
        description="blocked",
    )
    _assert_action_denied(other_user, "resource_delete", id=resource["id"])

    _add_collaborator_as(creator, package, editor, "editor")

    collaborator_resource = _create_resource_as(editor, package)
    assert collaborator_resource["package_id"] == package["id"]

    edited_by_collaborator = _patch_resource_as(
        editor,
        resource,
        description="editor update",
    )
    assert edited_by_collaborator["description"] == "editor update"

    _call_action_as(editor, "resource_delete", id=collaborator_resource["id"])


def test_creator_can_list_add_update_and_remove_collaborators_on_own_dataset():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    random_user = factories.User()
    member_user = factories.User()
    editor_user = factories.User()
    admin_user = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])

    assert _list_collaborators_as(creator, package) == []

    _add_collaborator_as(creator, package, member_user, "member")
    _add_collaborator_as(creator, package, editor_user, "editor")
    _add_collaborator_as(creator, package, admin_user, "admin")

    collaborators = _list_collaborators_as(creator, package)
    capacities = {row["user_id"]: row["capacity"] for row in collaborators}
    assert capacities[member_user["id"]] == "member"
    assert capacities[editor_user["id"]] == "editor"
    assert capacities[admin_user["id"]] == "admin"

    _add_collaborator_as(creator, package, member_user, "editor")
    collaborators = _list_collaborators_as(creator, package)
    capacities = {row["user_id"]: row["capacity"] for row in collaborators}
    assert capacities[member_user["id"]] == "editor"

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

    patched_package = _patch_dataset_as(editor, package, notes="editor notes")
    assert patched_package["notes"] == "editor notes"

    patched_resource = _patch_resource_as(editor, resource, description="editor resource")
    assert patched_resource["description"] == "editor resource"

    _assert_action_denied(editor, "package_collaborator_list", id=package["id"])
    _assert_action_denied(
        editor,
        "package_collaborator_create",
        id=package["id"],
        user_id=other_user["id"],
        capacity="member",
    )
    _assert_action_denied(
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

    owned_package = _create_dataset_as(creator, artesp_org["id"])
    other_package = _create_dataset_as(creator, artesp_org["id"])

    _add_collaborator_as(creator, owned_package, dataset_admin, "admin")

    _list_collaborators_as(dataset_admin, owned_package)
    _add_collaborator_as(dataset_admin, owned_package, target_user, "member")
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


def test_admin_collaborator_assignment_requires_config_flag():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    collaborator = factories.User()

    package = _create_dataset_as(creator, artesp_org["id"])
    previous_value = toolkit.config.get("ckan.auth.allow_admin_collaborators")
    toolkit.config["ckan.auth.allow_admin_collaborators"] = False

    try:
        with pytest.raises(toolkit.ValidationError):
            _call_action_as(
                creator,
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

    _assert_action_denied(other_user, "package_patch", id=package["id"], notes="blocked")
    _assert_action_denied(creator, "package_patch", id=package["id"], notes="legacy blocked")

    _add_collaborator_as(
        factories.Sysadmin(),
        package,
        creator,
        "editor",
    )

    updated_package = _patch_dataset_as(creator, package, notes="legacy collaborator")
    assert updated_package["notes"] == "legacy collaborator"


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
