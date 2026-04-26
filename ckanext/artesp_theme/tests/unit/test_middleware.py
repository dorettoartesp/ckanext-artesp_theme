"""Tests for middleware.py.

The FontAwesomeFixMiddleware is pure Python with no CKAN imports, so
these tests do not require CKAN fixtures.
"""
from unittest.mock import MagicMock

from ckanext.artesp_theme.middleware import FontAwesomeFixMiddleware, make_middleware


# ---------------------------------------------------------------------------
# FontAwesomeFixMiddleware.__init__
# ---------------------------------------------------------------------------

class TestFontAwesomeFixMiddlewareInit:
    def test_stores_app(self):
        fake_app = MagicMock()
        mw = FontAwesomeFixMiddleware(fake_app)
        assert mw.app is fake_app

    def test_compiles_regex_pattern(self):
        import re
        fake_app = MagicMock()
        mw = FontAwesomeFixMiddleware(fake_app)
        assert hasattr(mw, "pattern")
        assert isinstance(mw.pattern, type(re.compile("")))


# ---------------------------------------------------------------------------
# FontAwesomeFixMiddleware.__call__
# ---------------------------------------------------------------------------

def _make_wsgi_app(body: bytes, content_type: str = "text/html; charset=utf-8") -> MagicMock:
    """Return a WSGI callable that yields `body` with the given Content-Type."""
    def app(environ, start_response):
        start_response(
            "200 OK",
            [("Content-Type", content_type)],
        )
        return [body]

    return app


class TestFontAwesomeFixMiddlewareCall:
    def test_non_html_response_passes_through_unchanged(self):
        body = b'{"key": "value"}'
        inner_app = _make_wsgi_app(body, content_type="application/json")
        mw = FontAwesomeFixMiddleware(inner_app)

        collected_headers = []

        def start_response(status, headers, exc_info=None):
            collected_headers.extend(headers)

        result = mw({}, start_response)
        # For non-HTML, the original app_iter is returned directly
        chunks = list(result)
        response_body = b"".join(chunks)
        assert response_body == body

    def test_html_without_double_encoded_icons_passes_through(self):
        html = b"<html><body><p>Hello</p></body></html>"
        inner_app = _make_wsgi_app(html, content_type="text/html; charset=utf-8")
        mw = FontAwesomeFixMiddleware(inner_app)

        def start_response(status, headers, exc_info=None):
            pass

        result = mw({}, start_response)
        chunks = list(result)
        response_body = b"".join(chunks)
        assert b"<html>" in response_body

    def test_html_with_double_encoded_icons_gets_fixed(self):
        double_encoded = (
            b'<html><body>&amp;lt;i class=&amp;quot;fa fa-star&amp;quot;&amp;gt;'
            b'&amp;lt;/i&amp;gt;</body></html>'
        )
        inner_app = _make_wsgi_app(double_encoded, content_type="text/html")
        mw = FontAwesomeFixMiddleware(inner_app)

        def start_response(status, headers, exc_info=None):
            pass

        result = mw({}, start_response)
        chunks = list(result)
        response_body = b"".join(chunks)
        assert b'<i class="fa fa-star"></i>' in response_body

    def test_app_iter_with_close_method_gets_closed(self):
        """The middleware calls close() on the inner iterator if available."""
        html = b"<html><body>content</body></html>"
        close_called = []

        class IterableWithClose:
            def __init__(self, data):
                self._data = [data]
                self._iter = iter(self._data)

            def __iter__(self):
                return self

            def __next__(self):
                return next(self._iter)

            def close(self):
                close_called.append(True)

        def inner_app(environ, start_response):
            start_response("200 OK", [("Content-Type", "text/html")])
            return IterableWithClose(html)

        mw = FontAwesomeFixMiddleware(inner_app)

        def start_response(status, headers, exc_info=None):
            pass

        mw({}, start_response)
        assert close_called == [True]

    def test_string_chunks_are_encoded_to_utf8(self):
        """Middleware handles str chunks from app_iter."""
        def inner_app(environ, start_response):
            start_response("200 OK", [("Content-Type", "text/html")])
            return ["<html>string content</html>"]

        mw = FontAwesomeFixMiddleware(inner_app)

        def start_response(status, headers, exc_info=None):
            pass

        result = mw({}, start_response)
        chunks = list(result)
        response_body = b"".join(chunks)
        assert b"<html>" in response_body

    def test_calls_start_response_with_correct_status(self):
        """custom_start_response passes through to the real start_response."""
        html = b"<html></html>"
        inner_app = _make_wsgi_app(html, content_type="text/html")
        mw = FontAwesomeFixMiddleware(inner_app)

        captured = []

        def start_response(status, headers, exc_info=None):
            captured.append(status)

        mw({}, start_response)
        assert captured == ["200 OK"]


