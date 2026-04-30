import csv
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from io import StringIO

from flask import Blueprint, Response, current_app, jsonify, request
from flask_login import current_user

from app.extensions import socketio
from app.services.errors import ForbiddenError, ValidationError
from app.services.external_order_service import (
    create_external_order,
    list_external_orders,
    update_external_order,
)
from app.services.health_service import build_health_payload
from app.services.menu_service import (
    create_category,
    create_menu_item,
    delete_menu_item,
    list_menu_items,
    menu_payload,
    set_menu_item_image,
    update_category,
    update_menu_item,
)
from app.services.order_service import (
    confirm_payment,
    confirm_payment_from_webhook,
    create_order,
    get_order,
    list_orders,
    update_order_status,
)
from app.services.payment_service import apply_webhook_event
from app.services.serializers import (
    serialize_category,
    serialize_menu_item,
    serialize_order,
    serialize_table,
)
from app.services.table_service import create_table, list_tables, update_table
from app.services.upload_service import save_menu_image


api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


def _json_body():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Request body must be valid JSON.")
    return data


def _require_admin_api():
    if not current_user.is_authenticated or not current_user.is_admin:
        raise ForbiddenError("Admin authentication is required.")


@api_bp.get("/health")
def api_health_check():
    return jsonify(build_health_payload(current_app)), 200


@api_bp.get("/menu")
def menu_items():
    category_id = request.args.get("category_id", type=int)
    search = request.args.get("q", "")
    include_unavailable = (
        current_user.is_authenticated
        and current_user.is_admin
        and request.args.get("include_unavailable") == "1"
    )
    return jsonify(menu_payload(category_id, search, include_unavailable))


@api_bp.post("/orders")
def create_customer_order():
    order, payment = create_order(_json_body(), current_app.config)
    payload = serialize_order(order)
    if payment:
        payload["payment"] = payment
    return jsonify(payload), 201


@api_bp.get("/orders/<int:order_id>")
def get_customer_order(order_id):
    return jsonify(serialize_order(get_order(order_id)))


@api_bp.post("/payments/razorpay/verify")
def verify_razorpay_payment():
    order = confirm_payment(_json_body(), current_app.config)
    return jsonify(serialize_order(order))


@api_bp.post("/payments/razorpay/webhook")
def razorpay_webhook():
    raw_body = request.get_data()
    signature = request.headers.get("X-Razorpay-Signature", "")
    event_id = request.headers.get("X-Razorpay-Event-Id", "")
    result = apply_webhook_event(raw_body, signature, event_id, current_app.config)
    order = confirm_payment_from_webhook(result, current_app.config)
    if order:
        return jsonify({"status": "ok", "order": serialize_order(order)})
    return jsonify({"status": "ok", "result": result})


@api_bp.get("/admin/orders")
def admin_orders():
    _require_admin_api()
    status = request.args.get("status") or None
    return jsonify([serialize_order(order) for order in list_orders(status)])


@api_bp.patch("/admin/orders/<int:order_id>/status")
def admin_update_order_status(order_id):
    _require_admin_api()
    data = _json_body()
    order = update_order_status(
        order_id,
        data.get("status"),
        current_app.config,
        cancellation_reason=data.get("cancellation_reason"),
    )
    return jsonify(serialize_order(order))


@api_bp.get("/admin/external-orders")
def admin_external_orders():
    _require_admin_api()
    return jsonify(list_external_orders(current_app.instance_path))


@api_bp.post("/admin/external-orders")
def admin_create_external_order():
    _require_admin_api()
    order = create_external_order(current_app.instance_path, _json_body())
    socketio.emit("external_order_created", order, room="admin_orders")
    return jsonify(order), 201


@api_bp.patch("/admin/external-orders/<order_id>")
def admin_update_external_order(order_id):
    _require_admin_api()
    order = update_external_order(current_app.instance_path, order_id, _json_body())
    socketio.emit("external_order_updated", order, room="admin_orders")
    return jsonify(order)


