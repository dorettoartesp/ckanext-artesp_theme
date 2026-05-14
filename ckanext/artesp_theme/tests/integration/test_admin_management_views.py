import csv
import io
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


def _csv_rows(response):
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8-sig")
    else:
        body = body.lstrip("\ufeff")
    return list(csv.DictReader(io.StringIO(body), delimiter=";"))


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

    export_anonymous = app.get("/admin/gestao/usuarios/export.csv", expect_errors=True)
    export_regular = app.get(
        "/admin/gestao/usuarios/export.csv",
        environ_base={"REMOTE_USER": user["name"]},
        expect_errors=True,
    )

    assert export_anonymous.status_code == 403
    assert export_regular.status_code == 403


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

    assert "Usuários" in users_page.text
    assert username in users_page.text
    assert email in users_page.text
    assert "pagination" in users_page.text
    assert dataset_name not in users_page.text

    assert "Conjuntos de Dados" in datasets_page.text
    assert '<li class="active"><a href="/admin/gestao/usuarios"><i class="fa fa-users"></i>Gestão</a></li>' in datasets_page.text
    assert "sort_by=title" in datasets_page.text
    assert "sort_by=owner_org" in datasets_page.text
    assert "sort_by=creator" in datasets_page.text
    assert "sort_by=resources" in datasets_page.text
    assert dataset_name in datasets_page.text
    assert 'href="/dataset/edit/{}"'.format(dataset_name) in datasets_page.text
    assert "pagination" in datasets_page.text
    assert "gestao-resource.csv" not in datasets_page.text

    assert "Recursos" in resources_page.text
    assert '<li class="active"><a href="/admin/gestao/usuarios"><i class="fa fa-users"></i>Gestão</a></li>' in resources_page.text
    assert "sort_by=name" in resources_page.text
    assert "sort_by=dataset" in resources_page.text
    assert "sort_by=format" in resources_page.text
    assert "sort_by=updated" in resources_page.text
    assert "gestao-resource.csv" in resources_page.text
    assert 'href="/dataset/{}/resource/'.format(dataset_name) in resources_page.text
    assert "pagination" in resources_page.text


def test_admin_management_sorts_datasets_and_resources(app):
    suffix = uuid.uuid4().hex[:8]
    org = _artesp_org()
    sysadmin = factories.Sysadmin()
    dataset_a = factories.Dataset(
        name="gestao-sort-a-{}".format(suffix),
        title="AAA Gestao Sort {}".format(suffix),
        owner_org=org["id"],
    )
    dataset_z = factories.Dataset(
        name="gestao-sort-z-{}".format(suffix),
        title="ZZZ Gestao Sort {}".format(suffix),
        owner_org=org["id"],
    )
    factories.Resource(
        package_id=dataset_a["id"],
        name="aaa-gestao-sort-{}.csv".format(suffix),
        format="CSV",
        url="https://example.com/aaa-gestao-sort.csv",
    )
    factories.Resource(
        package_id=dataset_z["id"],
        name="zzz-gestao-sort-{}.json".format(suffix),
        format="JSON",
        url="https://example.com/zzz-gestao-sort.json",
    )

    datasets_page = app.get(
        "/admin/gestao/datasets?q=Gestao+Sort+{}&sort_by=title&sort_dir=asc".format(suffix),
        environ_base={"REMOTE_USER": sysadmin["name"]},
    )
    resources_page = app.get(
        "/admin/gestao/resources?q={}&sort_by=format&sort_dir=desc".format(suffix),
        environ_base={"REMOTE_USER": sysadmin["name"]},
    )

    assert datasets_page.text.index("AAA Gestao Sort") < datasets_page.text.index("ZZZ Gestao Sort")
    assert resources_page.text.index("zzz-gestao-sort") < resources_page.text.index("aaa-gestao-sort")


def test_admin_management_uses_standard_numbered_pagination(app):
    suffix = uuid.uuid4().hex[:8]
    sysadmin = factories.Sysadmin()
    for index in range(55):
        factories.User(
            name="gp{}{:02d}".format(suffix, index),
            email="gestao-page-{}-{:02d}@example.com".format(suffix, index),
        )

    response = app.get(
        "/admin/gestao/usuarios?q=gestao-page-{}&sort_by=name&sort_dir=asc&page=2".format(suffix),
        environ_base={"REMOTE_USER": sysadmin["name"]},
    )

    assert response.status_code == 200
    assert "55 registros" in response.text
    assert 'class="pagination-wrapper"' in response.text
    assert 'class="pagination justify-content-center"' in response.text
    assert "page=1" in response.text
    assert "q=gestao-page-{}".format(suffix) in response.text
    assert "sort_by=name" in response.text
    assert "sort_dir=asc" in response.text


