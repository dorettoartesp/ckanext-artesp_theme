import ckan.plugins.toolkit as tk


def artesp_theme_required(value):
    if not value or value is tk.missing:
        raise tk.Invalid(tk._("Required"))
    return value


def get_validators():
    return {
        "artesp_theme_required": artesp_theme_required,
    }
