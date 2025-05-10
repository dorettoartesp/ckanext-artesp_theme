from flask import Blueprint


artesp_theme = Blueprint(
    "artesp_theme", __name__)


def page():
    return "Hello, artesp_theme!"


artesp_theme.add_url_rule(
    "/artesp_theme/page", view_func=page)


def get_blueprints():
    return [artesp_theme]
