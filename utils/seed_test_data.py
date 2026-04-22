import argparse
from dataclasses import dataclass
import datetime
import json
import os
from typing import Iterable
import uuid

import ckanapi
from ckanapi import errors


DEFAULT_CKAN_URL = os.environ.get("CKAN_URL", "http://localhost:5000")
DEFAULT_API_KEY = os.environ.get("CKAN_API_KEY")


@dataclass(frozen=True)
class SeedConfig:
    ckan_url: str
    api_key: str
    prefix: str
    owner_org: str | None
    organization_count: int
    group_count: int
    dataset_count: int
    resources_per_dataset: int
    heavy_dataset_resources: int
    heavy_dataset_slug: str
    skip_heavy_dataset: bool
    rating_users_count: int


def parse_args() -> SeedConfig:
    parser = argparse.ArgumentParser(
        description=(
            "Cria organizacoes, grupos, datasets e um dataset com muitos "
            "recursos para testes no CKAN."
        )
    )
    parser.add_argument(
        "--ckan-url",
        default=DEFAULT_CKAN_URL,
        help="URL base do CKAN. Padrao: %(default)s",
    )
    parser.add_argument(
        "--api-key",
        default=DEFAULT_API_KEY,
        help="API key ou token do CKAN. Padrao: variavel CKAN_API_KEY",
    )
    parser.add_argument(
        "--prefix",
        default="seed-artesp",
        help="Prefixo usado para organizacoes, grupos e datasets.",
    )
    parser.add_argument(
        "--owner-org",
        default=os.environ.get("CKAN_SEED_OWNER_ORG", ""),
        help=(
            "Organizacao fixa para todos os datasets. Use quando o ambiente "
            "restringe criacao a uma unica organizacao, como a ARTESP. "
            "Padrao: variavel CKAN_SEED_OWNER_ORG"
        ),
    )
    parser.add_argument(
        "--organization-count",
        type=int,
        default=3,
        help="Quantidade de organizacoes de teste.",
    )
    parser.add_argument(
        "--group-count",
        type=int,
        default=3,
        help="Quantidade de grupos de teste.",
    )
    parser.add_argument(
        "--dataset-count",
        type=int,
        default=12,
        help="Quantidade de datasets regulares de teste.",
    )
    parser.add_argument(
        "--resources-per-dataset",
        type=int,
        default=8,
        help="Quantidade de recursos por dataset regular.",
    )
    parser.add_argument(
        "--heavy-dataset-resources",
        type=int,
        default=120,
        help="Quantidade de recursos no dataset pesado.",
    )
    parser.add_argument(
        "--heavy-dataset-slug",
        default="dataset-muitos-recursos",
        help="Sufixo do slug do dataset pesado.",
    )
    parser.add_argument(
        "--skip-heavy-dataset",
        action="store_true",
        help="Nao cria o dataset pesado com muitos recursos.",
    )
    parser.add_argument(
        "--rating-users-count",
        type=int,
        default=3,
        help="Quantidade de usuarios de teste que avaliam cada dataset. 0 para nao criar ratings.",
    )

    args = parser.parse_args()

    if not args.api_key:
        parser.error(
            "API key nao informada. Use --api-key ou defina CKAN_API_KEY."
        )

    numeric_fields = {
        "organization-count": args.organization_count,
        "group-count": args.group_count,
        "dataset-count": args.dataset_count,
        "resources-per-dataset": args.resources_per_dataset,
        "heavy-dataset-resources": args.heavy_dataset_resources,
    }
    invalid_fields = [name for name, value in numeric_fields.items() if value < 0]
    if invalid_fields:
        parser.error(
            "Todos os contadores devem ser maiores ou iguais a zero: "
            + ", ".join(invalid_fields)
        )
    owner_org = slugify(args.owner_org) if args.owner_org else None

    if args.dataset_count > 0 and args.organization_count == 0 and not owner_org:
        parser.error(
            "--organization-count deve ser maior que zero quando "
            "--dataset-count for maior que zero, exceto quando --owner-org "
            "for informado."
        )
    if args.dataset_count > 0 and args.group_count == 0:
        parser.error(
            "--group-count deve ser maior que zero quando --dataset-count "
            "for maior que zero."
        )
    if not args.skip_heavy_dataset and args.heavy_dataset_resources > 0:
        if args.organization_count == 0 and not owner_org:
            parser.error(
                "--organization-count deve ser maior que zero para criar o "
                "dataset pesado, exceto quando --owner-org for informado."
            )
        if args.group_count == 0:
            parser.error(
                "--group-count deve ser maior que zero para criar o dataset "
                "pesado."
            )

    return SeedConfig(
        ckan_url=args.ckan_url.rstrip("/"),
        api_key=args.api_key,
        prefix=slugify(args.prefix),
        owner_org=owner_org,
        organization_count=args.organization_count,
        group_count=args.group_count,
        dataset_count=args.dataset_count,
        resources_per_dataset=args.resources_per_dataset,
        heavy_dataset_resources=args.heavy_dataset_resources,
        heavy_dataset_slug=slugify(args.heavy_dataset_slug),
        skip_heavy_dataset=args.skip_heavy_dataset,
        rating_users_count=max(0, args.rating_users_count),
    )


