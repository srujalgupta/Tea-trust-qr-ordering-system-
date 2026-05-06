from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from app.extensions import db
from app.services.auth_service import (
    admin_required,
    authenticate_user,
    permission_required,
    validate_password_strength,
)
from app.services.errors import AppError
from app.services.security import generate_csrf_token


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _default_admin_endpoint(user):
    if user.can("dashboard:view"):
        return "admin.dashboard"
    if user.can("orders:update"):
        return "admin.kitchen_display"
    if user.can("menu:manage"):
        return "admin.menu_manager"
    return "admin.settings"


def _safe_next_url(target):
    if not target:
        return None
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not target.startswith("/"):
        return None
    return target


@admin_bp.get("/")
def index():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for(_default_admin_endpoint(current_user)))
    return redirect(url_for("admin.login"))


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for(_default_admin_endpoint(current_user)))

    if request.method == "POST":
        try:
            user = authenticate_user(
                request.form.get("username"),
                request.form.get("password"),
            )
        except AppError as exc:
            flash(exc.message, "error")
        else:
            session.clear()
            login_user(user)
            session.permanent = True
            generate_csrf_token()
            flash("Logged in successfully.", "success")
            return redirect(
                _safe_next_url(request.args.get("next"))
                or url_for(_default_admin_endpoint(user))
            )

    return render_template("admin/login.html")


@admin_bp.post("/logout")
@admin_required
def logout():
    logout_user()
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("admin.login"))


@admin_bp.get("/dashboard")
@permission_required("dashboard:view")
def dashboard():
    return render_template("admin/dashboard.html")


@admin_bp.get("/menu")
@permission_required("menu:manage")
def menu_manager():
    return render_template("admin/menu.html")


@admin_bp.get("/tables")
@permission_required("tables:manage")
def table_manager():
    return render_template("admin/tables.html")


@admin_bp.get("/kitchen")
@permission_required("orders:update")
def kitchen_display():
    return render_template("admin/kitchen.html")


@admin_bp.get("/analytics")
@permission_required("analytics:view")
def analytics():
    return render_template("admin/analytics.html")


@admin_bp.get("/settings")
@permission_required("settings:view")
def settings():
    database_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    database_label = "PostgreSQL" if database_uri.startswith("postgresql") else "SQLite / local"
    secret_key = current_app.config["SECRET_KEY"]
    admin_password = current_app.config["ADMIN_PASSWORD"]
    return render_template(
        "admin/settings.html",
        database_label=database_label,
        environment_name=current_app.config["ENV_NAME"],
        secret_configured=bool(secret_key)
        and secret_key != "dev-only-change-me"
        and len(secret_key) >= 32,
        database_configured=bool(current_app.config.get("DATABASE_URL")),
        password_changed=bool(admin_password)
        and admin_password != "admin12345"
        and len(admin_password) >= current_app.config["PASSWORD_MIN_LENGTH"],
        password_min_length=current_app.config["PASSWORD_MIN_LENGTH"],
        socketio_eventlet=current_app.config["SOCKETIO_ASYNC_MODE"] == "eventlet",
    )


@admin_bp.post("/settings/password")
@admin_required
def change_password():
    current_password = request.form.get("current_password") or ""
    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("admin.settings"))
    if new_password != confirm_password:
        flash("New passwords do not match.", "error")
        return redirect(url_for("admin.settings"))
    try:
        validate_password_strength(new_password, username=current_user.username)
    except AppError as exc:
        flash(exc.message, "error")
        return redirect(url_for("admin.settings"))

    current_user.set_password(new_password)
    db.session.commit()
    flash("Admin password updated.", "success")
    return redirect(url_for("admin.settings"))
