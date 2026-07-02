from dataclasses import dataclass
from math import ceil
import unicodedata

from flask import g, has_request_context, request

from ckan.lib.pagination import Page
import ckan.plugins.toolkit as toolkit


RESOURCE_PAGE_SIZE = 20
DATASET_READ_ENDPOINTS = {"dataset.read", "dcat.read_dataset"}


class ResourcePageNotFound(ValueError):
    pass


@dataclass(frozen=True)
class ResourcePage:
    resources: list[dict]
    page: int
    page_count: int
    page_size: int
    total: int
    filtered_total: int
    query: str


def _normalize(value):
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return without_accents.casefold()


def _parse_page(raw_page):
    try:
        page = int(raw_page or 1)
    except (TypeError, ValueError) as error:
        raise ResourcePageNotFound from error
    if page < 1:
        raise ResourcePageNotFound
    return page


def build_resource_page(resources, raw_page, query, page_size=RESOURCE_PAGE_SIZE):
    all_resources = list(resources or [])
    clean_query = str(query or "").strip()
    normalized_query = _normalize(clean_query)

    if normalized_query:
        filtered = [
            resource
            for resource in all_resources
            if normalized_query
            in _normalize(
                "{} {}".format(
                    resource.get("name", ""),
                    resource.get("description", ""),
                )
            )
        ]
    else:
        filtered = all_resources

    page = _parse_page(raw_page)
    page_count = max(1, ceil(len(filtered) / page_size))
    if page > page_count:
        raise ResourcePageNotFound

    start = (page - 1) * page_size
    return ResourcePage(
        resources=filtered[start:start + page_size],
        page=page,
        page_count=page_count,
        page_size=page_size,
        total=len(all_resources),
        filtered_total=len(filtered),
        query=clean_query,
    )


def _is_dataset_read_request():
    return has_request_context() and request.endpoint in DATASET_READ_ENDPOINTS


def paginate_dataset_view(package_dict):
    if not _is_dataset_read_request():
        return package_dict

    all_resources = list(package_dict.get("resources", []))
    try:
        resource_page = build_resource_page(
            all_resources,
            raw_page=request.args.get("resource_page", "1"),
            query=request.args.get("resource_q", ""),
        )
    except ResourcePageNotFound:
        toolkit.abort(404)

    def pager_url(**kwargs):
        page = kwargs.get("page", 1)
        params = {}
        if resource_page.query:
            params["resource_q"] = resource_page.query
        if page and int(page) > 1:
            params["resource_page"] = page
        return toolkit.url_for(
            "dataset.read", id=package_dict.get("name"), **params
        )

    g.artesp_full_dataset_resources = all_resources
    g.artesp_dataset_resource_page = resource_page
    g.artesp_dataset_resource_pagination = Page(
        collection=resource_page.resources,
        page=resource_page.page,
        items_per_page=resource_page.page_size,
        item_count=resource_page.filtered_total,
        presliced_list=True,
        url=pager_url,
    )
    package_dict["resources"] = resource_page.resources
    return package_dict


def get_resource_page():
    if not has_request_context():
        return None
    return getattr(g, "artesp_dataset_resource_page", None)


def get_resource_pagination():
    if not has_request_context():
        return None
    return getattr(g, "artesp_dataset_resource_pagination", None)


def get_full_resources(package_dict):
    if has_request_context():
        resources = getattr(g, "artesp_full_dataset_resources", None)
        if resources is not None:
            return resources
    return package_dict.get("resources", [])
