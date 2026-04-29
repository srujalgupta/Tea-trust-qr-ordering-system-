import logging
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from config import INSTANCE_DIR, get_config
from .extensions import db, login_manager, migrate, socketio
from .services.errors import AppError


def create_app(config_name=None):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

    _configure_logging(app)
    _validate_config(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    _configure_login_manager()
    socketio.init_app(app, async_mode=app.config["SOCKETIO_ASYNC_MODE"])

    from . import models as _models  # noqa: F401

    from .commands import register_commands
    from .services.security import register_security
    from .sockets import register_socket_handlers

    register_security(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_template_context(app)
    register_commands(app)
    register_socket_handlers()

    app.logger.info("Application started with %s config", app.config["ENV_NAME"])

    return app


def _register_blueprints(app):
    from .routes import register_blueprints

    register_blueprints(app)


def _configure_logging(app):
    level_name = app.config.get("LOG_LEVEL", "INFO")
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format="%(levelname)s:%(name)s:%(message)s")
    app.logger.setLevel(level)


def _configure_login_manager():
    login_manager.session_protection = "strong"
    login_manager.login_view = "admin.login"
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        if not str(user_id).isdigit():
            return None
        from app.models import User

        return db.session.get(User, int(user_id))


def _validate_config(app):
    if app.config["ENV_NAME"] != "production":
        return

    missing = []
    if app.config["SECRET_KEY"] == "dev-only-change-me":
        missing.append("SECRET_KEY")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        missing.append("DATABASE_URL")
    if app.config["ADMIN_PASSWORD"] == "admin12345":
        missing.append("ADMIN_PASSWORD")

    if missing:
        raise RuntimeError(
            "Missing required production environment variables: "
            + ", ".join(missing)
        )


def _wants_json_response():
    return (
        request.path.startswith("/api/")
        or request.accept_mimetypes.best == "application/json"
    )


def _register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        payload = {
            "error": error.error_code,
            "message": error.message,
        }
        if _wants_json_response():
            return jsonify(payload), error.status_code

        return render_template(
            "errors/error.html",
            status_code=error.status_code,
            message=error.message,
        ), error.status_code

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        db.session.rollback()
        app.logger.warning("Database integrity error: %s", error)
        payload = {
            "error": "integrity_error",
            "message": "A record with this value already exists or violates a database rule.",
        }
        if _wants_json_response():
            return jsonify(payload), 400

        return render_template(
            "errors/error.html",
            status_code=400,
            message=payload["message"],
        ), 400

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        payload = {
            "error": error.name.lower().replace(" ", "_"),
            "message": error.description,
        }
        if _wants_json_response():
            return jsonify(payload), error.code

        template = "errors/404.html" if error.code == 404 else "errors/error.html"
        return render_template(
            template,
            status_code=error.code,
            message=error.description,
        ), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        app.logger.exception("Unhandled application error")
        payload = {
            "error": "internal_server_error",
            "message": "An unexpected error occurred.",
        }
        if _wants_json_response():
            return jsonify(payload), 500

        return render_template(
            "errors/error.html",
            status_code=500,
            message=payload["message"],
        ), 500


def _register_template_context(app):
    @app.context_processor
    def inject_cafe_branding():
        return {
            "cafe": {
                "name": app.config["CAFE_NAME"],
                "tagline": app.config["CAFE_TAGLINE"],
                "subtitle": app.config["CAFE_SUBTITLE"],
                "phone": app.config["CAFE_PHONE"],
            },
            "table_count": app.config["CAFE_TABLE_COUNT"],
            "today_label": datetime.now().strftime("%d %b %Y").lstrip("0"),
        }
