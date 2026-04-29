from functools import wraps

from flask import redirect, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import User
from .errors import ForbiddenError, ValidationError


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("admin.login", next=request.full_path))
        if not current_user.is_admin:
            raise ForbiddenError("Admin access is required.")
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
        return user, False

    user = User(username=username, email=email, is_admin=True, active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user, True
