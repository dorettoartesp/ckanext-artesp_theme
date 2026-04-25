import uuid

import ckan.model as model
import ckan.plugins.toolkit as toolkit
import pytest
from ckan.tests import factories, helpers as test_helpers

from ckanext.artesp_theme.logic import auth as artesp_auth
from ckanext.artesp_theme.logic import auth_helpers


pytestmark = [
    pytest.mark.integration,
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.ckan_config("ckan.auth.allow_dataset_collaborators", True),
    pytest.mark.ckan_config("ckan.auth.allow_admin_collaborators", True),
    pytest.mark.ckan_config(
        "ckanext.artesp_theme.default_dataset_collaborator_capacity", "editor"
    ),
    pytest.mark.usefixtures("with_plugins"),
]


def _unique_name(prefix):
    return "{}-{}".format(prefix, uuid.uuid4().hex[:8])


def _user(**overrides):
    base = _unique_name("user")
    payload = {
        "name": base,
        "email": "{}@ckan.example.com".format(base),
        "state": "active",
    }
    payload.update(overrides)
    user = model.User(**payload)
    model.Session.add(user)
    model.Session.flush()
    return {"id": user.id, "name": user.name, "email": user.email}


def _sysadmin(**overrides):
    base = _unique_name("sysadmin")
    payload = {
        "name": base,
        "email": "{}@ckan.example.com".format(base),
        "state": "active",
        "sysadmin": True,
    }
    payload.update(overrides)
    user = model.User(**payload)
    model.Session.add(user)
    model.Session.flush()
    return {"id": user.id, "name": user.name, "email": user.email}


def _entity_id(entity):
    if isinstance(entity, dict):
        return entity["id"]
    return entity.id


def _action_context(user=None):
    if isinstance(user, dict):
        user = user["name"]
    return {"user": user or ""}


def _auth_context(user=None):
    context = _action_context(user)
    context["model"] = model
    return context


def _artesp_org():
    org = auth_helpers.get_artesp_org()
    if org:
        return {
            "id": org.id,
            "name": org.name,
            "title": org.title,
        }
    return factories.Organization(name="artesp")


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


def _create_dataset_row(owner_org, creator=None, **extra_data):
    package = model.Package(
        name=extra_data.pop("name", _unique_name("dataset")),
        title=extra_data.pop("title", _unique_name("Dataset")),
        owner_org=owner_org,
        state=extra_data.pop("state", "active"),
    )
    if creator:
        package.creator_user_id = _entity_id(creator)
    for key, value in extra_data.items():
        setattr(package, key, value)
    model.Session.add(package)
    model.Session.flush()
    return package


def _patch_dataset_as(user, package, **changes):
    payload = {"id": _entity_id(package)}
    payload.update(changes)
    return _call_action_as(user, "package_patch", **payload)


def _create_resource_as(user, package, **extra_data):
    payload = {
        "package_id": _entity_id(package),
        "name": _unique_name("resource"),
        "url": "https://example.com/{}.csv".format(uuid.uuid4().hex[:8]),
    }
    payload.update(extra_data)
    return _call_action_as(user, "resource_create", **payload)


def _create_resource_row(package, **extra_data):
    resource = model.Resource(
        package_id=_entity_id(package),
        name=extra_data.pop("name", _unique_name("resource")),
        url=extra_data.pop(
            "url", "https://example.com/{}.csv".format(uuid.uuid4().hex[:8])
        ),
    )
    resource.state = extra_data.pop("state", "active")
    for key, value in extra_data.items():
        setattr(resource, key, value)
    model.Session.add(resource)
    model.Session.flush()
    return resource


def _patch_resource_as(user, resource, **changes):
    payload = {"id": _entity_id(resource)}
    payload.update(changes)
    return _call_action_as(user, "resource_patch", **payload)


def _add_collaborator_row(package, collaborator, capacity):
    package_id = _entity_id(package)
    collaborator_id = _entity_id(collaborator)
    membership = (
        model.Session.query(model.PackageMember)
        .filter(model.PackageMember.package_id == package_id)
        .filter(model.PackageMember.user_id == collaborator_id)
        .one_or_none()
    )
    if membership:
        membership.capacity = capacity
    else:
        membership = model.PackageMember(
            package_id=package_id,
            user_id=collaborator_id,
            capacity=capacity,
        )
        model.Session.add(membership)
    model.Session.flush()
    return membership