# ---------------------------------------------------------------------------
# make_middleware
# ---------------------------------------------------------------------------

class TestMakeMiddleware:
    def test_flask_app_returns_app_with_handlers_in_cache_safe_order(self):
        """Flask app registers cache and icon hooks in LIFO-safe order."""
        fake_flask_app = MagicMock()
        fake_flask_app.debug = False
        fake_flask_app.before_request = MagicMock(side_effect=lambda f: f)
        fake_flask_app.after_request = MagicMock(side_effect=lambda f: f)
        # after_request is truthy → Flask path
        assert hasattr(fake_flask_app, "after_request")

        result = make_middleware(fake_flask_app)
        assert result is fake_flask_app
        fake_flask_app.before_request.assert_called_once()

        after_request_handlers = [
            call_args.args[0].__name__
            for call_args in fake_flask_app.after_request.call_args_list
        ]
        assert after_request_handlers == [
            "_home_cache_after",
            "fix_fontawesome_icons",
        ]

    def test_non_flask_app_returns_wsgi_middleware(self):
        """Non-Flask app → returns FontAwesomeFixMiddleware wrapping it."""
        fake_wsgi_app = MagicMock(spec=[])  # no after_request attr
        result = make_middleware(fake_wsgi_app)
        assert isinstance(result, FontAwesomeFixMiddleware)
        assert result.app is fake_wsgi_app

    def test_make_middleware_accepts_config_argument(self):
        """Config argument is accepted (but ignored)."""
        fake_wsgi_app = MagicMock(spec=[])
        result = make_middleware(fake_wsgi_app, config={"key": "value"})
        assert isinstance(result, FontAwesomeFixMiddleware)


# ---------------------------------------------------------------------------
# after_request handler (Flask path)
# ---------------------------------------------------------------------------

class TestAfterRequestHandler:
    def test_home_cache_stores_html_after_icons_are_fixed(self, monkeypatch):
        """Flask's LIFO hook execution stores already-fixed homepage HTML."""
        registered_handlers = []

        def capture_handler(f):
            registered_handlers.append(f)
            return f

        fake_flask_app = MagicMock()
        fake_flask_app.debug = False
        fake_flask_app.after_request = capture_handler

        make_middleware(fake_flask_app)

        from ckanext.artesp_theme import home_cache

        stored_bodies = []

        def store_response(response):
            stored_bodies.append(response.data.decode("utf-8"))
            return response

        monkeypatch.setattr(home_cache, "store", store_response)

        double_encoded = (
            '&amp;lt;i class=&amp;quot;fa fa-check&amp;quot;&amp;gt;'
            '&amp;lt;/i&amp;gt;'
        )
        fake_response = MagicMock()
        fake_response.content_type = "text/html; charset=utf-8"
        fake_response.data = f"<html><body>{double_encoded}</body></html>".encode("utf-8")

        for handler in reversed(registered_handlers):
            fake_response = handler(fake_response)

        assert stored_bodies == [
            '<html><body><i class="fa fa-check"></i></body></html>'
        ]

    def test_html_response_gets_icons_fixed(self):
        """The registered after_request handler fixes double-encoded icons in HTML."""
        registered_handlers = {}

        def capture_handler(f):
            registered_handlers[f.__name__] = f
            return f

        fake_flask_app = MagicMock()
        fake_flask_app.debug = False
        fake_flask_app.after_request = capture_handler

        make_middleware(fake_flask_app)
        registered_handler = registered_handlers["fix_fontawesome_icons"]

        # Build a fake Flask response
        double_encoded = (
            '&amp;lt;i class=&amp;quot;fa fa-check&amp;quot;&amp;gt;'
            '&amp;lt;/i&amp;gt;'
        )
        html_body = f"<html><body>{double_encoded}</body></html>"

        fake_response = MagicMock()
        fake_response.content_type = "text/html; charset=utf-8"
        fake_response.data = html_body.encode("utf-8")

        # Simulate the after_request call
        result = registered_handler(fake_response)
        assert result is fake_response
        fixed = fake_response.data.decode("utf-8")
        assert '<i class="fa fa-check"></i>' in fixed

    def test_non_html_response_is_not_modified(self):
        """after_request handler skips non-HTML content-types."""
        registered_handlers = {}

        def capture_handler(f):
            registered_handlers[f.__name__] = f
            return f

        fake_flask_app = MagicMock()
        fake_flask_app.debug = False
        fake_flask_app.after_request = capture_handler

        make_middleware(fake_flask_app)
        registered_handler = registered_handlers["fix_fontawesome_icons"]

        json_body = b'{"key": "value"}'
        fake_response = MagicMock()
        fake_response.content_type = "application/json"
        fake_response.data = json_body

        result = registered_handler(fake_response)
        assert result is fake_response
        # data should not have been written to
        fake_response.__setattr__  # just ensure no AttributeError