def _admin_orders_for_range(days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [
        order for order in list_orders()
        if order.created_at and _aware_datetime(order.created_at) >= cutoff
    ]


def _active_revenue_order(order):
    return order.status != "cancelled" and order.payment_status not in {"created", "failed"}


def _aware_datetime(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@api_bp.get("/admin/analytics")
def admin_analytics():
    _require_admin_api()
    days = max(1, min(request.args.get("days", 7, type=int), 365))
    orders = _admin_orders_for_range(days)
    revenue_orders = [order for order in orders if _active_revenue_order(order)]
    revenue = sum((order.total_amount for order in revenue_orders), start=0)

    daily = {}
    today = datetime.now(timezone.utc).date()
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        daily[day.isoformat()] = {"date": day.isoformat(), "revenue": 0.0, "orders": 0}

    hourly = {hour: 0 for hour in range(24)}
    status_counts = Counter()
    top_items = defaultdict(lambda: {"name": "", "quantity": 0, "revenue": 0.0})
    prep_minutes = []

    for order in orders:
        created_at = _aware_datetime(order.created_at)
        key = created_at.date().isoformat()
        if key in daily:
            daily[key]["orders"] += 1
            if _active_revenue_order(order):
                daily[key]["revenue"] += float(order.total_amount or 0)
        hourly[created_at.hour] += 1
        status_counts[order.status] += 1
        if order.status == "completed" and order.updated_at and order.created_at:
            prep_minutes.append(max(0, (_aware_datetime(order.updated_at) - created_at).total_seconds() / 60))
        if _active_revenue_order(order):
            for item in order.items:
                bucket = top_items[item.item_name]
                bucket["name"] = item.item_name
                bucket["quantity"] += int(item.quantity or 0)
                bucket["revenue"] += float(item.line_total or 0)

    peak_hour = max(hourly.items(), key=lambda pair: pair[1])[0] if orders else None
    top_items_payload = sorted(
        top_items.values(),
        key=lambda item: (item["quantity"], item["revenue"]),
        reverse=True,
    )[:10]

    return jsonify({
        "days": days,
        "order_count": len(orders),
        "revenue": float(revenue or 0),
        "average_order_value": float(revenue / len(revenue_orders)) if revenue_orders else 0,
        "peak_hour": peak_hour,
        "average_prep_minutes": round(sum(prep_minutes) / len(prep_minutes), 1) if prep_minutes else None,
        "daily": list(daily.values()),
        "hourly": [{"hour": hour, "orders": count} for hour, count in hourly.items()],
        "status_counts": dict(status_counts),
        "top_items": top_items_payload,
    })


@api_bp.get("/admin/export/orders.csv")
def admin_orders_export():
    _require_admin_api()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "order_number",
        "created_at",
        "table",
        "customer_name",
        "customer_phone",
        "status",
        "payment_method",
        "payment_status",
        "total_amount",
        "items",
        "notes",
    ])
    for order in list_orders():
        writer.writerow([
            order.order_number,
            order.created_at.isoformat() if order.created_at else "",
            order.table.label if order.table and order.table.label else "",
            order.customer_name or "",
            order.customer_phone or "",
            order.status,
            order.payment_method,
            order.payment_status,
            order.total_amount,
            "; ".join(f"{item.item_name} x {item.quantity}" for item in order.items),
            order.notes or "",
        ])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders.csv"},
    )


@api_bp.get("/admin/export/menu.csv")
def admin_menu_export():
    _require_admin_api()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["category", "name", "price", "available", "veg", "bestseller", "tags"])
    for item in list_menu_items(include_unavailable=True):
        writer.writerow([
            item.category.name if item.category else "",
            item.name,
            item.price,
            item.is_available,
            item.is_veg,
            item.is_bestseller,
            item.tags or "",
        ])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=menu.csv"},
    )


@api_bp.post("/admin/categories")
def admin_create_category():
    _require_admin_api()
    return jsonify(serialize_category(create_category(_json_body()))), 201


@api_bp.patch("/admin/categories/<int:category_id>")
def admin_update_category(category_id):
    _require_admin_api()
    return jsonify(serialize_category(update_category(category_id, _json_body())))


@api_bp.post("/admin/menu-items")
def admin_create_menu_item():
    _require_admin_api()
    return jsonify(serialize_menu_item(create_menu_item(_json_body()))), 201


@api_bp.patch("/admin/menu-items/<int:item_id>")
def admin_update_menu_item(item_id):
    _require_admin_api()
    return jsonify(serialize_menu_item(update_menu_item(item_id, _json_body())))


@api_bp.delete("/admin/menu-items/<int:item_id>")
def admin_delete_menu_item(item_id):
    _require_admin_api()
    delete_menu_item(item_id)
    return jsonify({"deleted": True})


@api_bp.post("/admin/menu-items/<int:item_id>/image")
def admin_upload_menu_image(item_id):
    _require_admin_api()
    filename = save_menu_image(
        request.files.get("image"),
        current_app.config["UPLOAD_FOLDER"],
        current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
    )
    return jsonify(serialize_menu_item(set_menu_item_image(item_id, filename)))


@api_bp.get("/admin/tables")
def admin_tables():
    _require_admin_api()
    include_inactive = request.args.get("include_inactive") == "1"
    return jsonify(
        [serialize_table(table) for table in list_tables(include_inactive=include_inactive)]
    )


@api_bp.post("/admin/tables")
def admin_create_table():
    _require_admin_api()
    return jsonify(serialize_table(create_table(_json_body()))), 201


@api_bp.patch("/admin/tables/<int:table_id>")
def admin_update_table(table_id):
    _require_admin_api()
    return jsonify(serialize_table(update_table(table_id, _json_body())))