def _add_collaborator_as(user, package, collaborator, capacity):
    return _call_action_as(
        user,
        "package_collaborator_create",
        id=_entity_id(package),
        user_id=_entity_id(collaborator),
        capacity=capacity,
    )


def _list_collaborators_as(user, package, **extra_data):
    payload = {"id": _entity_id(package)}
    payload.update(extra_data)
    return _call_action_as(user, "package_collaborator_list", **payload)


def _delete_collaborator_as(user, package, collaborator):
    return _call_action_as(
        user,
        "package_collaborator_delete",
        id=_entity_id(package),
        user_id=_entity_id(collaborator),
    )


def _collaborator_capacities(package):
    collaborators = (
        model.Session.query(model.PackageMember)
        .filter(model.PackageMember.package_id == _entity_id(package))
        .all()
    )
    return {row.user_id: row.capacity for row in collaborators}


def test_package_create_rules_for_regular_users():
    artesp_org = _artesp_org()
    regular_user = _user()

    user_dataset = _create_dataset_as(regular_user, artesp_org["id"])
    assert user_dataset["owner_org"] == artesp_org["id"]

    assert (
        artesp_auth.package_create(
            _auth_context(regular_user),
            {"name": _unique_name("missing-owner-org"), "title": "Missing owner_org"},
        )["success"]
        is False
    )
    assert (
        artesp_auth.package_create(
            _auth_context(regular_user),
            {
                "name": _unique_name("wrong-org"),
                "title": "Wrong org",
                "owner_org": "other-org",
            },
        )["success"]
        is False
    )


def test_package_create_auth_allows_ui_preflight_for_authenticated_users():
    _artesp_org()
    regular_user = _user()

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
    sysadmin = _sysadmin()
    regular_user = _user()

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
    sysadmin = _sysadmin()
    regular_user = _user()

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
    sysadmin = _sysadmin()
    regular_user = _user()

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
    sysadmin = _sysadmin()
    regular_user = _user()

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
    artesp_org = _artesp_org()
    creator = _user()
    other_user = _user()
    editor = _user()
    sysadmin = _sysadmin()

    package = _create_dataset_row(artesp_org["id"], creator=creator)

    _assert_auth_allowed(creator, "package_update", id=package.id)
    _assert_auth_allowed(creator, "package_delete", id=package.id)

    _assert_auth_denied(other_user, "package_update", id=package.id)
    _assert_auth_denied(other_user, "package_delete", id=package.id)

    _add_collaborator_row(package, editor, "editor")

    _assert_auth_allowed(editor, "package_update", id=package.id)
    _assert_auth_allowed(editor, "package_delete", id=package.id)

    _assert_auth_allowed(sysadmin, "package_update", id=package.id)
    _assert_auth_allowed(sysadmin, "package_delete", id=package.id)


def test_resource_rules_follow_parent_dataset_permissions():
    artesp_org = _artesp_org()
    creator = _user()
    other_user = _user()
    editor = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)
    resource = _create_resource_row(package)

    _assert_auth_allowed(creator, "resource_create", package_id=package.id)
    _assert_auth_allowed(creator, "resource_update", id=resource.id)
    _assert_auth_allowed(creator, "resource_delete", id=resource.id)

    _assert_auth_denied(
        other_user,
        "resource_create",
        package_id=package.id,
    )
    _assert_auth_denied(
        other_user,
        "resource_update",
        id=resource.id,
    )
    _assert_auth_denied(other_user, "resource_delete", id=resource.id)

    _add_collaborator_row(package, editor, "editor")

    _assert_auth_allowed(editor, "resource_create", package_id=package.id)
    _assert_auth_allowed(editor, "resource_update", id=resource.id)
    _assert_auth_allowed(editor, "resource_delete", id=resource.id)


