"""Flask-DebugToolbar SQLAlchemy integration for CKAN development.

Hooks into CKAN's SQLAlchemy engine so queries appear in the DebugToolbar
SQLAlchemy panel. Only activated when the Flask app is in debug mode.
"""
import logging

log = logging.getLogger(__name__)


def install(engine, app):
    """Hook flask-sqlalchemy query recording onto CKAN's engine.

    Uses flask_sqlalchemy.record_queries._listen so query objects land in
    g._sqlalchemy_queries in exactly the format the DebugToolbar expects.
    Registers a dummy Flask-SQLAlchemy extension so extension_used() returns
    True, which tells the panel it is available.
    """
    try:
        from flask_sqlalchemy import SQLAlchemy
        from flask_sqlalchemy.record_queries import _listen
    except ImportError:
        log.debug("flask-sqlalchemy not installed; SQLAlchemy debug panel disabled")
        return

    # Dummy URI so Flask-SQLAlchemy initialises cleanly without creating a
    # real PostgreSQL pool (we never query through this instance).
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    app.config.setdefault("SQLALCHEMY_RECORD_QUERIES", True)

    # ProfilerDebugPanel.__init__ only sets dump_filename when this key is
    # boolean True — ckan.ini delivers it as the string "True" which fails the
    # check, leaving dump_filename uninitialised and crashing on activation.
    app.config["DEBUG_TB_PROFILER_ENABLED"] = True

    db = SQLAlchemy()
    db.init_app(app)

    # Hook CKAN's real engine — not the dummy sqlite one created above.
    _listen(engine)
    log.debug("Flask-DebugToolbar: SQLAlchemy query recording active on CKAN engine")