def slugify(value: str) -> str:
    normalized = []
    previous_was_dash = False

    for char in value.lower():
        if char.isalnum():
            normalized.append(char)
            previous_was_dash = False
            continue

        if previous_was_dash:
            continue

        normalized.append("-")
        previous_was_dash = True

    slug = "".join(normalized).strip("-")
    if not slug:
        raise ValueError("Nao foi possivel gerar um slug valido.")
    return slug


def ensure_organization(
    ckan: ckanapi.RemoteCKAN,
    organization_name: str,
    title: str,
) -> None:
    try:
        ckan.action.organization_show(id=organization_name)
        print(f"Organizacao existente: {organization_name}")
        return
    except errors.NotFound:
        pass

    ckan.action.organization_create(
        name=organization_name,
        title=title,
        description=f"Organizacao de teste {title}.",
    )
    print(f"Organizacao criada: {organization_name}")


def require_existing_organization(
    ckan: ckanapi.RemoteCKAN,
    organization_name: str,
) -> None:
    try:
        ckan.action.organization_show(id=organization_name)
    except errors.NotFound as exc:
        raise SystemExit(
            f"Organizacao obrigatoria nao encontrada: {organization_name}"
        ) from exc


def ensure_group(
    ckan: ckanapi.RemoteCKAN,
    group_name: str,
    title: str,
) -> None:
    try:
        ckan.action.group_show(id=group_name)
        print(f"Grupo existente: {group_name}")
        return
    except errors.NotFound:
        pass

    ckan.action.group_create(
        name=group_name,
        title=title,
        description=f"Grupo de teste {title}.",
    )
    print(f"Grupo criado: {group_name}")


def build_dataset_payload(
    config: SeedConfig,
    dataset_index: int,
    organization_name: str,
    group_name: str,
) -> dict:
    name = f"{config.prefix}-dataset-{dataset_index:03d}"
    return {
        "name": name,
        "title": f"Dataset de teste {dataset_index:03d}",
        "notes": (
            "Dataset de teste gerado automaticamente para validar "
            "listagens, busca e renderizacao de recursos."
        ),
        "owner_org": organization_name,
        "groups": [{"name": group_name}],
        "tag_string": f"teste {config.prefix} dataset-{dataset_index:03d}",
        "license_id": "cc-by",
        "source_url": (
            f"https://example.com/{config.prefix}/dataset/{dataset_index:03d}"
        ),
        "version": f"2026.{dataset_index:03d}",
        "author": "Equipe ARTESP",
        "author_email": "dados@example.com",
        "maintainer": "Equipe ARTESP",
        "maintainer_email": "dados@example.com",
        "periodicidade": periodicidade_for_index(dataset_index),
        "atualizacaoVersao": "False",
        "descontinuado": "False",
        "dadosRacaEtnia": "False",
        "dadosGenero": "True" if dataset_index % 2 else "False",
        "dadosIdade": "True" if dataset_index % 3 == 0 else "False",
        "featuredDataset": False,
    }


