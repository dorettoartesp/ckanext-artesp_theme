"""Unit tests for rating administration helpers."""

from types import SimpleNamespace

from ckanext.artesp_theme.logic import rating_admin


def test_get_ratings_empty(monkeypatch):
    class FakeQuery:
        def filter_by(self, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def all(self):
            return []

    fake_session = SimpleNamespace(query=lambda cls: FakeQuery())

    monkeypatch.setattr(rating_admin.model, "Session", fake_session)

    assert rating_admin.get_ratings_for_package("pkg-123") == []


def test_get_ratings_for_user_includes_user_role(monkeypatch):
    rating = SimpleNamespace(
        id="rating-1",
        package_id="pkg-123",
        user_id="author-1",
        overall_rating=4,
        criteria={},
        comment="",
        status="finalizado",
        created_at="2026-04-22T10:00:00",
    )
    package = SimpleNamespace(title="Dataset de teste", name="dataset-de-teste")

    class FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def filter_by(self, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def all(self):
            return [rating]

    fake_session = SimpleNamespace(query=lambda cls: FakeQuery())

    monkeypatch.setattr(rating_admin.model, "Session", fake_session)
    monkeypatch.setattr(rating_admin, "_get_editable_package_ids", lambda user_id: {"pkg-123"})
    monkeypatch.setattr(rating_admin, "_get_user_roles_for_packages", lambda user_id, pkg_ids: {"pkg-123": "Criador"})
    monkeypatch.setattr(
        rating_admin.model,
        "Package",
        SimpleNamespace(get=lambda package_id: package if package_id == "pkg-123" else None),
    )
    monkeypatch.setattr(
        rating_admin.model,
        "User",
        SimpleNamespace(get=lambda user_id: SimpleNamespace(fullname="Autor", name="autor")),
    )

    rows = rating_admin.get_ratings_for_user("manager-1")

    assert rows[0]["user_role"] == "Criador"


def test_get_ratings_for_user_includes_dataset_name(monkeypatch):
    rating = SimpleNamespace(
        id="rating-1",
        package_id="pkg-123",
        user_id="author-1",
        overall_rating=4,
        criteria={},
        comment="",
        status="finalizado",
        created_at="2026-04-22T10:00:00",
    )
    package = SimpleNamespace(title="Dataset de teste", name="dataset-de-teste")

    class FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def filter_by(self, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def all(self):
            return [rating]

    fake_session = SimpleNamespace(query=lambda cls: FakeQuery())

    monkeypatch.setattr(rating_admin.model, "Session", fake_session)
    monkeypatch.setattr(rating_admin, "_get_editable_package_ids", lambda user_id: {"pkg-123"})
    monkeypatch.setattr(rating_admin, "_get_user_roles_for_packages", lambda user_id, pkg_ids: {"pkg-123": "Criador"})
    monkeypatch.setattr(
        rating_admin.model,
        "Package",
        SimpleNamespace(get=lambda package_id: package if package_id == "pkg-123" else None),
    )
    monkeypatch.setattr(
        rating_admin.model,
        "User",
        SimpleNamespace(get=lambda user_id: SimpleNamespace(fullname="Autor Externo", name="autor-externo")),
    )

    rows = rating_admin.get_ratings_for_user("manager-1")

    assert rows[0]["dataset_name"] == "Dataset de teste"
    assert rows[0]["author_name"] == "Autor Externo"


def test_create_action_updates_status(monkeypatch):
    rating = SimpleNamespace(
        id="rating-1",
        package_id="pkg-123",
        user_id="user-1",
        status="pendente",
    )

    class FakeQuery:
        def get(self, rating_id):
            assert rating_id == "rating-1"
            return rating

    added = []
    committed = []
    fake_session = SimpleNamespace(
        query=lambda cls: FakeQuery(),
        add=added.append,
        commit=lambda: committed.append(True),
    )

    monkeypatch.setattr(rating_admin.model, "Session", fake_session)

    action = rating_admin.create_rating_action(
        "rating-1",
        "admin-1",
        "aprovado",
        "Avaliacao revisada",
        False,
    )

    assert rating.status == "aprovado"
    assert action.status_before == "pendente"
    assert action.status_after == "aprovado"
    assert action.email_sent is False
    assert added == [action]
    assert committed == [True]


def test_get_rating_detail_includes_actions(monkeypatch):
    rating = SimpleNamespace(
        id="rating-1",
        package_id="pkg-123",
        user_id="user-1",
        overall_rating=5,
        criteria={"links_work": True},
        comment="Bom dataset",
        status="pendente",
        created_at="2026-04-22T10:00:00",
    )
    action = SimpleNamespace(
        actor_id="admin-1",
        status_before="pendente",
        status_after="aprovado",
        note="Revisado",
        email_sent=False,
        created_at="2026-04-22T10:10:00",
    )

    class RatingQuery:
        def get(self, rating_id):
            assert rating_id == "rating-1"
            return rating

    class ActionQuery:
        def filter_by(self, **kwargs):
            assert kwargs == {"rating_id": "rating-1"}
            return self

        def order_by(self, *args, **kwargs):
            return self

        def all(self):
            return [action]

    def fake_query(cls):
        if cls is rating_admin.DatasetRating:
            return RatingQuery()
        if cls is rating_admin.RatingAction:
            return ActionQuery()
        raise AssertionError(cls)

    fake_user = SimpleNamespace(fullname="Admin Responsavel", name="admin")
    fake_session = SimpleNamespace(query=fake_query)

    monkeypatch.setattr(rating_admin.model, "Session", fake_session)
    monkeypatch.setattr(
        rating_admin.model,
        "User",
        SimpleNamespace(get=lambda user_id: fake_user if user_id == "admin-1" else None),
    )

    detail = rating_admin.get_rating_detail("rating-1")

    assert detail["rating"]["id"] == "rating-1"
    assert detail["actions"][0]["actor_name"] == "Admin Responsavel"
    assert detail["actions"][0]["status_after"] == "aprovado"
