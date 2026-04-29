from app.extensions import db
from .base import TimestampMixin
from .constants import ORDER_STATUSES, PAYMENT_METHODS, PAYMENT_STATUSES


class Order(TimestampMixin, db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(40), nullable=False, unique=True, index=True)
    table_id = db.Column(
        db.Integer,
        db.ForeignKey("tables.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    customer_name = db.Column(db.String(120), nullable=True)
    customer_phone = db.Column(db.String(30), nullable=True, index=True)
    notes = db.Column(db.Text, nullable=True)
    subtotal_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    currency = db.Column(db.String(3), nullable=False, default="INR")
    payment_method = db.Column(db.String(20), nullable=False, default="cash")
    payment_status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)

    table = db.relationship("CafeTable", back_populates="orders")
    items = db.relationship(
        "OrderItem",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    payments = db.relationship(
        "Payment",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    daily_token = db.relationship(
        "DailyToken",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.CheckConstraint(
            f"status IN {ORDER_STATUSES}",
            name="ck_orders_status",
        ),
        db.CheckConstraint(
            f"payment_status IN {PAYMENT_STATUSES}",
            name="ck_orders_payment_status",
        ),
        db.CheckConstraint(
            f"payment_method IN {PAYMENT_METHODS}",
            name="ck_orders_payment_method",
        ),
        db.CheckConstraint("total_amount >= 0", name="ck_orders_total_non_negative"),
        db.Index("ix_orders_status_created", "status", "created_at"),
        db.Index("ix_orders_table_created", "table_id", "created_at"),
    )


class OrderItem(TimestampMixin, db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    menu_item_id = db.Column(
        db.Integer,
        db.ForeignKey("menu_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    item_name = db.Column(db.String(160), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    menu_item = db.relationship("MenuItem", back_populates="order_items")

    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        db.CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        db.CheckConstraint("line_total >= 0", name="ck_order_items_line_total_non_negative"),
    )
