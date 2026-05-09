from app.extensions import db
from .base import TimestampMixin


class CustomerContact(TimestampMixin, db.Model):
    __tablename__ = "customer_contacts"

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(
        db.Integer,
        db.ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        default=1,
        index=True,
    )
    name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=False, index=True)
    marketing_opt_in = db.Column(db.Boolean, nullable=False, default=False, index=True)
    order_count = db.Column(db.Integer, nullable=False, default=0)
    total_spend = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    first_order_at = db.Column(db.DateTime, nullable=True)
    last_order_at = db.Column(db.DateTime, nullable=True, index=True)
    last_order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    store = db.relationship("Store", back_populates="customer_contacts")
    last_order = db.relationship("Order")

    __table_args__ = (
        db.UniqueConstraint("store_id", "phone", name="uq_customer_contacts_store_phone"),
    )
