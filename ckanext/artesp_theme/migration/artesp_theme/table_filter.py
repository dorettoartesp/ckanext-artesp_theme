"""Helpers for keeping Alembic scoped to extension-owned tables."""


def include_extension_table(object_name, type_):
    if type_ != "table":
        return True

    return object_name.startswith("dataset_rating") or object_name in {
        "rating_action",
        "audit_event",
    }
