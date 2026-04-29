from app.extensions import db
from .base import TimestampMixin
from .constants import TOKEN_STATUSES


class DailyToken(TimestampMixin, db.Model):
    __tablename__ = "daily_tokens"

    id = db.Column(db.Integer, primary_key=True)
    token_date = db.Column(db.Date, nullable=False, index=True)
    token_number = db.Column(db.Integer, nullable=False)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)

    order = db.relationship("Order", back_populates="daily_token")

    __table_args__ = (
        db.UniqueConstraint("token_date", "token_number", name="uq_daily_tokens_date_number"),
        db.CheckConstraint("token_number > 0", name="ck_daily_tokens_number_positive"),
        db.CheckConstraint(
            f"status IN {TOKEN_STATUSES}",
            name="ck_daily_tokens_status",
        ),
        db.Index("ix_daily_tokens_date_status", "token_date", "status"),
    )
