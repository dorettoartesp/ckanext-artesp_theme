import ckan.model as model
import pytest
import uuid
from ckan.tests import factories

from ckanext.artesp_theme.logic import auth_helpers


pytestmark = [
    pytest.mark.integration,
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.ckan_config("ckan.auth.allow_dataset_collaborators", "true"),
    pytest.mark.ckan_config("ckan.auth.allow_admin_collaborators", "true"),
    pytest.mark.usefixtures("with_plugins"),
]


def _artesp_org():
    org = auth_helpers.get_artesp_org()
    if org:
        return {"id": org.id, "name": org.name}
    return factories.Organization(name="artesp")


def test_admin_management_requires_sysadmin(app):
    user = factories.User()

    anonymous = app.get("/admin/gestao", expect_errors=True)
    regular = app.get(
        "/admin/gestao",
        environ_base={"REMOTE_USER": user["name"]},
        expect_errors=True,
    )

    assert anonymous.status_code == 403
    assert regular.status_code == 403


def test_admin_management_has_separate_paginated_pages(app):
    suffix = uuid.uuid4().hex[:8]
    org = _artesp_org()
    sysadmin = factories.Sysadmin()
    username = "gestao-user-render-{}".format(suffix)
    email = "{}@example.com".format(username)
    dataset_name = "gestao-dataset-render-{}".format(suffix)
    user = factories.User(
        name=username,
        email=email,
        fullname="Usuario Gestao",
    )
    dataset = factories.Dataset(
        name=dataset_name,
        title="Dataset Gestao",
        owner_org=org["id"],
        user=user,
    )
    factories.Resource(
        package_id=dataset["id"],
        name="gestao-resource.csv",
        format="CSV",
        url="https://example.com/gestao-resource.csv",
    )

    users_page = app.get(
        "/admin/gestao/usuarios?q={}".format(username),
        environ_base={"REMOTE_USER": sysadmin["name"]},
    )
    datasets_page = app.get(
        "/admin/gestao/datasets?q={}".format(dataset_name),
        environ_base={"REMOTE_USER": sysadmin["name"]},
    )
    resources_page = app.get(
        "/admin/gestao/resources?q=gestao-resource.csv",
        environ_base={"REMOTE_USER": sysadmin["name"]},
    )

    assert users_page.status_code == 200
    assert datasets_page.status_code == 200
    assert resources_page.status_code == 200

    assert "Usuarios" in users_page.text
    assert username in users_page.text
    assert email in users_page.text
    assert "pagination" in users_page.text
    assert dataset_name not in users_page.text

    assert "Datasets" in datasets_page.text
    assert dataset_name in datasets_page.text
    assert 'href="/dataset/edit/{}"'.format(dataset_name) in datasets_page.text
    assert "pagination" in datasets_page.text
    assert "gestao-resource.csv" not in datasets_page.text

    assert "Resources" in resources_page.text
    assert "gestao-resource.csv" in resources_page.text
    assert 'href="/dataset/{}/resource/'.format(dataset_name) in resources_page.text
    assert "pagination" in resources_page.text


def test_admin_management_can_revoke_sysadmin(app):
    suffix = uuid.uuid4().hex[:8]
    sysadmin = factories.Sysadmin()
    target = factories.Sysadmin(name="gestao-target-sysadmin-{}".format(suffix))

    response = app.post(
        "/admin/gestao/sysadmin",
        data={"username": target["name"], "status": "0"},
        environ_base={"REMOTE_USER": sysadmin["name"]},
        follow_redirects=False,
    )

    model.Session.expire_all()
    target_obj = model.User.get(target["name"])

    assert response.status_code == 302
    assert target_obj.sysadmin is False


def test_admin_management_can_add_admin_collaborator(app):
    suffix = uuid.uuid4().hex[:8]
    org = _artesp_org()
    sysadmin = factories.Sysadmin()
    collaborator = factories.User(name="gestao-collaborator-{}".format(suffix))
    dataset = factories.Dataset(
        name="gestao-collab-dataset-{}".format(suffix),
        owner_org=org["id"],
    )

    response = app.post(
        "/admin/gestao/collaborator",
        data={
            "package_id": dataset["id"],
            "username": collaborator["name"],
            "capacity": "admin",
        },
        environ_base={"REMOTE_USER": sysadmin["name"]},
        follow_redirects=False,
    )

    model.Session.expire_all()
    member = (
        model.Session.query(model.PackageMember)
        .filter(model.PackageMember.package_id == dataset["id"])
        .filter(model.PackageMember.user_id == collaborator["id"])
        .one_or_none()
    )

    assert response.status_code == 302
    assert member is not None
    assert member.capacity == "admin"
