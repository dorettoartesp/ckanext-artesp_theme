import importlib.util
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[3] / "utils" / "seed_test_data.py"
)
SPEC = importlib.util.spec_from_file_location("seed_test_data_module", MODULE_PATH)
seed_test_data = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(seed_test_data)


def test_parse_args_defaults_owner_org_from_env(monkeypatch):
    monkeypatch.setenv("CKAN_SEED_OWNER_ORG", "artesp")
    monkeypatch.setattr(
        sys,
        "argv",
        ["seed_test_data.py", "--api-key", "dummy-token"],
    )

    config = seed_test_data.parse_args()

    assert config.owner_org == "artesp"


def test_parse_args_explicit_owner_org_overrides_env(monkeypatch):
    monkeypatch.setenv("CKAN_SEED_OWNER_ORG", "artesp")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "seed_test_data.py",
            "--api-key",
            "dummy-token",
            "--owner-org",
            "outra-org",
        ],
    )

    config = seed_test_data.parse_args()

    assert config.owner_org == "outra-org"