def build_heavy_dataset_payload(
    config: SeedConfig,
    organization_name: str,
    group_name: str,
) -> dict:
    name = f"{config.prefix}-{config.heavy_dataset_slug}"
    return {
        "name": name,
        "title": "Dataset de teste com muitos recursos",
        "notes": (
            "Dataset de teste volumoso para validar comportamento de paginas "
            "com listagens extensas de recursos."
        ),
        "owner_org": organization_name,
        "groups": [{"name": group_name}],
        "tag_string": f"teste {config.prefix} muitos-recursos",
        "license_id": "cc-by",
        "source_url": f"https://example.com/{config.prefix}/dataset/muitos-recursos",
        "version": "2026.heavy",
        "author": "Equipe ARTESP",
        "author_email": "dados@example.com",
        "maintainer": "Equipe ARTESP",
        "maintainer_email": "dados@example.com",
        "periodicidade": "MENSAL",
        "atualizacaoVersao": "True",
        "descontinuado": "False",
        "dadosRacaEtnia": "False",
        "dadosGenero": "False",
        "dadosIdade": "False",
        "featuredDataset": False,
    }


def periodicidade_for_index(dataset_index: int) -> str:
    choices = [
        "DIARIA",
        "SEMANAL",
        "QUINZENAL",
        "MENSAL",
        "TRIMESTRAL",
        "SEMESTRAL",
        "ANUAL",
        "SOB_DEMANDA",
    ]
    return choices[dataset_index % len(choices)]


def build_resource_payload(
    dataset_name: str,
    resource_index: int,
) -> dict:
    format_name, extension = resource_format_for_index(resource_index)
    resource_name = f"Recurso {resource_index:03d} - {format_name}"
    return {
        "name": resource_name,
        "description": (
            f"Recurso de teste {resource_index:03d} do dataset {dataset_name}."
        ),
        "format": format_name,
        "url": (
            "https://example.com/resource?"
            f"dataset={dataset_name}&resource={resource_index:03d}&ext={extension}"
        ),
    }


def resource_format_for_index(resource_index: int) -> tuple[str, str]:
    formats = [
        ("CSV", "csv"),
        ("PDF", "pdf"),
        ("JSON", "json"),
        ("XML", "xml"),
        ("ZIP", "zip"),
        ("TXT", "txt"),
        ("HTML", "html"),
        ("XLSX", "xlsx"),
    ]
    return formats[resource_index % len(formats)]


def ensure_dataset(ckan: ckanapi.RemoteCKAN, payload: dict) -> dict:
    try:
        dataset = ckan.action.package_show(id=payload["name"])
        print(f"Dataset existente: {payload['name']}")
        return dataset
    except errors.NotFound:
        dataset = ckan.action.package_create(**payload)
        print(f"Dataset criado: {payload['name']}")
        return dataset


def ensure_resources(
    ckan: ckanapi.RemoteCKAN,
    package_id: str,
    package_name: str,
    desired_count: int,
) -> int:
    package = ckan.action.package_show(id=package_id)
    existing_resource_names = {resource["name"] for resource in package["resources"]}
    created_count = 0

    for resource_index in range(desired_count):
        payload = build_resource_payload(package_name, resource_index)
        if payload["name"] in existing_resource_names:
            continue

        ckan.action.resource_create(package_id=package_id, **payload)
        existing_resource_names.add(payload["name"])
        created_count += 1
        print(
            "  Recurso criado: "
            f"{package_name} -> {payload['name']}"
        )

    return created_count


def make_organization_names(config: SeedConfig) -> list[str]:
    return [
        f"{config.prefix}-org-{index + 1:02d}"
        for index in range(config.organization_count)
    ]


def make_group_names(config: SeedConfig) -> list[str]:
    return [
        f"{config.prefix}-grupo-{index + 1:02d}"
        for index in range(config.group_count)
    ]


