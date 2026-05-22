"""App extensions."""

from __future__ import annotations

from flask import request
from flask_mysqldb import MySQL
from flask.sessions import SecureCookieSessionInterface


class MobileSessionInterface(SecureCookieSessionInterface):
    """Session interface that uses a different cookie name for mobile clients."""

    def get_cookie_name(self, app):
        if request.headers.get("X-Client") == "mobile":
            return "hazardhub_mobile"
        return app.config.get("SESSION_COOKIE_NAME", "session")


mysql = MySQL()


def init_extensions(app):
    app.session_interface = MobileSessionInterface()
    mysql.init_app(app)
