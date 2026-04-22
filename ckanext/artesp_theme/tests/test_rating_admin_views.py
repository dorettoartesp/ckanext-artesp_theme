"""Tests for rating administration views."""

import ckan.model as model
import pytest
from ckan.tests import factories

from ckanext.artesp_theme.model import (
    DatasetRating,
    RatingAction,
    dataset_rating_table,
    rating_action_table,
)


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


@pytest.fixture(autouse=True)
def _ensure_rating_admin_tables(clean_db):
    bind = model.Session.get_bind()
    dataset_rating_table.create(bind=bind, checkfirst=True)
    rating_action_table.create(bind=bind, checkfirst=True)
    yield


@pytest.fixture
def artesp_org():
    return factories.Organization(name="artesp")


@pytest.fixture
def user(artesp_org):
    return factories.User()


@pytest.fixture
def pkg(user, artesp_org):
    return factories.Dataset(user=user, owner_org=artesp_org["id"])


def test_rating_admin_list_renders_for_dataset_owner(app, user, pkg):
    rating_author = factories.User()
    rating = DatasetRating(
        user_id=rating_author["id"],
        package_id=pkg["id"],
        overall_rating=4,
        comment="",
    )
    model.Session.add(rating)
    model.Session.commit()

    response = app.get(
        f"/dataset/{pkg['name']}/rating-admin",
        environ_base={"REMOTE_USER": user["name"]},
        expect_errors=True,
    )

    assert response.status_code == 200
    assert "Avaliações" in response.text


def test_rating_admin_index_renders_for_internal_user(app, user, pkg):
    rating_author = factories.User()
    rating = DatasetRating(
        user_id=rating_author["id"],
        package_id=pkg["id"],
        overall_rating=4,
        comment="Comentario de teste",
    )
    model.Session.add(rating)
    model.Session.commit()

    response = app.get(
        f"/user/{user['name']}/rating-admin",
        environ_base={"REMOTE_USER": user["name"]},
        expect_errors=True,
    )

    assert response.status_code == 200
    assert "Dataset" in response.text
    assert (pkg["title"] or pkg["name"]) in response.text


def test_rating_admin_index_shows_user_role(app, user, pkg):
    rating_author = factories.User()
    rating = DatasetRating(
        user_id=rating_author["id"],
        package_id=pkg["id"],
        overall_rating=3,
        comment="Comentário de teste",
    )
    model.Session.add(rating)
    model.Session.commit()

    response = app.get(
        f"/user/{user['name']}/rating-admin",
        environ_base={"REMOTE_USER": user["name"]},
        expect_errors=True,
    )

    assert response.status_code == 200
    assert "Papel" in response.text
    assert "Criador" in response.text


def test_rating_admin_detail_renders_action_history(app, user, pkg):
    rating_author = factories.User()
    rating = DatasetRating(
        user_id=rating_author["id"],
        package_id=pkg["id"],
        overall_rating=4,
        comment="Precisa revisar a qualidade",
    )
    model.Session.add(rating)
    model.Session.commit()

    action = RatingAction(
        rating_id=rating.id,
        actor_id=user["id"],
        status_before="pendente",
        status_after="aprovado",
        note="Revisado",
    )
    model.Session.add(action)
    model.Session.commit()

    response = app.get(
        f"/dataset/{pkg['name']}/rating-admin/{rating.id}",
        environ_base={"REMOTE_USER": user["name"]},
        expect_errors=True,
    )

    assert response.status_code == 200
    assert "Histórico de ações" in response.text


def test_rating_admin_action_updates_status(app, user, pkg):
    rating_author = factories.User()
    rating = DatasetRating(
        user_id=rating_author["id"],
        package_id=pkg["id"],
        overall_rating=3,
        comment="Precisa de contexto adicional",
    )
    model.Session.add(rating)
    model.Session.commit()

    response = app.post(
        f"/dataset/{pkg['name']}/rating-admin/{rating.id}/action",
        data={"new_status": "aprovado", "note": "Tratado", "send_email": ""},
        environ_base={"REMOTE_USER": user["name"]},
        expect_errors=True,
    )

    model.Session.expire_all()
    updated = model.Session.query(DatasetRating).get(rating.id)

    assert response.status_code == 200
    assert "Histórico de ações" in response.text
    assert updated.status == "aprovado"
