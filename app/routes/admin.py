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
from app.services.store_service import get_store


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


def _store_from_login_request(store_slug=None):
    store_ref = (
        store_slug
        or request.form.get("store")
        or request.args.get("store")
        or request.args.get("store_id")
    )
    return get_store(store_ref) if store_ref else None


def _default_admin_url(user, store=None):
    if store and user.can_access_store(store.id):
        return url_for(_default_admin_endpoint(user), store=store.slug)
    if getattr(user, "store", None) and user.can_access_store(user.store.id):
        return url_for(_default_admin_endpoint(user), store=user.store.slug)
    return url_for(_default_admin_endpoint(user))


@admin_bp.get("/")
def index():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(_default_admin_url(current_user, _store_from_login_request()))
    store_ref = request.args.get("store") or request.args.get("store_id")
    if store_ref:
        return redirect(url_for("admin.login", store=store_ref))
    return redirect(url_for("admin.login"))


@admin_bp.route("/login", methods=["GET", "POST"])
@admin_bp.route("/<store_slug>/login", methods=["GET", "POST"])
def login(store_slug=None):
    login_store = _store_from_login_request(store_slug)
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(_default_admin_url(current_user, login_store))

    if request.method == "POST":
        try:
            user = authenticate_user(
                request.form.get("username"),
                request.form.get("password"),
            )
        except AppError as exc:
            flash(exc.message, "error")
        else:
            if login_store and not user.can_access_store(login_store.id):
                flash(
                    f"This login is for {login_store.name}. Use a {login_store.name} profile or an owner account.",
                    "error",
                )
                return render_template("admin/login.html", store=login_store)

            session.clear()
            login_user(user)
            session.permanent = True
            generate_csrf_token()
            flash("Logged in successfully.", "success")
            return redirect(
                _safe_next_url(request.args.get("next"))
                or _default_admin_url(user, login_store)
            )

    return render_template("admin/login.html", store=login_store)


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
    return render_template(
        "admin/settings.html",
        database_label=database_label,
        environment_name=current_app.config["ENV_NAME"],
        password_min_length=current_app.config["PASSWORD_MIN_LENGTH"],
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