def cycle_pick(values: list[str], index: int) -> str:
    if not values:
        raise ValueError("A lista de valores nao pode ser vazia.")
    return values[index % len(values)]


def seed_regular_datasets(
    ckan: ckanapi.RemoteCKAN,
    config: SeedConfig,
    organizations: list[str],
    groups: list[str],
) -> tuple[int, int, list[dict]]:
    dataset_count = 0
    resource_count = 0
    datasets = []

    for dataset_index in range(config.dataset_count):
        organization_name = cycle_pick(organizations, dataset_index)
        group_name = cycle_pick(groups, dataset_index)
        payload = build_dataset_payload(
            config=config,
            dataset_index=dataset_index,
            organization_name=organization_name,
            group_name=group_name,
        )
        dataset = ensure_dataset(ckan, payload)
        datasets.append(dataset)
        dataset_count += 1
        resource_count += ensure_resources(
            ckan=ckan,
            package_id=dataset["id"],
            package_name=payload["name"],
            desired_count=config.resources_per_dataset,
        )

    return dataset_count, resource_count, datasets


def seed_heavy_dataset(
    ckan: ckanapi.RemoteCKAN,
    config: SeedConfig,
    organization_name: str,
    group_name: str,
) -> tuple[int, int, list[dict]]:
    if config.skip_heavy_dataset:
        return 0, 0, []

    payload = build_heavy_dataset_payload(
        config=config,
        organization_name=organization_name,
        group_name=group_name,
    )
    dataset = ensure_dataset(ckan, payload)
    resource_count = ensure_resources(
        ckan=ckan,
        package_id=dataset["id"],
        package_name=payload["name"],
        desired_count=config.heavy_dataset_resources,
    )
    return 1, resource_count, [dataset]


_RATING_OVERALL = [5, 4, 3, 4, 2, 5, 3, 1, 4, 5]
_RATING_CRITERIA = [
    {"links_work": True,  "up_to_date": True,  "well_structured": True},
    {"links_work": True,  "up_to_date": False, "well_structured": True},
    {"links_work": False, "up_to_date": True,  "well_structured": False},
    {"links_work": True,  "up_to_date": True},
    {},
]
_RATING_COMMENTS = [
    "Dados muito úteis para análise de tráfego.",
    "Boa organização, mas os links poderiam ser mais estáveis.",
    "",
    "Excelente conjunto de dados, bem estruturado.",
    "",
    "Informações atualizadas e fáceis de usar.",
    "",
]


def ensure_rating_user(
    ckan: ckanapi.RemoteCKAN,
    username: str,
    email: str,
) -> dict:
    try:
        user = ckan.action.user_show(id=username)
        print(f"Usuário de rating existente: {username}")
        return user
    except errors.NotFound:
        pass
    user = ckan.action.user_create(
        name=username,
        email=email,
        password="SeedPassword123!",
        fullname=f"Avaliador Seed {username}",
    )
    print(f"Usuário de rating criado: {username}")
    return user


def seed_rating_users(
    ckan: ckanapi.RemoteCKAN,
    config: SeedConfig,
) -> list[dict]:
    users = []
    for i in range(config.rating_users_count):
        username = f"{config.prefix}-rater-{i + 1:02d}"
        email = f"{config.prefix}-rater-{i + 1:02d}@seed.example.com"
        user = ensure_rating_user(ckan, username, email)
        users.append({"id": user["id"], "name": username})
    return users


