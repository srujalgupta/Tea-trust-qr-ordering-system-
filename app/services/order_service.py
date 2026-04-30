import uuid
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import CafeTable, MenuItem, Order, OrderItem
from app.models.constants import ORDER_STATUSES, TOKEN_STATUSES
from .errors import NotFoundError, ValidationError
from .notification_service import send_order_confirmation, send_order_ready
from .payment_service import apply_checkout_success, create_cash_payment
from .pos_service import send_order_to_pos
from .realtime_service import emit_order_created, emit_order_updated
from .serializers import serialize_order
from .token_service import generate_daily_token_for_order, sync_token_status


def _order_number():
    return f"QC-{uuid.uuid4().hex[:10].upper()}"


def _normalize_items(items):
    if not isinstance(items, list) or not items:
        raise ValidationError("At least one order item is required.")

    quantities = {}
    notes = {}
    for item in items:
        try:
            menu_item_id = int(item.get("menu_item_id") or item.get("id"))
            quantity = int(item.get("quantity"))
        except (AttributeError, TypeError, ValueError):
            raise ValidationError("Each item requires menu_item_id and quantity.") from None
        if menu_item_id <= 0 or quantity <= 0:
            raise ValidationError("Item ids and quantities must be positive.")
        if quantity > 25:
            raise ValidationError("Quantity per item cannot exceed 25.")
        quantities[menu_item_id] = quantities.get(menu_item_id, 0) + quantity
        note = (item.get("note") or "").strip()[:240]
        if note:
            existing = notes.get(menu_item_id)
            notes[menu_item_id] = f"{existing}; {note}" if existing else note
    return quantities, notes


def _get_active_table(table_id):
    if table_id in (None, "", 0):
        return None
    try:
        table_id = int(table_id)
    except (TypeError, ValueError):
        raise ValidationError("table_id must be a number.") from None
    table = db.session.get(CafeTable, table_id)
    if not table or not table.is_active:
        raise ValidationError("Selected table is not available.")
    return table


def _get_menu_items(item_quantities):
    items = (
        MenuItem.query.options(selectinload(MenuItem.category))
        .filter(MenuItem.id.in_(item_quantities.keys()))
        .all()
    )
    found = {item.id: item for item in items}
    missing = set(item_quantities.keys()) - set(found.keys())
    if missing:
        raise ValidationError(f"Menu item not found: {sorted(missing)[0]}.")

    unavailable = [item.name for item in found.values() if not item.is_available]
    if unavailable:
        raise ValidationError(f"{unavailable[0]} is currently unavailable.")
    return found


def create_order(data, config):
    item_quantities, item_notes = _normalize_items(data.get("items"))
    menu_items = _get_menu_items(item_quantities)
    table = _get_active_table(data.get("table_id"))

    payment_method = (data.get("payment_method") or "cash").strip().lower()
    if payment_method != "cash":
        raise ValidationError("Online payment is disabled. Customers pay directly at the store.")

    subtotal = Decimal("0.00")
    order_notes = (data.get("notes") or "").strip()[:1000]
    instruction_lines = []
    for menu_item_id, note in item_notes.items():
        menu_item = menu_items.get(menu_item_id)
        if menu_item:
            instruction_lines.append(f"- {menu_item.name}: {note}")
    if instruction_lines:
        item_notes_text = "Item instructions:\n" + "\n".join(instruction_lines)
        order_notes = f"{order_notes}\n\n{item_notes_text}".strip()

    order = Order(
        order_number=_order_number(),
        table=table,
        customer_name=(data.get("customer_name") or "").strip()[:120],
        customer_phone=(data.get("customer_phone") or "").strip()[:30],
        notes=order_notes,
        currency=config["PAYMENT_CURRENCY"],
        payment_method=payment_method,
        payment_status="cash_pending",
        status="pending",
    )
    db.session.add(order)

    for menu_item_id, quantity in item_quantities.items():
        menu_item = menu_items[menu_item_id]
        unit_price = menu_item.normalized_price()
        line_total = unit_price * quantity
        subtotal += line_total
        order.items.append(
            OrderItem(
                menu_item=menu_item,
                item_name=menu_item.name,
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    order.subtotal_amount = subtotal
    order.tax_amount = Decimal("0.00")
    order.total_amount = subtotal
    db.session.flush()

    create_cash_payment(order)
    generate_daily_token_for_order(order)

    db.session.commit()

    after_order_confirmed(order, config)

    return order, None


def get_order(order_id):
    order = (
        Order.query.options(
            selectinload(Order.items),
            selectinload(Order.payments),
            selectinload(Order.daily_token),
            selectinload(Order.table),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise NotFoundError("Order not found.")
    return order


def list_orders(status=None):
    query = Order.query.options(
        selectinload(Order.items),
        selectinload(Order.payments),
        selectinload(Order.daily_token),
        selectinload(Order.table),
    )
    if status:
        query = query.filter(Order.status == status)
    return query.order_by(Order.created_at.desc()).all()


def after_order_confirmed(order, config):
    payload = serialize_order(order)
    try:
        send_order_to_pos(payload, config.get("POS_WEBHOOK_URL"))
    except Exception:
        pass
    try:
        send_order_confirmation(payload, config.get("NOTIFICATION_WEBHOOK_URL"))
    except Exception:
        pass
    emit_order_created(order)


def confirm_payment(data, config):
    payment = apply_checkout_success(data, config)
    order = payment.order
    generate_daily_token_for_order(order)
    db.session.commit()
    after_order_confirmed(order, config)
    return order


def confirm_payment_from_webhook(result, config):
    payment = result.get("payment")
    if not payment:
        return None
    order = payment.order
    if payment.status == "paid" and not order.daily_token:
        generate_daily_token_for_order(order)
    db.session.commit()
    if payment.status == "paid":
        after_order_confirmed(order, config)
    return order


def update_order_status(order_id, status, config, cancellation_reason=None):
    status = (status or "").strip().lower()
    if status not in ORDER_STATUSES:
        raise ValidationError("Invalid order status.")
    if status in {"pending", "preparing", "ready", "completed"} and status not in TOKEN_STATUSES:
        raise ValidationError("Invalid token status.")

    order = get_order(order_id)
    if order.status == "payment_pending" and status != "cancelled":
        raise ValidationError("Cannot update kitchen status before payment confirmation.")

    order.status = status
    if status == "cancelled":
        reason = (cancellation_reason or "").strip()[:240]
        if reason and "Cancellation reason:" not in (order.notes or ""):
            order.notes = f"{order.notes or ''}\n\nCancellation reason: {reason}".strip()
        if order.payment_status == "paid":
            order.payment_status = "refunded"
            for payment in order.payments:
                if payment.status == "paid":
                    payment.status = "refunded"
    elif status == "completed" and order.payment_method == "cash" and order.payment_status == "cash_pending":
        order.payment_status = "paid"
        for payment in order.payments:
            if payment.provider == "cash" and payment.status == "cash_pending":
                payment.status = "paid"
    if status in TOKEN_STATUSES:
        sync_token_status(order, status)
    db.session.commit()

    if status == "ready":
        try:
            send_order_ready(serialize_order(order), config.get("NOTIFICATION_WEBHOOK_URL"))
        except Exception:
            pass
    emit_order_updated(order)
    return order
