"""
Application entry point: Application Factory Pattern.

Creates the Flask instance via create_app() for testing, multi-env deployment,
and extension registration.
"""

import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from flask_jwt_extended.exceptions import (
    InvalidHeaderError,
    JWTDecodeError,
    NoAuthorizationError,
)
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from werkzeug.exceptions import HTTPException

from db import db
from extensions import api, jwt
from resources import register_blueprints

load_dotenv()


def create_app(test_config=None):
    """
    Application factory: create and configure the Flask app.

    :param test_config: Optional dict config injected during tests
    :return: Configured Flask app
    """
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance")
    os.makedirs(instance_path, exist_ok=True)

    db_uri = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///" + os.path.join(instance_path, "data.db"),
    )

    # Resolve relative SQLite paths only (MySQL URI is used as-is)
    if db_uri.startswith("sqlite:///") and not db_uri.startswith("sqlite:////"):
        relative_path = db_uri.replace("sqlite:///", "", 1)
        if not os.path.isabs(relative_path):
            db_uri = "sqlite:///" + os.path.join(
                os.path.abspath(os.path.dirname(__file__)), relative_path
            )
        db_file = db_uri.replace("sqlite:///", "", 1)
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
        os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS", "False").lower() == "true"
    )

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret")
    expires = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "86400"))
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=expires)

    app.config["API_TITLE"] = "E-Commerce REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)
    api.init_app(app)

    register_blueprints(api)

    _register_error_handlers(app)

    with app.app_context():
        import models  # noqa: F401

        if db_uri.startswith("mysql"):
            from utils.wait_db import wait_for_db

            wait_for_db()

        db.create_all()

        from utils.db_migrate import run_migrations

        run_migrations()

        from utils.seed import load_dummy_data

        load_dummy_data()

    @app.route("/")
    def index():
        """Frontend admin dashboard."""
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        """API health check (JSON)."""
        return jsonify(
            {
                "message": "E-Commerce REST API is running.",
                "docs": "/swagger-ui",
                "frontend": "/",
                "version": "v1",
            }
        )

    return app


def _register_error_handlers(app):
    """Unified JSON error responses for RESTful API."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        return jsonify({"message": error.description}), error.code

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Token has expired."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return jsonify({"message": "Invalid token.", "error": error_string}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        return jsonify({"message": "Authorization required.", "error": error_string}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Token has been revoked."}), 401

    @app.errorhandler(NoAuthorizationError)
    def handle_no_auth(error):
        return jsonify({"message": "Authorization header missing or invalid."}), 401

    @app.errorhandler(JWTDecodeError)
    @app.errorhandler(InvalidHeaderError)
    @app.errorhandler(ExpiredSignatureError)
    @app.errorhandler(InvalidTokenError)
    def handle_jwt_errors(error):
        return jsonify({"message": str(error)}), 401


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
