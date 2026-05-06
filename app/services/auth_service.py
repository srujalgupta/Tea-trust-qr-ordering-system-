from functools import wraps

from flask import redirect, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import User
from app.models.constants import STAFF_ROLES
from .errors import ForbiddenError, ValidationError


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
    if not user or not user.check_password(password):
        raise ValidationError("Invalid username or password.")
    if not user.is_active:
        raise ForbiddenError("This account is disabled.")
    return user


def ensure_admin_user(username, password, email=None):
    user = User.query.filter_by(username=username).first()
    if user:
        if not user.role:
            user.role = "owner"
            db.session.commit()
        return user, False

    user = User(username=username, email=email, is_admin=True, role="owner", active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user, True
