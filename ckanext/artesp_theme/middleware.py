import logging
import re
from markupsafe import Markup
from typing import Callable, Dict, Any, Optional

log = logging.getLogger(__name__)


def install_safe_error_mail_handler() -> None:
    """Patch CKAN's email error handler before Flask app construction.

    CKAN registers its email error handler before extension middleware runs.
    With ``email_to`` enabled, the stock ContextualFilter reads
    ``flask.request`` while the app is still starting, which can abort uWSGI
    worker startup outside a request context.
    """
    try:
        import ckan.config.middleware.flask_app as flask_app
        from flask import request as _request
    except Exception as exc:
        log.debug("artesp_theme: unable to patch CKAN error mail handler: %s", exc)
        return

    current_handler = getattr(flask_app, "_setup_error_mail_handler", None)
    if getattr(current_handler, "_artesp_request_safe", False):
        return

    def _setup_request_safe_error_mail_handler(app):
        class ContextualFilter(logging.Filter):
            def filter(self, log_record):  # type: ignore[override]
                try:
                    log_record.url = _request.path
                    log_record.method = _request.method
                    log_record.ip = _request.environ.get("REMOTE_ADDR")
                    log_record.headers = _request.headers
                except RuntimeError:
                    log_record.url = ""
                    log_record.method = ""
                    log_record.ip = ""
                    log_record.headers = ""
                return True

        config = flask_app.config
        smtp_server = config.get("smtp.server")
        mailhost = (
            tuple(smtp_server.split(":"))
            if smtp_server and ":" in smtp_server
            else smtp_server
        )
        credentials = None
        if config.get("smtp.user"):
            credentials = (
                config.get("smtp.user"),
                config.get("smtp.password"),
            )
        secure = () if config.get("smtp.starttls") else None
        mail_handler = flask_app.SMTPHandler(
            mailhost=mailhost,
            fromaddr=config.get("error_email_from"),
            toaddrs=[config.get("email_to")],
            subject="Application Error",
            credentials=credentials,
            secure=secure,
        )

        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(logging.Formatter("""
Time:               %(asctime)s
URL:                %(url)s
Method:             %(method)s
IP:                 %(ip)s
Headers:            %(headers)s

"""))

        app.logger.addFilter(ContextualFilter())
        app.logger.addHandler(mail_handler)

    _setup_request_safe_error_mail_handler._artesp_request_safe = True
    flask_app._setup_error_mail_handler = _setup_request_safe_error_mail_handler


class FontAwesomeFixMiddleware:
    """
    WSGI middleware to fix double-encoded Font Awesome icons in CKAN templates.

    This middleware intercepts the response and fixes any double-encoded
    Font Awesome icons in the HTML content.
    """

    def __init__(self, app: Callable) -> None:
        """
        Initialize the middleware.

        Args:
            app: The WSGI application
        """
        self.app = app

        # Regular expression to match double-encoded Font Awesome icons
        # This pattern matches strings like:
        # &amp;lt;i class=&amp;quot;fa fa-icon&amp;quot;&amp;gt;&amp;lt;/i&amp;gt;
        self.pattern = re.compile(
            r'&amp;lt;i\s+class=&amp;quot;fa\s+fa-([a-z0-9-]+)&amp;quot;&amp;gt;&amp;lt;/i&amp;gt;'
        )

    def __call__(self, environ: Dict[str, Any], start_response: Callable) -> Any:
        """
        Call the middleware.

        Args:
            environ: The WSGI environment
            start_response: The WSGI start_response function

        Returns:
            The response from the application
        """
        # Initialize headers to avoid AttributeError
        self.headers = []
        self.status = '200 OK'
        self.exc_info = None

        # Create a response interceptor
        def custom_start_response(status, headers, exc_info=None):
            self.status = status
            self.headers = headers
            self.exc_info = exc_info
            return start_response(status, headers, exc_info)

        # Get the response from the application
        app_iter = self.app(environ, custom_start_response)

        # Check if the response is HTML
        is_html = False
        for name, value in self.headers:
            if name.lower() == 'content-type' and 'text/html' in value.lower():
                is_html = True
                break

        # If not HTML, return the response as is
        if not is_html:
            return app_iter

        # Collect the response body
        response_body = b''
        for chunk in app_iter:
            if isinstance(chunk, str):
                response_body += chunk.encode('utf-8')
            else:
                response_body += chunk

        # Close the app_iter if it has a close method
        if hasattr(app_iter, 'close'):
            app_iter.close()

        # Fix double-encoded Font Awesome icons
        response_text = response_body.decode('utf-8')

        def replace_icon(match):
            icon_name = match.group(1)
            return f'<i class="fa fa-{icon_name}"></i>'

        fixed_response = self.pattern.sub(replace_icon, response_text)

        # Return the fixed response
        return [fixed_response.encode('utf-8')]


