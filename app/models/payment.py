from app.extensions import db
from .base import TimestampMixin
from .constants import PAYMENT_PROVIDER_SQL, PAYMENT_STATUS_SQL


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
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="INR")
    status = db.Column(db.String(30), nullable=False, default="cash_pending", index=True)

    order = db.relationship("Order", back_populates="payments")

    __table_args__ = (
        db.CheckConstraint(
            f"provider IN {PAYMENT_PROVIDER_SQL}",
            name="ck_payments_provider",
        ),
        db.CheckConstraint(
            f"status IN {PAYMENT_STATUS_SQL}",
            name="ck_payments_status",
        ),
        db.CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
    )
