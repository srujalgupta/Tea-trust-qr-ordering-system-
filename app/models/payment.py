from app.extensions import db
from .base import TimestampMixin
from .constants import PAYMENT_PROVIDERS, PAYMENT_STATUSES


class Payment(TimestampMixin, db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider = db.Column(db.String(30), nullable=False, default="cash", index=True)
    provider_order_id = db.Column(db.String(120), nullable=True, index=True)
    provider_payment_id = db.Column(db.String(120), nullable=True, index=True)
    provider_signature = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="INR")
    status = db.Column(db.String(30), nullable=False, default="created", index=True)
    webhook_event_id = db.Column(db.String(120), nullable=True, unique=True)
    raw_payload = db.Column(db.JSON, nullable=True)

    order = db.relationship("Order", back_populates="payments")

    __table_args__ = (
        db.CheckConstraint(
            f"provider IN {PAYMENT_PROVIDERS}",
            name="ck_payments_provider",
        ),
        db.CheckConstraint(
            f"status IN {PAYMENT_STATUSES}",
            name="ck_payments_status",
        ),
        db.CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
    )
