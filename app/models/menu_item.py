from decimal import Decimal

from app.extensions import db
from .base import TimestampMixin


class MenuItem(TimestampMixin, db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(160), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    is_available = db.Column(db.Boolean, nullable=False, default=True, index=True)
    is_veg = db.Column(db.Boolean, nullable=False, default=True, index=True)
    is_bestseller = db.Column(db.Boolean, nullable=False, default=False, index=True)
    tags = db.Column(db.String(255), nullable=True)

    category = db.relationship("Category", back_populates="menu_items")
    order_items = db.relationship("OrderItem", back_populates="menu_item")

    __table_args__ = (
        db.CheckConstraint("price >= 0", name="ck_menu_items_price_non_negative"),
        db.Index("ix_menu_items_category_available", "category_id", "is_available"),
    )

    def normalized_price(self):
        return Decimal(self.price).quantize(Decimal("0.01"))
