from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.extensions import db
from app.services.auth_service import admin_required, authenticate_user
from app.services.errors import AppError


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
def index():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("admin.login"))


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        try:
            user = authenticate_user(
                request.form.get("username"),
                request.form.get("password"),
            )
        except AppError as exc:
            flash(exc.message, "error")
        else:
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(request.args.get("next") or url_for("admin.dashboard"))

    return render_template("admin/login.html")


@admin_bp.post("/logout")
@admin_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("admin.login"))


@admin_bp.get("/dashboard")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")


@admin_bp.get("/menu")
@admin_required
def menu_manager():
    return render_template("admin/menu.html")


@admin_bp.get("/tables")
@admin_required
def table_manager():
    return render_template("admin/tables.html")


@admin_bp.get("/kitchen")
@admin_required
def kitchen_display():
    return render_template("admin/kitchen.html")


@admin_bp.get("/analytics")
@admin_required
def analytics():
    return render_template("admin/analytics.html")


@admin_bp.get("/settings")
@admin_required
def settings():
    database_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    database_label = "PostgreSQL" if database_uri.startswith("postgresql") else "SQLite / local"
    return render_template(
        "admin/settings.html",
        database_label=database_label,
        environment_name=current_app.config["ENV_NAME"],
        secret_configured=current_app.config["SECRET_KEY"] != "dev-only-change-me",
        database_configured=bool(current_app.config.get("DATABASE_URL")),
        password_changed=current_app.config["ADMIN_PASSWORD"] != "admin12345",
        socketio_eventlet=current_app.config["SOCKETIO_ASYNC_MODE"] == "eventlet",
    )


@admin_bp.post("/settings/password")
@admin_required
def change_password():
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("admin.settings"))
    if len(new_password) < 10:
        flash("New password must be at least 10 characters.", "error")
        return redirect(url_for("admin.settings"))
    if new_password != confirm_password:
        flash("New passwords do not match.", "error")
        return redirect(url_for("admin.settings"))

    current_user.set_password(new_password)
    db.session.commit()
    flash("Admin password updated.", "success")
    return redirect(url_for("admin.settings"))