def _fix_contextual_filter(app: Callable) -> None:
    """Replace CKAN's ContextualFilter with a request-context-safe version.

    CKAN installs a ContextualFilter on app.logger when email_to is configured.
    That filter accesses request.path unconditionally, which raises RuntimeError
    during app startup (outside a request context) and prevents the app from
    loading. We swap it out for a version that guards the access.
    """
    import logging as _logging
    from flask import request as _request

    class _SafeContextualFilter(_logging.Filter):
        def filter(self, log_record):  # type: ignore[override]
            try:
                log_record.url = _request.path
                log_record.method = _request.method
                log_record.ip = _request.environ.get("REMOTE_ADDR")
                log_record.headers = _request.headers
            except RuntimeError:
                log_record.url = ""
                log_record.method = ""
                log_record.ip = ""
                log_record.headers = ""
            return True

    logger = getattr(app, "logger", None)
    if logger is None:
        return
    for f in list(logger.filters):
        if type(f).__name__ == "ContextualFilter":
            logger.removeFilter(f)
            logger.addFilter(_SafeContextualFilter())
            log.debug("artesp_theme: replaced ContextualFilter with safe version")
            break


def make_middleware(app: Callable, config: Optional[Dict[str, Any]] = None) -> Callable:
    """
    Factory function to create the middleware.

    Args:
        app: The WSGI application
        config: The configuration dictionary (not used)

    Returns:
        The middleware
    """
    # Check if the app is a Flask app
    if hasattr(app, 'after_request'):
        # Flask executes after_request hooks in LIFO order, so register
        # _home_cache_after first so it runs AFTER fix_fontawesome_icons,
        # ensuring the cached HTML is already icon-fixed.
        from ckanext.artesp_theme import home_cache

        @app.before_request
        def _home_cache_before():
            return home_cache.get()

        @app.after_request
        def _home_cache_after(response):
            return home_cache.store(response)

        @app.after_request
        def fix_fontawesome_icons(response):
            if response.content_type and 'text/html' in response.content_type.lower():
                pattern = re.compile(
                    r'&amp;lt;i\s+class=&amp;quot;fa\s+fa-([a-z0-9-]+)&amp;quot;&amp;gt;&amp;lt;/i&amp;gt;'
                )

                def replace_icon(match):
                    icon_name = match.group(1)
                    return f'<i class="fa fa-{icon_name}"></i>'

                response.data = pattern.sub(replace_icon, response.data.decode('utf-8')).encode('utf-8')
            return response

        _fix_contextual_filter(app)

        if app.debug:
            try:
                from ckan.model.meta import engine
                from ckanext.artesp_theme.dev_toolbar import install as _install_dev_toolbar
                _install_dev_toolbar(engine, app)
            except Exception as exc:
                log.debug("dev_toolbar init failed: %s", exc)

        # Return the Flask app with the after_request handler
        return app
    else:
        # If it's not a Flask app, use our WSGI middleware
        return FontAwesomeFixMiddleware(app)
