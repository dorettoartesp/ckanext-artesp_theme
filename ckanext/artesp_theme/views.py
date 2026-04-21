import logging

from flask import Blueprint, redirect, request, url_for

import ckan.plugins.toolkit as tk
from ckan.common import config
from ckan.lib import captcha

log = logging.getLogger(__name__)

artesp_theme = Blueprint("artesp_theme", __name__)


def page():
    return "Hello, artesp_theme!"


artesp_theme.add_url_rule("/artesp_theme/page", view_func=page)


def _check_captcha_fail_closed():
    """Validate reCAPTCHA. Raises ValidationError if key absent or token invalid."""
    if not config.get("ckan.recaptcha.privatekey"):
        raise tk.ValidationError({"captcha": [tk._("Captcha not configured")]})
    captcha.check_recaptcha(request)


def rating_submit(package_name: str):
    if not tk.current_user.is_authenticated:
        return redirect(url_for("user.login"))

    try:
        _check_captcha_fail_closed()
    except tk.ValidationError:
        tk.h.flash_error(tk._("Captcha validation failed. Please try again."))
        return redirect(url_for("dataset.read", id=package_name))

    criteria = {}
    from ckanext.artesp_theme.logic.rating import RATING_CRITERIA
    for key in RATING_CRITERIA:
        raw = request.form.get(f"criteria_{key}", "").strip().lower()
        if raw:
            criteria[key] = raw in ("true", "1", "yes")

    try:
        tk.get_action("dataset_rating_upsert")(
            {"user": tk.current_user.name},
            {
                "package_id": tk.get_action("package_show")(
                    {"ignore_auth": True}, {"id": package_name}
                )["id"],
                "overall_rating": request.form.get("overall_rating"),
                "criteria": criteria,
                "comment": request.form.get("comment", ""),
            },
        )
        tk.h.flash_success(tk._("Your rating was submitted successfully."))
    except tk.ValidationError as exc:
        errors = "; ".join(
            v[0] if isinstance(v, list) else str(v)
            for v in exc.error_dict.values()
        )
        tk.h.flash_error(tk._("Invalid rating: {errors}").format(errors=errors))
    except tk.NotAuthorized:
        tk.h.flash_error(tk._("You are not authorized to rate this dataset."))

    return redirect(url_for("dataset.read", id=package_name))


artesp_theme.add_url_rule(
    "/dataset/<package_name>/rate",
    view_func=rating_submit,
    methods=["POST"],
)


def get_blueprints():
    return [artesp_theme]
