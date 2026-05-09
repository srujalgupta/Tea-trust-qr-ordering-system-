from functools import wraps

from flask import current_app, has_app_context, redirect, request, url_for
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User
from app.models.constants import STAFF_ROLES
from .errors import ForbiddenError, ValidationError


COMMON_WEAK_PASSWORDS = {
    "admin",
    "admin123",
    "admin12345",
    "password",
    "password123",
    "qwerty123",
    "letmein123",
    "1234567890",
    "123456789",
}

_DUMMY_PASSWORD_HASH = generate_password_hash("invalid-login-password")


def _password_min_length():
    if has_app_context():
        return current_app.config.get("PASSWORD_MIN_LENGTH", 12)
    return 12


def _allows_dev_seed_password(username, password):
    if not has_app_context():
        return False
    return (
        current_app.config.get("ENV_NAME") != "production"
        and username == current_app.config.get("ADMIN_USERNAME")
        and password == "admin12345"
    )


def admin_required(view):
    return permission_required(None)(view)


def permission_required(permission):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("admin.login", next=request.full_path))
            if not current_user.is_admin:
                raise ForbiddenError("Staff access is required.")
            if permission and not current_user.can(permission):
                raise ForbiddenError("This staff profile does not have access to that area.")
            return view(*args, **kwargs)

        return wrapped

    return decorator


def require_admin_api(permission=None):
    if not current_user.is_authenticated or not current_user.is_admin:
        raise ForbiddenError("Staff authentication is required.")
    if permission and not current_user.can(permission):
        raise ForbiddenError("This staff profile does not have access to that action.")


def validate_staff_role(role):
    role = (role or "").strip().lower()
    if role not in STAFF_ROLES:
        raise ValidationError("Choose a valid staff profile.")
    return role


def validate_password_strength(password, username=None, required=True):
    password = password or ""
    if required and not password:
        raise ValidationError("Password is required.")
    if not password:
        return password
    if password != password.strip():
        raise ValidationError("Password cannot start or end with spaces.")

    min_length = _password_min_length()
    if len(password) < min_length:
        raise ValidationError(f"Password must be at least {min_length} characters.")

    normalized = password.lower()
    normalized_username = (username or "").strip().lower()
    if normalized in COMMON_WEAK_PASSWORDS:
        raise ValidationError("Choose a less common password.")
    if normalized_username and normalized in {
        normalized_username,
        f"{normalized_username}123",
        f"{normalized_username}12345",
        f"{normalized_username}@123",
    }:
        raise ValidationError("Password cannot be based on the username.")
    return password


def owner_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("admin.login", next=request.full_path))
        if not current_user.is_admin:
            raise ForbiddenError("Staff access is required.")
        if current_user.role != "owner":
            raise ForbiddenError("Owner access is required.")
        return view(*args, **kwargs)

    return wrapped


def authenticate_user(username, password):
    username = (username or "").strip()
    if not username or not password:
        raise ValidationError("Username and password are required.")

    user = User.query.filter_by(username=username).first()
    if not user:
        check_password_hash(_DUMMY_PASSWORD_HASH, password or "")
        raise ValidationError("Invalid username or password.")
    if not user.check_password(password):
        raise ValidationError("Invalid username or password.")
    if not user.is_active:
        raise ForbiddenError("This account is disabled.")
    return user


def _clean_optional_email(value):
    value = (value or "").strip().lower()
    return value or None


def ensure_admin_user(username, password, email=None):
    username = (username or "").strip()
    email = _clean_optional_email(email)
    user = User.query.filter_by(username=username).first()
    if not user and email:
        user = User.query.filter_by(email=email).first()
    if user:
        changed = False
        if not user.role:
            user.role = "owner"
            changed = True
        if user.role == "owner" and user.store_id is not None:
            user.store_id = None
            changed = True
        if email and not user.email:
            email_owner = User.query.filter_by(email=email).first()
            if not email_owner or email_owner.id == user.id:
                user.email = email
                changed = True
        if changed:
            db.session.commit()
        return user, False

    if not _allows_dev_seed_password(username, password):
        validate_password_strength(password, username=username)

    user = User(
        username=username,
        email=email,
        is_admin=True,
        role="owner",
        store_id=None,
        active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user, True
