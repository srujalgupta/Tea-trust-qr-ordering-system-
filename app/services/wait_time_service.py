from math import ceil

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import CafeTable, MenuItem, Order
from .errors import ValidationError
from .store_service import get_store, validate_store_match


ACTIVE_WAIT_STATUSES = ("pending", "preparing")
BASE_PREP_MINUTES = 5
PREPARING_BASE_MINUTES = 3
MINUTES_PER_CART_ITEM = 2
PREPARING_MINUTES_PER_ITEM = 1.5
MINUTES_PER_QUEUE_ORDER = 3
MINUTES_PER_QUEUE_ITEM = 1
WAIT_RANGE_PADDING_MINUTES = 5


def _store_reference(data):
    return (
        data.get("store_id")
        or data.get("store")
        or data.get("location_id")
        or data.get("location")
    )


def _active_table(table_id):
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


def _resolve_store(data):
    table = _active_table(data.get("table_id"))
    store_reference = _store_reference(data)
    if store_reference:
        store = get_store(store_reference)
    else:
        store = table.store if table else get_store()
    if table:
        validate_store_match(
            table.store_id,
            store,
            "Selected table belongs to a different store.",
        )
    return store


def _normalize_cart_items(items):
    if not items:
        return {}
    if not isinstance(items, list):
        raise ValidationError("items must be a list.")

    quantities = {}
    for item in items:
        try:
            menu_item_id = int(item.get("menu_item_id") or item.get("id"))
            quantity = int(item.get("quantity"))
        except (AttributeError, TypeError, ValueError):
            raise ValidationError("Each item requires menu_item_id and quantity.") from None
        if menu_item_id <= 0 or quantity <= 0:
            raise ValidationError("Item ids and quantities must be positive.")
        total_quantity = quantities.get(menu_item_id, 0) + quantity
        if total_quantity > 25:
            raise ValidationError("Quantity per item cannot exceed 25.")
        quantities[menu_item_id] = total_quantity
    return quantities


def _available_menu_items(item_quantities, store):
    if not item_quantities:
        return {}
    items = (
        MenuItem.query.options(selectinload(MenuItem.category))
        .filter(MenuItem.store_id == store.id)
        .filter(MenuItem.id.in_(item_quantities.keys()))
        .all()
    )
    found = {item.id: item for item in items}
    missing = set(item_quantities.keys()) - set(found.keys())
    if missing:
        raise ValidationError(f"Menu item not found: {sorted(missing)[0]}.")

    unavailable = [
        item.name
        for item in found.values()
        if not item.is_available or not item.category or not item.category.is_active
    ]
    if unavailable:
        raise ValidationError(f"{unavailable[0]} is currently unavailable.")
    return found


def _queue_orders(store, before_order=None):
    query = (
        Order.query.options(selectinload(Order.items))
        .filter(Order.store_id == store.id)
        .filter(Order.status.in_(ACTIVE_WAIT_STATUSES))
    )
    if before_order is not None:
        query = query.filter(Order.id != before_order.id)
        if before_order.created_at:
            query = query.filter(
                db.or_(
                    Order.created_at < before_order.created_at,
                    db.and_(
                        Order.created_at == before_order.created_at,
                        Order.id < before_order.id,
                    ),
                )
            )
    return query.order_by(Order.created_at.asc(), Order.id.asc()).all()


def _item_count_from_quantities(item_quantities):
    return sum(int(quantity or 0) for quantity in item_quantities.values())


def _item_count_from_order(order):
    return sum(int(item.quantity or 0) for item in order.items)


def _queue_item_count(orders):
    return sum(_item_count_from_order(order) for order in orders)


def _own_prep_minutes(item_count, status=None):
    if item_count <= 0:
        return 0
    if status == "preparing":
        return PREPARING_BASE_MINUTES + ceil(item_count * PREPARING_MINUTES_PER_ITEM)
    return BASE_PREP_MINUTES + item_count * MINUTES_PER_CART_ITEM


def _build_estimate(store, item_count, queue_orders, status=None):
    queue_order_count = len(queue_orders)
    queue_item_count = _queue_item_count(queue_orders)

    if item_count <= 0:
        return {
            "store_id": store.id,
            "store_name": store.name,
            "cart_item_count": 0,
            "queue_order_count": queue_order_count,
            "queue_item_count": queue_item_count,
            "estimated_wait_minutes_min": 0,
            "estimated_wait_minutes_max": 0,
            "estimated_wait_label": "Add items to see wait time",
        }

    queue_minutes = (
        queue_order_count * MINUTES_PER_QUEUE_ORDER
        + queue_item_count * MINUTES_PER_QUEUE_ITEM
    )
    min_minutes = max(5, queue_minutes + _own_prep_minutes(item_count, status=status))
    max_minutes = min_minutes + WAIT_RANGE_PADDING_MINUTES

    return {
        "store_id": store.id,
        "store_name": store.name,
        "cart_item_count": item_count,
        "queue_order_count": queue_order_count,
        "queue_item_count": queue_item_count,
        "estimated_wait_minutes_min": min_minutes,
        "estimated_wait_minutes_max": max_minutes,
        "estimated_wait_label": f"Estimated wait: {min_minutes}-{max_minutes} minutes",
    }


def estimate_wait_for_cart(data):
    store = _resolve_store(data or {})
    item_quantities = _normalize_cart_items((data or {}).get("items"))
    _available_menu_items(item_quantities, store)
    return _build_estimate(
        store,
        _item_count_from_quantities(item_quantities),
        _queue_orders(store),
    )


def estimate_wait_for_order(order):
    if order.status == "ready":
        return {
            "store_id": order.store_id,
            "store_name": order.store.name if order.store else "",
            "cart_item_count": _item_count_from_order(order),
            "queue_order_count": 0,
            "queue_item_count": 0,
            "estimated_wait_minutes_min": 0,
            "estimated_wait_minutes_max": 0,
            "estimated_wait_label": "Ready now",
        }
    if order.status == "completed":
        return {
            "store_id": order.store_id,
            "store_name": order.store.name if order.store else "",
            "cart_item_count": _item_count_from_order(order),
            "queue_order_count": 0,
            "queue_item_count": 0,
            "estimated_wait_minutes_min": 0,
            "estimated_wait_minutes_max": 0,
            "estimated_wait_label": "Completed",
        }
    if order.status == "cancelled":
        return {
            "store_id": order.store_id,
            "store_name": order.store.name if order.store else "",
            "cart_item_count": _item_count_from_order(order),
            "queue_order_count": 0,
            "queue_item_count": 0,
            "estimated_wait_minutes_min": 0,
            "estimated_wait_minutes_max": 0,
            "estimated_wait_label": "Order cancelled",
        }

    store = order.store or get_store(order.store_id)
    return _build_estimate(
        store,
        _item_count_from_order(order),
        _queue_orders(store, before_order=order),
        status=order.status,
    )
