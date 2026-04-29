from app.extensions import db
from datetime import datetime

class DailyToken(db.Model):
    __tablename__ = "daily_tokens"

    id = db.Column(db.Integer, primary_key=True)
    token_number = db.Column(db.Integer, nullable=False)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))

    status = db.Column(db.String(50), default="pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)