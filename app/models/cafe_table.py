from app.extensions import db
from .base import TimestampMixin


class CafeTable(TimestampMixin, db.Model):
    __tablename__ = "tables"

    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, nullable=False, unique=True, index=True)
    label = db.Column(db.String(120), nullable=True)
    qr_slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    orders = db.relationship("Order", back_populates="table")

    __table_args__ = (
        db.CheckConstraint("table_number > 0", name="ck_tables_table_number_positive"),
    )
