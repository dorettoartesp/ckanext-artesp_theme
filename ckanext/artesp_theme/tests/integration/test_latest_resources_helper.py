"""Integration tests for the latest resources helper."""

from datetime import datetime, timedelta
from unittest.mock import patch
import uuid

import pytest
import ckan.model as model

import ckanext.artesp_theme.helpers as helpers


class TestGetLatestResources:
    pytestmark = [
        pytest.mark.integration,
        pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
        pytest.mark.usefixtures("with_plugins"),
        pytest.mark.xdist_group("helpers_latest_resources"),
    ]

    @pytest.fixture(autouse=True)
    def _cleanup_latest_resources_rows(self):
        (
            model.Session.query(model.Resource)
            .filter(model.Resource.url.like("https://example.com/latestres-%"))
            .delete(synchronize_session=False)
        )
        (
            model.Session.query(model.Package)
            .filter(model.Package.name.like("latestres-dataset-%"))
            .delete(synchronize_session=False)
        )
        model.Session.commit()
        yield
        (
            model.Session.query(model.Resource)
            .filter(model.Resource.url.like("https://example.com/latestres-%"))
            .delete(synchronize_session=False)
        )
        (
            model.Session.query(model.Package)
            .filter(model.Package.name.like("latestres-dataset-%"))
            .delete(synchronize_session=False)
        )
        model.Session.commit()

    def _package(self, title="Dataset", owner_org="artesp"):
        package = model.Package(
            name="latestres-dataset-{}".format(uuid.uuid4().hex[:8]),
            title=title,
            owner_org=owner_org,
            state="active",
        )
        model.Session.add(package)
        model.Session.flush()
        return package

    def _resource(self, package, name, seconds=0):
        resource = model.Resource(
            package_id=package.id,
            name=name,
            url="https://example.com/latestres-{}.csv".format(uuid.uuid4().hex[:8]),
            metadata_modified=datetime.utcnow() + timedelta(seconds=seconds),
        )
        resource.state = "active"
        model.Session.add(resource)
        model.Session.flush()
        return resource

    def _patch_package_show(self, monkeypatch, *packages):
        package_dicts = {
            package.id: {"id": package.id, "title": package.title, "name": package.name}
            for package in packages
        }

        def fake_get_action(name):
            assert name == "package_show"
            return lambda context, data_dict: package_dicts[data_dict["id"]]

        monkeypatch.setattr(helpers.toolkit, "get_action", fake_get_action)

    def test_returns_latest_resources_with_dataset_context(self, monkeypatch):
        dataset = self._package(title="Dataset title")
        resource = self._resource(dataset, "latest-resource", seconds=86400)
        self._patch_package_show(monkeypatch, dataset)

        results = helpers.get_latest_resources(limit=1)

        assert len(results) == 1
        assert results[0]["resource"].id == resource.id
        assert results[0]["dataset"]["id"] == dataset.id
        assert results[0]["parent_dataset_title"] == dataset.title

    def test_filters_latest_resources_by_dataset_id(self, monkeypatch):
        dataset = self._package()
        other_dataset = self._package()
        self._resource(dataset, "dataset-resource")
        self._resource(other_dataset, "other-resource", seconds=1)
        self._patch_package_show(monkeypatch, dataset, other_dataset)

        results = helpers.get_latest_resources(limit=10, dataset_id=dataset.id)

        assert results
        assert all(item["resource"].package_id == dataset.id for item in results)

    def test_filters_latest_resources_by_org_id(self, monkeypatch):
        artesp_org_id = "artesp-org"
        dataset = self._package(owner_org=artesp_org_id)
        other_package = self._package(title="Other org dataset", owner_org="other-org")

        self._resource(dataset, "artesp-resource")
        self._resource(other_package, "other-resource", seconds=1)
        self._patch_package_show(monkeypatch, dataset, other_package)

        results = helpers.get_latest_resources(limit=10, org_id=artesp_org_id)

        assert results
        assert all(item["resource"].package_id == dataset.id for item in results)

    def test_skips_resource_when_package_lookup_fails(self, monkeypatch):
        dataset = self._package()
        self._resource(dataset, "broken-package-resource")

        monkeypatch.setattr(
            helpers.toolkit,
            "get_action",
            lambda name: (
                lambda context, data_dict: (_ for _ in ()).throw(Exception("boom"))
            ),
        )

        assert helpers.get_latest_resources(limit=5) == []

    def test_returns_empty_when_query_raises(self):
        with patch(
            "ckanext.artesp_theme.helpers.Session.query",
            side_effect=Exception("database down"),
        ):
            assert helpers.get_latest_resources(limit=5) == []
