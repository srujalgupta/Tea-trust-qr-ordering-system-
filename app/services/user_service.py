import re

from app.extensions import db
from app.models import User
from app.models.constants import STAFF_ROLE_LABELS
from .auth_service import validate_password_strength, validate_staff_role
from .errors import NotFoundError, ValidationError


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def _clean_optional_email(value):
    value = (value or "").strip().lower()
    return value or None


def _clean_username(value):
    value = (value or "").strip()
    if len(value) < 3:
        raise ValidationError("Username must be at least 3 characters.")
    if len(value) > 80:
        raise ValidationError("Username must be 80 characters or fewer.")
    if not USERNAME_PATTERN.match(value):
        raise ValidationError("Username can only use letters, numbers, dots, dashes, and underscores.")
    return value


def _validate_password(password, username=None, required=True):
    return validate_password_strength(password, username=username, required=required)


def _ensure_username_available(username, user_id=None):
    user = User.query.filter_by(username=username).first()
    if user and user.id != user_id:
        raise ValidationError("That username is already in use.")


def _ensure_email_available(email, user_id=None):
    if not email:
        return
    user = User.query.filter_by(email=email).first()
    if user and user.id != user_id:
        raise ValidationError("That email is already in use.")


def _owner_count():
    return User.query.filter_by(is_admin=True, role="owner", active=True).count()


def _bool_value(value):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return bool(value)


def _protect_last_owner(user, next_role=None, next_active=None):
    next_role = next_role if next_role is not None else user.role
    next_active = next_active if next_active is not None else user.active
    if user.role == "owner" and user.active and (next_role != "owner" or not next_active):
        if _owner_count() <= 1:
            raise ValidationError("At least one active owner profile is required.")


def get_staff_profile(user_id):
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise NotFoundError("Staff profile not found.") from None
    user = db.session.get(User, user_id)
    if not user or not user.is_admin:
        raise NotFoundError("Staff profile not found.")
    return user


def list_staff_profiles():
    return User.query.filter_by(is_admin=True).order_by(User.active.desc(), User.username.asc()).all()


def create_staff_profile(data):
    username = _clean_username(data.get("username"))
    email = _clean_optional_email(data.get("email"))
    role = validate_staff_role(data.get("role"))
    password = _validate_password(data.get("password"), username=username, required=True)

    _ensure_username_available(username)
    _ensure_email_available(email)

    user = User(username=username, email=email, role=role, is_admin=True, active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def update_staff_profile(user_id, data, actor=None):
    user = get_staff_profile(user_id)

    next_role = validate_staff_role(data.get("role")) if "role" in data else user.role
    next_active = _bool_value(data.get("active")) if "active" in data else user.active
    _protect_last_owner(user, next_role=next_role, next_active=next_active)

    if actor and actor.id == user.id and (next_role != user.role or next_active != user.active):
        raise ValidationError("You cannot change your own role or active status.")

    if "username" in data:
        username = _clean_username(data.get("username"))
        _ensure_username_available(username, user.id)
        user.username = username
    if "email" in data:
        email = _clean_optional_email(data.get("email"))
        _ensure_email_available(email, user.id)
        user.email = email
    if "role" in data:
        user.role = next_role
    if "active" in data:
        user.active = next_active
    if data.get("password"):
        user.set_password(
            _validate_password(data.get("password"), username=user.username, required=False)
        )

    db.session.commit()
    return user


def delete_staff_profile(user_id, actor=None):
    user = get_staff_profile(user_id)
    _protect_last_owner(user, next_active=False)

    if actor and actor.id == user.id:
        raise ValidationError("You cannot delete your own profile.")

    db.session.delete(user)
    db.session.commit()


def role_options_payload():
    return [{"value": value, "label": STAFF_ROLE_LABELS[value]} for value in STAFF_ROLE_LABELS]
