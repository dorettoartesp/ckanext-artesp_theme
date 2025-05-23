from flask import Blueprint, render_template, request, g
from ckan.plugins import toolkit
from ckan.lib.helpers import flash_error, redirect_to

artesp_theme = Blueprint('artesp_theme', __name__)


def about_ckan():
    return render_template('static/about_ckan.html')


def terms():
    return render_template('static/terms.html')


def privacy():
    return render_template('static/privacy.html')


def contact():
    return render_template('static/contact.html')


def harvesting():
    return render_template('static/harvesting.html')


artesp_theme.add_url_rule('/about-ckan', view_func=about_ckan)
artesp_theme.add_url_rule('/terms', view_func=terms)
artesp_theme.add_url_rule('/privacy', view_func=privacy)
artesp_theme.add_url_rule('/contact', view_func=contact)
artesp_theme.add_url_rule('/harvesting', view_func=harvesting)

@artesp_theme.before_app_request
def restrict_stats_page_access():
    """
    Restricts access to the /stats page to authenticated users.
    """
    if request.path == '/stats':
        if not g.user:  # g.user is the username, empty for anonymous
            flash_error(toolkit._('You must be logged in to access the statistics page.'))
            return redirect_to(toolkit.url_for('user.login'))
    return None # Continue processing the request