def test_creator_can_list_add_update_and_remove_collaborators_on_own_dataset():
    artesp_org = _artesp_org()
    creator = _user()
    random_user = _user()
    member_user = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)

    assert _list_collaborators_as(creator, package) == []

    _call_action_as(
        creator,
        "package_collaborator_create",
        id=package.id,
        user_id=member_user["id"],
    )

    collaborators = _list_collaborators_as(creator, package)
    capacities = {row["user_id"]: row["capacity"] for row in collaborators}
    assert capacities[member_user["id"]] == "editor"

    _delete_collaborator_as(creator, package, member_user)
    collaborators = _list_collaborators_as(creator, package)
    assert collaborators == []

    _assert_auth_denied(random_user, "package_collaborator_list", id=package.id)
    _assert_auth_denied(
        random_user,
        "package_collaborator_create",
        id=package.id,
        user_id=member_user["id"],
        capacity="member",
    )
    _assert_auth_denied(
        random_user,
        "package_collaborator_delete",
        id=package.id,
        user_id=member_user["id"],
    )


def test_editor_can_edit_but_cannot_manage_collaborators():
    artesp_org = _artesp_org()
    creator = _user()
    editor = _user()
    other_user = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)
    resource = _create_resource_row(package)
    _add_collaborator_row(package, editor, "editor")

    _assert_auth_allowed(editor, "package_update", id=package.id)
    _assert_auth_allowed(editor, "resource_update", id=resource.id)

    _assert_auth_denied(editor, "package_collaborator_list", id=package.id)
    _assert_auth_denied(
        editor,
        "package_collaborator_create",
        id=package.id,
        user_id=other_user["id"],
        capacity="member",
    )
    _assert_auth_denied(
        editor,
        "package_collaborator_delete",
        id=package.id,
        user_id=editor["id"],
    )


def test_admin_collaborator_can_manage_only_their_dataset():
    artesp_org = _artesp_org()
    creator = _user()
    dataset_admin = _user()
    target_user = _user()

    owned_package = _create_dataset_row(artesp_org["id"], creator=creator)
    other_package = _create_dataset_row(artesp_org["id"], creator=creator)

    _add_collaborator_row(owned_package, dataset_admin, "admin")

    _assert_auth_allowed(dataset_admin, "package_collaborator_list", id=owned_package.id)
    _assert_auth_allowed(
        dataset_admin,
        "package_collaborator_create",
        id=owned_package.id,
        user_id=target_user["id"],
        capacity="editor",
    )
    _add_collaborator_row(owned_package, target_user, "editor")
    _assert_auth_allowed(
        dataset_admin,
        "package_collaborator_delete",
        id=owned_package.id,
        user_id=target_user["id"],
    )

    _assert_auth_denied(dataset_admin, "package_collaborator_list", id=other_package.id)
    _assert_auth_denied(
        dataset_admin,
        "package_collaborator_create",
        id=other_package.id,
        user_id=target_user["id"],
        capacity="member",
    )


def test_sysadmin_can_manage_collaborators_on_any_dataset():
    artesp_org = _artesp_org()
    creator = _user()
    sysadmin = _sysadmin()
    collaborator = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)

    _assert_auth_allowed(sysadmin, "package_collaborator_list", id=package.id)
    _assert_auth_allowed(
        sysadmin,
        "package_collaborator_create",
        id=package.id,
        user_id=collaborator["id"],
        capacity="member",
    )
    _add_collaborator_row(package, collaborator, "member")
    _assert_auth_allowed(
        sysadmin,
        "package_collaborator_delete",
        id=package.id,
        user_id=collaborator["id"],
    )


def test_sysadmin_can_define_and_update_collaborator_roles():
    artesp_org = _artesp_org()
    creator = _user()
    sysadmin = _sysadmin()
    collaborator = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)

    _add_collaborator_as(sysadmin, package, collaborator, "member")
    capacities = _collaborator_capacities(package)
    assert capacities[collaborator["id"]] == "member"

    _add_collaborator_as(sysadmin, package, collaborator, "admin")
    capacities = _collaborator_capacities(package)
    assert capacities[collaborator["id"]] == "admin"


