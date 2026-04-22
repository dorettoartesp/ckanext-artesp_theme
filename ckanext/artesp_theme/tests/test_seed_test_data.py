import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


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


def test_load_internal_manager_specs_reads_ldif_users():
    specs = seed_test_data.load_internal_manager_specs()

    assert [spec.username for spec in specs] == [
        "joao.silva",
        "maria.santos",
        "admin.artesp",
    ]
    assert [spec.email for spec in specs] == [
        "joao.silva@artesp.sp.gov.br",
        "maria.santos@artesp.sp.gov.br",
        "admin@artesp.sp.gov.br",
    ]


def test_build_external_rating_user_payload_marks_user_as_external():
    config = seed_test_data.SeedConfig(
        ckan_url="http://localhost:5000",
        api_key="dummy-token",
        prefix="seed-artesp",
        owner_org="artesp",
        organization_count=0,
        group_count=0,
        dataset_count=0,
        resources_per_dataset=0,
        heavy_dataset_resources=0,
        heavy_dataset_slug="dataset-muitos-recursos",
        skip_heavy_dataset=True,
        rating_users_count=3,
    )

    payload = seed_test_data.build_external_rating_user_payload(config, 0)

    assert payload["name"] == "seed-artesp-govbr-01"
    assert payload["email"] == "seed-artesp-govbr-01@govbr.invalid"
    assert payload["plugin_extras"]["artesp"]["user_type"] == "external"
    assert payload["plugin_extras"]["artesp"]["govbr_sub"] == (
        "seed-govbr-seed-artesp-01"
    )


def test_rating_status_for_comment_uses_same_default_as_admin_flow():
    assert seed_test_data.rating_status_for_comment("") == "finalizado"
    assert seed_test_data.rating_status_for_comment(" Comentario ") == "pendente"


def test_ensure_internal_manager_user_uses_ldap_resolution(monkeypatch):
    spec = seed_test_data.InternalManagerSpec(
        username="joao.silva",
        fullname="Joao Silva",
        email="joao.silva@artesp.sp.gov.br",
        password="senha123",
    )
    resolved_user = SimpleNamespace(
        id="user-id-1",
        name="joao_silva",
        fullname="Joao Silva",
        email="joao.silva@artesp.sp.gov.br",
    )

    monkeypatch.setattr(
        seed_test_data,
        "resolve_internal_manager_user",
        lambda spec, ckan_url=None: resolved_user,
    )

    user = seed_test_data.ensure_internal_manager_user(None, spec)

    assert user["id"] == "user-id-1"
    assert user["name"] == "joao_silva"
