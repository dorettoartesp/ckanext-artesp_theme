import os

import pytest

_INTEGRATION_FIXTURES = {"clean_db", "clean_index"}
_APP_FIXTURES = {"app", "ckan_config", "with_plugins"}


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Redirect --ckan-ini to a per-worker ini when running under pytest-xdist."""
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if not worker_id:
        return
    worker_ini = f"/tmp/ckan_test_{worker_id}.ini"
    if os.path.exists(worker_ini):
        try:
            config.option.ckan_ini = worker_ini
        except AttributeError:
            pass


def pytest_collection_modifyitems(items):
    for item in items:
        fixtures = set(item.fixturenames)
        if _INTEGRATION_FIXTURES & fixtures:
            item.add_marker(pytest.mark.integration)
        elif _APP_FIXTURES & fixtures:
            item.add_marker(pytest.mark.app)
        else:
            item.add_marker(pytest.mark.unit)