def test_admin_collaborator_assignment_requires_config_flag():
    artesp_org = _artesp_org()
    creator = _user()
    sysadmin = _sysadmin()
    collaborator = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)
    previous_value = toolkit.config.get("ckan.auth.allow_admin_collaborators")
    toolkit.config["ckan.auth.allow_admin_collaborators"] = False

    try:
        with pytest.raises(toolkit.ValidationError):
            _call_action_as(
                sysadmin,
                "package_collaborator_create",
                id=package.id,
                user_id=collaborator["id"],
                capacity="admin",
            )
    finally:
        toolkit.config["ckan.auth.allow_admin_collaborators"] = previous_value


def test_anonymous_requests_are_denied_for_relevant_operations():
    artesp_org = _artesp_org()
    creator = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)
    resource = _create_resource_row(package)

    _assert_auth_denied(None, "package_create", owner_org=artesp_org["id"])
    _assert_auth_denied(None, "package_update", id=package.id)
    _assert_auth_denied(None, "resource_create", package_id=package.id)
    _assert_auth_denied(None, "package_collaborator_list", id=package.id)
    _assert_auth_denied(None, "resource_update", id=resource.id)


def test_direct_auth_functions_handle_missing_context_and_payload_safely():
    artesp_org = _artesp_org()
    package = _create_dataset_row(artesp_org["id"])
    resource = _create_resource_row(package)

    assert artesp_auth.package_create({"model": model}, {"owner_org": artesp_org["id"]})[
        "success"
    ] is False
    assert artesp_auth.package_create(
        {"model": model, "user": "missing-user"},
        {"owner_org": artesp_org["id"]},
    )["success"] is False
    assert artesp_auth.package_update({"model": model, "user": ""}, {"id": package.id})[
        "success"
    ] is False
    assert artesp_auth.resource_create({"model": model, "user": ""}, {"package_id": package.id})[
        "success"
    ] is False
    assert artesp_auth.package_collaborator_create(
        {"model": model, "user": ""},
        {"id": package.id, "user_id": "missing-user", "capacity": "member"},
    )["success"] is False
    assert artesp_auth.resource_update({"model": model, "user": ""}, {"id": resource.id})[
        "success"
    ] is False


def test_nonexistent_dataset_resource_and_incomplete_payloads_are_denied_safely():
    user = _user()

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
    artesp_org = _artesp_org()
    creator = _user()
    other_user = _user()

    package_obj = _create_dataset_row(artesp_org["id"], creator=creator)
    package_obj.creator_user_id = "deleted-or-legacy-user"
    model.Session.add(package_obj)
    model.Session.flush()

    _assert_auth_denied(other_user, "package_update", id=package_obj.id)
    _assert_auth_denied(creator, "package_update", id=package_obj.id)

    _add_collaborator_row(package_obj, creator, "editor")

    _assert_auth_allowed(creator, "package_update", id=package_obj.id)


def test_self_removal_is_blocked_when_it_would_orphan_collaborator_governance():
    artesp_org = _artesp_org()
    creator = _user()
    collaborator_admin = _user()

    package_obj = _create_dataset_row(artesp_org["id"], creator=creator)
    package_obj.creator_user_id = None
    model.Session.add(package_obj)
    model.Session.flush()

    _add_collaborator_row(package_obj, collaborator_admin, "admin")

    _assert_action_denied(
        collaborator_admin,
        "package_collaborator_delete",
        id=package_obj.id,
        user_id=collaborator_admin["id"],
    )


# ---------------------------------------------------------------------------
# Branch coverage for auth edge cases
# ---------------------------------------------------------------------------

def test_package_create_sysadmin_is_allowed_directly():
    """Line 43: sysadmin allow path in package_create."""
    _artesp_org()
    sysadmin = _sysadmin()

    result = test_helpers.call_auth(
        "package_create",
        context=_auth_context(sysadmin),
    )
    assert result  # call_auth returns True or dict with success


def test_package_create_denied_when_artesp_org_missing(monkeypatch):
    """Line 51: deny when ARTESP org does not exist."""
    from ckanext.artesp_theme.logic import auth as artesp_auth
    from ckanext.artesp_theme.logic import auth_helpers

    regular_user = _user()
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
    regular_user = _user()
    _assert_auth_denied(regular_user, "organization_create")


