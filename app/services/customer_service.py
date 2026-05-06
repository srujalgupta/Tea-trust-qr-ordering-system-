from decimal import Decimal

from app.extensions import db
from app.models import CustomerContact
from .errors import ValidationError


def normalize_phone(value):
    value = (value or "").strip()
    if not value:
        return ""

    has_plus = value.startswith("+")
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) < 7 or len(digits) > 16:
        raise ValidationError("Enter a valid phone number.")
    return f"+{digits}" if has_plus else digits


def upsert_customer_contact(order, marketing_opt_in=False):
    phone = normalize_phone(order.customer_phone)
    if not phone:
        return None

    contact = CustomerContact.query.filter_by(phone=phone).first()
    if not contact:
        contact = CustomerContact(phone=phone, order_count=0, total_spend=Decimal("0.00"))
        db.session.add(contact)

    if order.customer_name:
        contact.name = order.customer_name
    contact.marketing_opt_in = bool(contact.marketing_opt_in or marketing_opt_in)
    contact.order_count = int(contact.order_count or 0) + 1
    contact.total_spend = Decimal(contact.total_spend or 0) + Decimal(order.total_amount or 0)
    contact.first_order_at = contact.first_order_at or order.created_at
    contact.last_order_at = order.created_at
    contact.last_order_id = order.id
    order.customer_phone = phone
    return contact


def list_customer_contacts(marketing_only=False):
    query = CustomerContact.query
    if marketing_only:
        query = query.filter_by(marketing_opt_in=True)
    return query.order_by(
        CustomerContact.last_order_at.desc().nullslast(),
        CustomerContact.created_at.desc(),
    ).all()
