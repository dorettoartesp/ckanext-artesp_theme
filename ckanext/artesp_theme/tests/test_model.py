"""Tests for the DatasetRating model."""

import uuid

import ckan.model as model
import pytest
from ckan.tests import factories
from sqlalchemy.exc import IntegrityError

from ckanext.artesp_theme.logic import auth_helpers
from ckanext.artesp_theme.model import DatasetRating, dataset_rating_table


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


@pytest.fixture(autouse=True)
def _ensure_dataset_rating_table():
    bind = model.Session.get_bind()
    dataset_rating_table.create(bind=bind, checkfirst=True)
    model.Session.execute(dataset_rating_table.delete())
    model.Session.commit()
    yield
    model.Session.rollback()


@pytest.fixture
def org_and_user():
    artesp_org = auth_helpers.get_artesp_org()
    org = (
        {"id": artesp_org.id, "name": artesp_org.name}
        if artesp_org
        else factories.Organization(name="artesp")
    )
    user = factories.User()
    return org, user


def _package(user=None, owner_org="artesp"):
    package = model.Package(
        name="rating-model-pkg-{}".format(uuid.uuid4().hex[:8]),
        title="Rating model package",
        owner_org=owner_org,
        creator_user_id=user["id"] if isinstance(user, dict) else None,
        state="active",
    )
    model.Session.add(package)
    model.Session.commit()
    return package


class TestDatasetRating:
    def test_status_defaults_to_finalizado_without_comment(self):
        rating = DatasetRating(
            user_id="user-id",
            package_id="package-id",
            overall_rating=4,
            comment="",
        )

        assert rating.status == "finalizado"

    def test_status_defaults_to_pendente_with_comment(self):
        rating = DatasetRating(
            user_id="user-id",
            package_id="package-id",
            overall_rating=4,
            comment="Precisa atualizar o dicionario de dados",
        )

        assert rating.status == "pendente"

    def test_create_and_persist(self, org_and_user):
        org, user = org_and_user
        pkg = _package(user=user, owner_org=org["id"])
        r = DatasetRating(
            user_id=user["id"],
            package_id=pkg.id,
            overall_rating=5,
            criteria={"links_work": True},
            comment="Great dataset",
        )
        model.Session.add(r)
        model.Session.commit()

        loaded = DatasetRating.get_for(user["id"], pkg.id)
        assert loaded is not None
        assert loaded.overall_rating == 5
        assert loaded.criteria == {"links_work": True}
        assert loaded.comment == "Great dataset"
        assert loaded.created_at is not None
        assert loaded.updated_at is not None
        assert loaded.id

    def test_get_for_returns_none_when_missing(self):
        assert DatasetRating.get_for("missing-user", "missing-package") is None

    def test_unique_per_user_and_package(self, org_and_user):
        org, user = org_and_user
        pkg = _package(user=user, owner_org=org["id"])
        model.Session.add(
            DatasetRating(
                user_id=user["id"], package_id=pkg.id, overall_rating=3
            )
        )
        model.Session.commit()

        model.Session.add(
            DatasetRating(
                user_id=user["id"], package_id=pkg.id, overall_rating=4
            )
        )
        with pytest.raises(IntegrityError):
            model.Session.commit()
        model.Session.rollback()

    def test_list_for_package_orders_by_updated_at_desc(self, org_and_user):
        org, user_a = org_and_user
        user_b = factories.User()
        pkg = _package(user=user_a, owner_org=org["id"])

        r1 = DatasetRating(user_id=user_a["id"], package_id=pkg.id, overall_rating=4)
        model.Session.add(r1)
        model.Session.commit()

        r2 = DatasetRating(user_id=user_b["id"], package_id=pkg.id, overall_rating=5)
        model.Session.add(r2)
        model.Session.commit()

        listed = DatasetRating.list_for_package(pkg.id)
        assert [r.user_id for r in listed] == [user_b["id"], user_a["id"]]