def test_dataset_rating_upsert_denies_anonymous():
    """Line 210: dataset_rating_upsert with no user context."""
    from ckanext.artesp_theme.logic import auth as artesp_auth

    result = artesp_auth.dataset_rating_upsert({"model": model})
    assert result["success"] is False


def test_authorize_package_operation_sysadmin_allowed():
    """Line 266: _authorize_package_operation allows sysadmin."""
    artesp_org = _artesp_org()
    creator = _user()
    sysadmin = _sysadmin()

    package = _create_dataset_row(artesp_org["id"], creator=creator)
    result = test_helpers.call_auth(
        "package_update",
        context=_auth_context(sysadmin),
        id=package.id,
    )
    assert result  # sysadmin is allowed


def test_authorize_package_operation_denies_no_id():
    """Line 277: _authorize_package_operation with no data_dict id."""
    regular_user = _user()
    _assert_auth_denied(regular_user, "package_update")


def test_authorize_package_operation_denies_non_artesp_dataset():
    """Line 284: _authorize_package_operation when package not in artesp org."""
    _artesp_org()
    other_org = factories.Organization(name=_unique_name("other-org-x"))
    creator = _user()

    # Create dataset at model level to bypass the custom action restriction
    other_org_obj = model.Group.get(other_org["id"])
    pkg = model.Package(
        name=_unique_name("other-ds"),
        title="Other org dataset",
        owner_org=other_org_obj.id,
        state="active",
    )
    model.Session.add(pkg)
    model.Session.flush()

    _assert_auth_denied(creator, "package_update", id=pkg.id)


def test_authorize_package_operation_denies_moving_outside_artesp():
    """Line 291: deny when owner_org is changed to non-artesp org."""
    artesp_org = _artesp_org()
    other_org = factories.Organization(name=_unique_name("other-move"))
    creator = _user()
    package = _create_dataset_row(artesp_org["id"], creator=creator)

    # creator tries to move to other org
    result = artesp_auth.package_update(
        {"model": model, "auth_user_obj": model.User.get(creator["name"])},
        {"id": package.id, "owner_org": other_org["id"]},
    )
    assert result["success"] is False


def test_authorize_resource_operation_sysadmin_allowed():
    """Line 315: _authorize_resource_operation allows sysadmin."""
    artesp_org = _artesp_org()
    creator = _user()
    sysadmin = _sysadmin()

    package = _create_dataset_row(artesp_org["id"], creator=creator)
    resource = _create_resource_row(package)

    result = test_helpers.call_auth(
        "resource_update",
        context=_auth_context(sysadmin),
        id=resource.id,
    )
    assert result  # sysadmin is allowed


def test_authorize_resource_operation_denies_missing_parent_dataset(monkeypatch):
    """Line 335: deny when parent dataset cannot be resolved."""
    from ckanext.artesp_theme.logic import auth as artesp_auth
    from ckanext.artesp_theme.logic import auth_helpers

    regular_user = _user()
    user_obj = model.User.get(regular_user["name"])

    # resource_create path — package_id that resolves to nothing
    result = artesp_auth.resource_create(
        {"model": model, "auth_user_obj": user_obj},
        {"package_id": "nonexistent-package-id"},
    )
    assert result["success"] is False


def test_authorize_resource_operation_denies_non_artesp_resource():
    """Line 338: deny when resource belongs to non-artesp dataset."""
    _artesp_org()
    other_org = factories.Organization(name=_unique_name("other-res-org"))
    creator = _user()

    # Create package at model level to bypass custom action restriction
    other_org_obj = model.Group.get(other_org["id"])
    pkg = model.Package(
        name=_unique_name("other-res-ds"),
        title="Other org dataset for resource",
        owner_org=other_org_obj.id,
        state="active",
    )
    model.Session.add(pkg)
    model.Session.flush()

    resource = _create_resource_row(pkg, url="https://example.com/res.csv")

    _assert_auth_denied(creator, "resource_update", id=resource.id)