def test_admin_management_exports_filtered_csv(app):
    suffix = uuid.uuid4().hex[:8]
    org = _artesp_org()
    sysadmin = factories.Sysadmin()
    user_a = factories.User(
        name="gestao-export-a-{}".format(suffix),
        email="a-{}@example.com".format(suffix),
        fullname="AAA Export User {}".format(suffix),
    )
    user_z = factories.User(
        name="gestao-export-z-{}".format(suffix),
        email="z-{}@example.com".format(suffix),
        fullname="ZZZ Export User {}".format(suffix),
    )
    dataset_a = factories.Dataset(
        name="gestao-export-a-{}".format(suffix),
        title="AAA Export Dataset {}".format(suffix),
        owner_org=org["id"],
        user=user_a,
        notes="Dataset export notes A",
        tags=[{"name": "export-a-{}".format(suffix)}],
    )
    dataset_z = factories.Dataset(
        name="gestao-export-z-{}".format(suffix),
        title="ZZZ Export Dataset {}".format(suffix),
        owner_org=org["id"],
        user=user_z,
        notes="Dataset export notes Z",
        tags=[{"name": "export-z-{}".format(suffix)}],
    )
    factories.Resource(
        package_id=dataset_a["id"],
        name="aaa-export-resource-{}.csv".format(suffix),
        description="Resource export notes A",
        format="CSV",
        url="https://example.com/aaa-export-resource.csv",
    )
    factories.Resource(
        package_id=dataset_z["id"],
        name="zzz-export-resource-{}.json".format(suffix),
        description="Resource export notes Z",
        format="JSON",
        url="https://example.com/zzz-export-resource.json",
    )

    users_response = app.get(
        "/admin/gestao/usuarios/export.csv?q={}&sort_by=name&sort_dir=desc".format(suffix),
        environ_base={"REMOTE_USER": sysadmin["name"]},
    )
    datasets_response = app.get(
        "/admin/gestao/datasets/export.csv?q=Export+Dataset+{}&sort_by=title&sort_dir=asc".format(suffix),
        environ_base={"REMOTE_USER": sysadmin["name"]},
    )
    resources_response = app.get(
        "/admin/gestao/resources/export.csv?q={}&sort_by=format&sort_dir=desc".format(suffix),
        environ_base={"REMOTE_USER": sysadmin["name"]},
    )

    assert users_response.headers["Content-Type"].startswith("text/csv")
    assert "attachment;" in users_response.headers["Content-Disposition"]
    assert "usuarios-gestao-" in users_response.headers["Content-Disposition"]
    assert users_response.body.startswith("\ufeff")

    user_rows = _csv_rows(users_response)
    dataset_rows = _csv_rows(datasets_response)
    resource_rows = _csv_rows(resources_response)

    assert user_rows[0]["usuario"].startswith("gestao-export-z-")
    assert user_rows[1]["usuario"].startswith("gestao-export-a-")
    assert {"id", "usuario", "nome_completo", "email", "sysadmin", "criado_em", "atualizado_em", "datasets_criados"} <= set(user_rows[0])

    assert dataset_rows[0]["titulo"].startswith("AAA Export Dataset")
    assert dataset_rows[1]["titulo"].startswith("ZZZ Export Dataset")
    assert dataset_rows[0]["tags"].startswith("export-a-")
    assert {"id", "nome", "titulo", "descricao", "organizacao", "criador", "licenca", "recursos", "colaboradores", "tags"} <= set(dataset_rows[0])

    assert resource_rows[0]["formato"] == "JSON"
    assert resource_rows[1]["formato"] == "CSV"
    assert resource_rows[0]["dataset_titulo"].startswith("ZZZ Export Dataset")
    assert {"id", "nome", "descricao", "formato", "mimetype", "url", "tamanho", "dataset_nome", "dataset_titulo", "organizacao"} <= set(resource_rows[0])


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
