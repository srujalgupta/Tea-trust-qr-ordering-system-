from app.extensions import db
from app.models import Payment


def create_cash_payment(order):
    payment = Payment(
        order=order,
        provider="cash",
        amount=order.total_amount,
        currency=order.currency,
        status="cash_pending",
    )
    db.session.add(payment)
    return payment