def test_authorize_collaborator_operation_sysadmin_allowed():
    """Line 368: _authorize_collaborator_operation allows sysadmin."""
    artesp_org = _artesp_org()
    creator = _user()
    sysadmin = _sysadmin()

    package = _create_dataset_row(artesp_org["id"], creator=creator)

    result = test_helpers.call_auth(
        "package_collaborator_list",
        context=_auth_context(sysadmin),
        id=package.id,
    )
    assert result  # sysadmin is allowed


def test_authorize_collaborator_operation_denies_no_id():
    """Line 382: deny when no dataset id."""
    regular_user = _user()
    _assert_auth_denied(regular_user, "package_collaborator_list")


def test_authorize_collaborator_operation_denies_non_artesp_dataset():
    """Line 389: deny when dataset not in artesp org."""
    _artesp_org()
    other_org = factories.Organization(name=_unique_name("other-collab-org"))
    creator = _user()

    other_org_obj = model.Group.get(other_org["id"])
    pkg = model.Package(
        name=_unique_name("other-collab-ds"),
        title="Other org for collaborators",
        owner_org=other_org_obj.id,
        state="active",
    )
    model.Session.add(pkg)
    model.Session.flush()

    _assert_auth_denied(creator, "package_collaborator_list", id=pkg.id)


def test_validate_requested_capacity_sysadmin_no_capacity_is_denied():
    """Lines 401, 403: sysadmin with no capacity set → deny."""
    artesp_org = _artesp_org()
    creator = _user()
    sysadmin = _sysadmin()
    collaborator = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)

    # sysadmin trying to add collaborator without capacity
    with pytest.raises(toolkit.ValidationError):
        _call_action_as(
            sysadmin,
            "package_collaborator_create",
            id=package.id,
            user_id=collaborator["id"],
            # no capacity
        )


def test_validate_requested_capacity_invalid_capacity_is_denied():
    """Lines 405-407: invalid capacity string."""
    artesp_org = _artesp_org()
    creator = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)
    other_user = _user()

    with pytest.raises((toolkit.NotAuthorized, toolkit.ValidationError)):
        _call_action_as(
            creator,
            "package_collaborator_create",
            id=package.id,
            user_id=other_user["id"],
            capacity="superuser",  # invalid capacity
        )


def test_validate_requested_capacity_non_default_role_denied_for_non_sysadmin():
    """Line 412: non-sysadmin cannot change from default capacity."""
    artesp_org = _artesp_org()
    creator = _user()
    collaborator = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)

    # creator trying to add with non-default "member" capacity (default is "editor")
    with pytest.raises(toolkit.NotAuthorized):
        _call_action_as(
            creator,
            "package_collaborator_create",
            id=package.id,
            user_id=collaborator["id"],
            capacity="member",
        )


def test_target_user_not_found_is_denied():
    """Line 418: target user not found — auth denies when target user doesn't exist."""
    artesp_org = _artesp_org()
    creator = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)

    # Call auth directly (bypasses normalize which tries LDAP)
    result = artesp_auth.package_collaborator_create(
        _auth_context(creator),
        {"id": package.id, "user_id": "nonexistent-user-id-xyz"},
    )
    assert result["success"] is False


def test_existing_collaborator_non_sysadmin_cannot_change_role():
    """Line 427: existing collaborator + non-sysadmin cannot change role."""
    artesp_org = _artesp_org()
    creator = _user()
    collaborator = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)
    # Add collaborator as default (editor)
    _call_action_as(
        creator,
        "package_collaborator_create",
        id=package.id,
        user_id=collaborator["id"],
    )

    # Try to re-add (change role) — non-sysadmin cannot change
    with pytest.raises(toolkit.NotAuthorized):
        _call_action_as(
            creator,
            "package_collaborator_create",
            id=package.id,
            user_id=collaborator["id"],
        )


def test_require_existing_collaborator_not_found_is_denied():
    """Line 432: require_existing_collaborator but collaborator not found."""
    artesp_org = _artesp_org()
    creator = _user()
    non_collaborator = _user()

    package = _create_dataset_row(artesp_org["id"], creator=creator)

    # Try to delete a collaborator that doesn't exist
    with pytest.raises(toolkit.NotAuthorized):
        _call_action_as(
            creator,
            "package_collaborator_delete",
            id=package.id,
            user_id=non_collaborator["id"],
        )
