import hashlib
import hmac
import json
import uuid
from decimal import Decimal

from app.extensions import db
from app.models import Payment
from .errors import NotFoundError, PaymentError, ValidationError


def amount_to_subunits(amount):
    return int((Decimal(amount).quantize(Decimal("0.01")) * 100).to_integral_value())


def razorpay_is_mock_mode(config):
    if config.get("RAZORPAY_FORCE_MOCK"):
        return True
    if not config.get("RAZORPAY_KEY_ID") or not config.get("RAZORPAY_KEY_SECRET"):
        return True
    try:
        import razorpay  # noqa: F401
    except ImportError:
        return True
    return False


def _razorpay_client(config):
    try:
        import razorpay
    except ImportError as exc:
        raise PaymentError("The razorpay package is not installed.") from exc
    return razorpay.Client(
        auth=(config["RAZORPAY_KEY_ID"], config["RAZORPAY_KEY_SECRET"])
    )


def create_gateway_payment(order, config):
    amount_subunits = amount_to_subunits(order.total_amount)
    if amount_subunits <= 0:
        raise ValidationError("Order amount must be greater than zero.")

    if razorpay_is_mock_mode(config):
        provider_order_id = f"mock_order_{uuid.uuid4().hex[:18]}"
        payment = Payment(
            order=order,
            provider="mock",
            provider_order_id=provider_order_id,
            amount=order.total_amount,
            currency=order.currency,
            status="created",
            raw_payload={"mode": "mock", "amount": amount_subunits},
        )
        db.session.add(payment)
        return payment, {
            "mode": "mock",
            "provider": "mock",
            "provider_order_id": provider_order_id,
            "amount": amount_subunits,
            "currency": order.currency,
            "key_id": "",
        }

    client = _razorpay_client(config)
    gateway_order = client.order.create(
        {
            "amount": amount_subunits,
            "currency": order.currency,
            "receipt": order.order_number[:40],
            "notes": {"local_order_id": str(order.id)},
        }
    )
    payment = Payment(
        order=order,
        provider="razorpay",
        provider_order_id=gateway_order["id"],
        amount=order.total_amount,
        currency=order.currency,
        status="created",
        raw_payload=gateway_order,
    )
    db.session.add(payment)
    return payment, {
        "mode": "razorpay",
        "provider": "razorpay",
        "provider_order_id": gateway_order["id"],
        "amount": gateway_order["amount"],
        "currency": gateway_order["currency"],
        "key_id": config["RAZORPAY_KEY_ID"],
    }


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


def verify_payment_signature(provider_order_id, provider_payment_id, signature, secret):
    if not provider_order_id or not provider_payment_id or not signature:
        raise PaymentError("Payment verification details are incomplete.")
    if not secret:
        raise PaymentError("RAZORPAY_KEY_SECRET is not configured.")

    message = f"{provider_order_id}|{provider_payment_id}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PaymentError("Payment signature verification failed.")
    return True


def verify_webhook_signature(raw_body, signature, secret):
    if not signature:
        raise PaymentError("Missing X-Razorpay-Signature header.")
    if not secret:
        raise PaymentError("RAZORPAY_WEBHOOK_SECRET is not configured.")

    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PaymentError("Webhook signature verification failed.")
    return True


def get_payment_by_provider_order_id(provider_order_id):
    payment = Payment.query.filter_by(provider_order_id=provider_order_id).first()
    if not payment:
        raise NotFoundError("Payment record not found.")
    return payment


def apply_checkout_success(data, config):
    provider_order_id = data.get("razorpay_order_id") or data.get("provider_order_id")
    provider_payment_id = data.get("razorpay_payment_id") or data.get("provider_payment_id")
    signature = data.get("razorpay_signature") or data.get("provider_signature")
    payment = get_payment_by_provider_order_id(provider_order_id)

    if payment.provider == "mock":
        provider_payment_id = provider_payment_id or f"mock_pay_{uuid.uuid4().hex[:18]}"
    else:
        verify_payment_signature(
            provider_order_id,
            provider_payment_id,
            signature,
            config["RAZORPAY_KEY_SECRET"],
        )

    payment.provider_payment_id = provider_payment_id
    payment.provider_signature = signature
    payment.status = "paid"
    payment.order.payment_status = "paid"
    payment.order.status = "pending"
    return payment


def parse_webhook(raw_body):
    try:
        return json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise PaymentError("Invalid webhook JSON payload.") from exc


def apply_webhook_event(raw_body, signature, event_id, config):
    verify_webhook_signature(raw_body, signature, config["RAZORPAY_WEBHOOK_SECRET"])
    payload = parse_webhook(raw_body)
    event_name = payload.get("event")

    if event_id and Payment.query.filter_by(webhook_event_id=event_id).first():
        return {"duplicate": True, "event": event_name}

    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    provider_order_id = entity.get("order_id")
    provider_payment_id = entity.get("id")
    if not provider_order_id:
        order_entity = payload.get("payload", {}).get("order", {}).get("entity", {})
        provider_order_id = order_entity.get("id")

    if not provider_order_id:
        return {"ignored": True, "event": event_name}

    payment = get_payment_by_provider_order_id(provider_order_id)
    payment.webhook_event_id = event_id
    payment.provider_payment_id = provider_payment_id or payment.provider_payment_id
    payment.raw_payload = payload

    if event_name in {"payment.captured", "order.paid"}:
        payment.status = "paid"
        payment.order.payment_status = "paid"
        payment.order.status = "pending"
    elif event_name == "payment.failed":
        payment.status = "failed"
        payment.order.payment_status = "failed"

    return {"event": event_name, "payment": payment}
