"""Tests for dataset_rating_upsert / show / summary actions."""

import pytest
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.tests import factories

from ckanext.artesp_theme.logic import auth_helpers
from ckanext.artesp_theme.model import DatasetRating, dataset_rating_table


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


@pytest.fixture(autouse=True)
def _ensure_rating_table():
    bind = model.Session.get_bind()
    dataset_rating_table.create(bind=bind, checkfirst=True)
    model.Session.execute(dataset_rating_table.delete())
    model.Session.commit()
    yield
    model.Session.rollback()


@pytest.fixture
def artesp_org():
    org = auth_helpers.get_artesp_org()
    if org:
        return {"id": org.id, "name": org.name}
    return factories.Organization(name="artesp")


@pytest.fixture
def user(artesp_org):
    return factories.User()


@pytest.fixture
def pkg(user, artesp_org):
    return factories.Dataset(user=user, owner_org=artesp_org["id"])


@pytest.fixture
def context(user):
    return {"user": user["name"], "ignore_auth": True}


class TestDatasetRatingUpsert:
    def test_creates_rating(self, context, pkg):
        result = model.Session.execute.__class__  # ensure import works
        import ckan.plugins.toolkit as tk
        result = tk.get_action("dataset_rating_upsert")(
            context,
            {
                "package_id": pkg["id"],
                "overall_rating": 4,
                "criteria": {"links_work": True, "up_to_date": False, "well_structured": True},
            },
        )
        assert result["created"] is True
        assert "id" in result
        assert result["comment_notification_enqueued"] is False

    def test_updates_existing_rating(self, context, pkg):
        import ckan.plugins.toolkit as tk
        action = tk.get_action("dataset_rating_upsert")
        first = action(context, {"package_id": pkg["id"], "overall_rating": 3})
        second = action(context, {"package_id": pkg["id"], "overall_rating": 5})
        assert second["created"] is False
        assert second["id"] == first["id"]

        loaded = DatasetRating.get_for(context["user"] and model.User.get(context["user"]).id, pkg["id"])
        assert loaded.overall_rating == 5

    def test_invalid_overall_rating_raises(self, context, pkg):
        import ckan.plugins.toolkit as tk
        with pytest.raises(tk.ValidationError):
            tk.get_action("dataset_rating_upsert")(
                context, {"package_id": pkg["id"], "overall_rating": 6}
            )

    def test_invalid_criteria_key_raises(self, context, pkg):
        import ckan.plugins.toolkit as tk
        with pytest.raises(tk.ValidationError):
            tk.get_action("dataset_rating_upsert")(
                context,
                {"package_id": pkg["id"], "overall_rating": 3, "criteria": {"bogus_key": True}},
            )

    def test_comment_notification_enqueued_when_comment_given(self, context, pkg, monkeypatch):
        import ckan.plugins.toolkit as tk
        import ckanext.artesp_theme.logic.action as action_mod

        enqueued = {}

        def fake_enqueue(package_id, rating_id):
            enqueued["package_id"] = package_id
            enqueued["rating_id"] = rating_id

        monkeypatch.setattr(action_mod, "_enqueue_rating_notification", fake_enqueue)

        result = tk.get_action("dataset_rating_upsert")(
            context,
            {"package_id": pkg["id"], "overall_rating": 5, "comment": "Great data!"},
        )
        assert result["comment_notification_enqueued"] is True
        assert enqueued["package_id"] == pkg["id"]

    def test_anonymous_raises(self, pkg):
        with pytest.raises((tk.NotAuthorized, tk.ValidationError)):
            tk.get_action("dataset_rating_upsert")(
                {}, {"package_id": pkg["id"], "overall_rating": 3}
            )

    def test_missing_dataset_raises_object_not_found(self, context):
        with pytest.raises(tk.ObjectNotFound):
            tk.get_action("dataset_rating_upsert")(
                context,
                {"package_id": "missing-dataset-id", "overall_rating": 3},
            )


