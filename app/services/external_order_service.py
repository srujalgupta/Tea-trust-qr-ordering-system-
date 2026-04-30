import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .errors import NotFoundError, ValidationError


EXTERNAL_ORDER_STATUSES = ("pending", "preparing", "ready", "completed", "cancelled")
EXTERNAL_PLATFORMS = {
    "swiggy": "Swiggy",
    "zomato": "Zomato",
}


def _store_path(instance_path):
    path = Path(instance_path)
    path.mkdir(parents=True, exist_ok=True)
    return path / "external_orders.json"


def _read_orders(instance_path):
    path = _store_path(instance_path)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError("External order store is not valid JSON.") from exc
    if not isinstance(payload, list):
        raise ValidationError("External order store must contain a list.")
    return payload


def _write_orders(instance_path, orders):
    path = _store_path(instance_path)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(orders, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _money_value(value):
    try:
        amount = Decimal(str(value or "0")).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        raise ValidationError("total_amount must be a valid number.") from None
    if amount < 0:
        raise ValidationError("total_amount cannot be negative.")
    return float(amount)


def _clean_text(value, max_length=240):
    return (value or "").strip()[:max_length]


def _items_from_text(value):
    items = [
        line.strip(" -\t")
        for line in str(value or "").replace(",", "\n").splitlines()
        if line.strip(" -\t")
    ]
    if not items:
        raise ValidationError("items_text is required.")
    return items[:30]


def list_external_orders(instance_path):
    return sorted(
        _read_orders(instance_path),
        key=lambda order: order.get("created_at", ""),
        reverse=True,
    )


def create_external_order(instance_path, data):
    platform = _clean_text(data.get("platform"), 30).lower()
    if platform not in EXTERNAL_PLATFORMS:
        raise ValidationError("platform must be zomato or swiggy.")

    now = datetime.now(timezone.utc).isoformat()
    items = _items_from_text(data.get("items_text"))
    order = {
        "id": f"DO-{uuid.uuid4().hex[:8].upper()}",
        "platform": platform,
        "platform_label": EXTERNAL_PLATFORMS[platform],
        "platform_order_id": _clean_text(data.get("platform_order_id"), 80) or "Not shared",
        "customer_name": _clean_text(data.get("customer_name"), 120) or "Delivery customer",
        "customer_phone": _clean_text(data.get("customer_phone"), 30),
        "items": items,
        "items_text": "\n".join(items),
        "total_amount": _money_value(data.get("total_amount")),
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    orders = _read_orders(instance_path)
    orders.append(order)
    _write_orders(instance_path, orders)
    return order


def update_external_order(instance_path, order_id, data):
    status = _clean_text(data.get("status"), 30).lower()
    if status not in EXTERNAL_ORDER_STATUSES:
        raise ValidationError("Invalid external order status.")

    orders = _read_orders(instance_path)
    for order in orders:
        if str(order.get("id")) == str(order_id):
            order["status"] = status
            order["updated_at"] = datetime.now(timezone.utc).isoformat()
            _write_orders(instance_path, orders)
            return order
    raise NotFoundError("External order not found.")