def seed_ratings(
    datasets: list[dict],
    rating_users: list[dict],
) -> int:
    db_url = os.environ.get("CKAN_SQLALCHEMY_URL", "")
    if not db_url:
        print("  AVISO: CKAN_SQLALCHEMY_URL nao definido — ratings nao inseridos.")
        return 0

    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        print("  AVISO: sqlalchemy nao disponivel — ratings nao inseridos.")
        return 0

    engine = create_engine(db_url)
    now = datetime.datetime.utcnow()
    count = 0

    with engine.begin() as conn:
        for ds_index, dataset in enumerate(datasets):
            pkg_id = dataset.get("id")
            if not pkg_id:
                continue
            for user_index, user in enumerate(rating_users):
                user_id = user["id"]
                existing = conn.execute(
                    text(
                        "SELECT id FROM dataset_rating"
                        " WHERE user_id = :uid AND package_id = :pid"
                    ),
                    {"uid": user_id, "pid": pkg_id},
                ).first()
                if existing:
                    continue

                slot = (ds_index * len(rating_users) + user_index)
                overall_rating = _RATING_OVERALL[slot % len(_RATING_OVERALL)]
                criteria = _RATING_CRITERIA[slot % len(_RATING_CRITERIA)]
                comment = _RATING_COMMENTS[slot % len(_RATING_COMMENTS)]

                conn.execute(
                    text(
                        "INSERT INTO dataset_rating"
                        " (id, user_id, package_id, overall_rating, criteria, comment, created_at, updated_at)"
                        " VALUES (:id, :uid, :pid, :rating, :criteria, :comment, :now, :now)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "uid": user_id,
                        "pid": pkg_id,
                        "rating": overall_rating,
                        "criteria": json.dumps(criteria),
                        "comment": comment,
                        "now": now,
                    },
                )
                count += 1
                print(
                    f"  Rating criado: {dataset.get('name')} <- {user['name']}"
                    f" (nota {overall_rating})"
                )

    return count


def print_summary(
    organizations: Iterable[str],
    groups: Iterable[str],
    regular_dataset_count: int,
    regular_resources_created: int,
    heavy_dataset_count: int,
    heavy_resources_created: int,
    ratings_created: int = 0,
) -> None:
    print("")
    print("Resumo da carga:")
    print(f"  Organizacoes preparadas: {len(list(organizations))}")
    print(f"  Grupos preparados: {len(list(groups))}")
    print(f"  Datasets regulares processados: {regular_dataset_count}")
    print(f"  Recursos regulares criados agora: {regular_resources_created}")
    print(f"  Datasets pesados processados: {heavy_dataset_count}")
    print(f"  Recursos do dataset pesado criados agora: {heavy_resources_created}")
    print(f"  Ratings criados agora: {ratings_created}")


def seed_data(config: SeedConfig) -> None:
    ckan = ckanapi.RemoteCKAN(config.ckan_url, apikey=config.api_key)

    print(f"Conectando ao CKAN em {config.ckan_url}...")

    organizations = make_organization_names(config)
    groups = make_group_names(config)

    if config.owner_org:
        require_existing_organization(ckan, config.owner_org)

    for index, organization_name in enumerate(organizations, start=1):
        ensure_organization(
            ckan=ckan,
            organization_name=organization_name,
            title=f"Organizacao de teste {index:02d}",
        )

    for index, group_name in enumerate(groups, start=1):
        ensure_group(
            ckan=ckan,
            group_name=group_name,
            title=f"Grupo de teste {index:02d}",
        )

    dataset_organizations = (
        [config.owner_org]
        if config.owner_org
        else organizations
    )

    regular_dataset_count, regular_resources_created, regular_datasets = seed_regular_datasets(
        ckan=ckan,
        config=config,
        organizations=dataset_organizations,
        groups=groups,
    )

    heavy_dataset_count, heavy_resources_created, heavy_datasets = seed_heavy_dataset(
        ckan=ckan,
        config=config,
        organization_name=cycle_pick(dataset_organizations, 0),
        group_name=cycle_pick(groups, 0),
    )

    ratings_created = 0
    if config.rating_users_count > 0:
        print("\nCriando usuários e ratings de teste...")
        all_datasets = regular_datasets + heavy_datasets
        rating_users = seed_rating_users(ckan=ckan, config=config)
        ratings_created = seed_ratings(datasets=all_datasets, rating_users=rating_users)

    print_summary(
        organizations=organizations,
        groups=groups,
        regular_dataset_count=regular_dataset_count,
        regular_resources_created=regular_resources_created,
        heavy_dataset_count=heavy_dataset_count,
        heavy_resources_created=heavy_resources_created,
        ratings_created=ratings_created,
    )


if __name__ == "__main__":
    seed_data(parse_args())
