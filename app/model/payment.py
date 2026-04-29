from app.extensions import db

class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))

    razorpay_order_id = db.Column(db.String(100))
    payment_id = db.Column(db.String(100))

    status = db.Column(db.String(50))