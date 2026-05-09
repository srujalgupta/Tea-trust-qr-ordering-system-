from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from .base import TimestampMixin
from .constants import ROLE_PERMISSIONS, STAFF_ROLE_LABELS


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    email = db.Column(db.String(255), nullable=True, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=True)
    role = db.Column(db.String(30), nullable=False, default="owner", index=True)
    store_id = db.Column(
        db.Integer,
        db.ForeignKey("stores.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    active = db.Column(db.Boolean, nullable=False, default=True)

    store = db.relationship("Store")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password or "")

    @property
    def is_active(self):
        return self.active

    @property
    def role_label(self):
        return STAFF_ROLE_LABELS.get(self.role, "Staff")

    @property
    def permissions(self):
        return ROLE_PERMISSIONS.get(self.role, set())

    def can(self, permission):
        permissions = self.permissions
        return "*" in permissions or permission in permissions

    def can_access_store(self, store_id):
        if self.role == "owner":
            return True
        return self.store_id is not None and int(self.store_id) == int(store_id)
