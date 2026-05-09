from app.extensions import db
from .base import TimestampMixin


class Store(TimestampMixin, db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    address = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    categories = db.relationship(
        "Category",
        back_populates="store",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    menu_items = db.relationship("MenuItem", back_populates="store", lazy="selectin")
    tables = db.relationship("CafeTable", back_populates="store", lazy="selectin")
    orders = db.relationship("Order", back_populates="store", lazy="selectin")
    customer_contacts = db.relationship(
        "CustomerContact",
        back_populates="store",
        lazy="selectin",
    )
