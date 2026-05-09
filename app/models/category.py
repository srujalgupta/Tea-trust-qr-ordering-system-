from app.extensions import db
from .base import TimestampMixin


class Category(TimestampMixin, db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(
        db.Integer,
        db.ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        default=1,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, nullable=False, default=0, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    store = db.relationship("Store", back_populates="categories")
    menu_items = db.relationship(
        "MenuItem",
        back_populates="category",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint("store_id", "name", name="uq_categories_store_name"),
        db.Index("ix_categories_store_order", "store_id", "display_order"),
    )