class TestDatasetRatingShow:
    def test_returns_own_rating(self, context, user, pkg):
        import ckan.plugins.toolkit as tk
        tk.get_action("dataset_rating_upsert")(
            context,
            {"package_id": pkg["id"], "overall_rating": 4, "comment": "nice"},
        )
        result = tk.get_action("dataset_rating_show")(context, {"package_id": pkg["id"]})
        assert result["overall_rating"] == 4
        assert result["comment"] == "nice"

    def test_returns_none_when_no_rating(self, context, pkg):
        import ckan.plugins.toolkit as tk
        result = tk.get_action("dataset_rating_show")(context, {"package_id": pkg["id"]})
        assert result is None

    def test_does_not_expose_other_user_rating(self, artesp_org, pkg):
        import ckan.plugins.toolkit as tk
        user_b = factories.User()
        ctx_b = {"user": user_b["name"], "ignore_auth": True}
        tk.get_action("dataset_rating_upsert")(
            ctx_b, {"package_id": pkg["id"], "overall_rating": 2}
        )
        user_a = factories.User()
        ctx_a = {"user": user_a["name"], "ignore_auth": True}
        result = tk.get_action("dataset_rating_show")(ctx_a, {"package_id": pkg["id"]})
        assert result is None


class TestDatasetRatingSummary:
    def test_empty_summary(self, context, pkg):
        import ckan.plugins.toolkit as tk
        result = tk.get_action("dataset_rating_summary")(context, {"package_id": pkg["id"]})
        assert result["package_id"] == pkg["id"]
        assert result["overall"]["count"] == 0
        assert result["overall"]["average"] is None

    def test_aggregates_ratings(self, artesp_org, pkg):
        import ckan.plugins.toolkit as tk
        for rating in (3, 5):
            u = factories.User()
            tk.get_action("dataset_rating_upsert")(
                {"user": u["name"], "ignore_auth": True},
                {"package_id": pkg["id"], "overall_rating": rating},
            )
        result = tk.get_action("dataset_rating_summary")({}, {"package_id": pkg["id"]})
        assert result["overall"]["count"] == 2
        assert result["overall"]["average"] == pytest.approx(4.0)

    def test_criteria_aggregation(self, artesp_org, pkg):
        for val in (True, False):
            u = factories.User()
            tk.get_action("dataset_rating_upsert")(
                {"user": u["name"], "ignore_auth": True},
                {
                    "package_id": pkg["id"],
                    "overall_rating": 3,
                    "criteria": {"links_work": val, "up_to_date": True, "well_structured": True},
                },
            )
        result = tk.get_action("dataset_rating_summary")({}, {"package_id": pkg["id"]})
        criteria = result["overall"]["criteria"]
        assert criteria["links_work"]["yes"] == 1
        assert criteria["links_work"]["no"] == 1

    def test_omitted_criteria_do_not_count_as_negative_votes(self, artesp_org, pkg):
        for _ in range(2):
            u = factories.User()
            tk.get_action("dataset_rating_upsert")(
                {"user": u["name"], "ignore_auth": True},
                {"package_id": pkg["id"], "overall_rating": 4},
            )

        result = tk.get_action("dataset_rating_summary")({}, {"package_id": pkg["id"]})
        criteria = result["overall"]["criteria"]
        assert criteria["links_work"] == {"yes": 0, "no": 0}
        assert criteria["up_to_date"] == {"yes": 0, "no": 0}
        assert criteria["well_structured"] == {"yes": 0, "no": 0}

    def test_private_dataset_summary_requires_visibility(self, artesp_org):
        owner = factories.User()
        private_pkg = factories.Dataset(
            user=owner,
            owner_org=artesp_org["id"],
            private=True,
        )

        with pytest.raises((tk.NotAuthorized, tk.ObjectNotFound)):
            tk.get_action("dataset_rating_summary")({}, {"package_id": private_pkg["id"]})

    def test_summary_does_not_expose_user_data(self, context, user, pkg):
        tk.get_action("dataset_rating_upsert")(
            context, {"package_id": pkg["id"], "overall_rating": 5}
        )
        result = tk.get_action("dataset_rating_summary")({}, {"package_id": pkg["id"]})
        result_str = str(result)
        assert user["name"] not in result_str
        assert user.get("email", "") not in result_str
