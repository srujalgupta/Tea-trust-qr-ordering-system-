import csv
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from io import StringIO

from flask import Blueprint, Response, current_app, jsonify, request
from flask_login import current_user

from app.services.auth_service import require_admin_api
from app.services.broadcast_service import send_customer_broadcast
from app.services.errors import ValidationError
from app.services.customer_service import list_customer_contacts
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
    create_order,
    get_order,
    list_orders,
    update_order_status,
    verify_customer_order_access,
)
from app.services.serializers import (
    serialize_category,
    serialize_customer_contact,
    serialize_menu_item,
    serialize_order,
    serialize_staff_profile,
    serialize_store,
    serialize_table,
)
from app.services.store_service import list_stores, store_from_request_args
from app.services.table_service import create_table, list_tables, update_table
from app.services.upload_service import save_menu_image
from app.services.user_service import (
    create_staff_profile,
    delete_staff_profile,
    list_staff_profiles,
    role_options_payload,
    update_staff_profile,
)


api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


def _json_body():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Request body must be valid JSON.")
    return data


def _selected_store():
    return store_from_request_args(request.args)


@api_bp.get("/health")
def api_health_check():
    return jsonify(build_health_payload(current_app)), 200


@api_bp.get("/stores")
def stores():
    include_inactive = (
        current_user.is_authenticated
        and current_user.is_admin
        and request.args.get("include_inactive") == "1"
    )
    return jsonify([serialize_store(store) for store in list_stores(include_inactive)])


@api_bp.get("/menu")
def menu_items():
    store = _selected_store()
    category_id = request.args.get("category_id", type=int)
    search = request.args.get("q", "")
    include_unavailable = (
        current_user.is_authenticated
        and current_user.is_admin
        and current_user.can("menu:manage")
        and request.args.get("include_unavailable") == "1"
    )
    return jsonify(menu_payload(category_id, search, include_unavailable, store=store))


@api_bp.post("/orders")
def create_customer_order():
    order, payment = create_order(_json_body(), current_app.config)
    payload = serialize_order(order)
    if payment:
        payload["payment"] = payment
    return jsonify(payload), 201


@api_bp.get("/orders/<int:order_id>")
def get_customer_order(order_id):
    order = get_order(order_id)
    if not (current_user.is_authenticated and current_user.is_admin):
        verify_customer_order_access(order, request.args.get("key"))
    return jsonify(serialize_order(order))


@api_bp.get("/admin/orders")
def admin_orders():
    require_admin_api("orders:view")
    store = _selected_store()
    status = request.args.get("status") or None
    return jsonify([serialize_order(order) for order in list_orders(status, store=store)])


@api_bp.patch("/admin/orders/<int:order_id>/status")
def admin_update_order_status(order_id):
    require_admin_api("orders:update")
    data = _json_body()
    order = update_order_status(
        order_id,
        data.get("status"),
        current_app.config,
        cancellation_reason=data.get("cancellation_reason"),
    )
    return jsonify(serialize_order(order))


def _admin_orders_for_range(days, store):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [
        order for order in list_orders(store=store)
        if order.created_at and _aware_datetime(order.created_at) >= cutoff
    ]


def _active_revenue_order(order):
    return order.status != "cancelled" and order.payment_status in {"cash_pending", "paid"}


def _aware_datetime(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@api_bp.get("/admin/analytics")
def admin_analytics():
    require_admin_api("analytics:view")
    store = _selected_store()
    days = max(1, min(request.args.get("days", 7, type=int), 365))
    orders = _admin_orders_for_range(days, store)
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
    require_admin_api("staff:manage")
    store = _selected_store()
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
    for order in list_orders(store=store):
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
    require_admin_api("staff:manage")
    store = _selected_store()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["category", "name", "price", "available", "veg", "bestseller", "tags"])
    for item in list_menu_items(include_unavailable=True, store=store):
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


@api_bp.get("/admin/customers")
def admin_customer_contacts():
    require_admin_api("staff:manage")
    store = _selected_store()
    marketing_only = request.args.get("marketing_only") == "1"
    return jsonify([
        serialize_customer_contact(contact)
        for contact in list_customer_contacts(marketing_only=marketing_only, store=store)
    ])


@api_bp.get("/admin/export/customers.csv")
def admin_customers_export():
    require_admin_api("staff:manage")
    store = _selected_store()
    marketing_only = request.args.get("marketing_only") == "1"
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "name",
        "phone",
        "marketing_opt_in",
        "order_count",
        "total_spend",
        "last_order_at",
    ])
    for contact in list_customer_contacts(marketing_only=marketing_only, store=store):
        writer.writerow([
            contact.name or "",
            contact.phone,
            "yes" if contact.marketing_opt_in else "no",
            contact.order_count,
            contact.total_spend,
            contact.last_order_at.isoformat() if contact.last_order_at else "",
        ])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=customer-contacts.csv"},
    )


@api_bp.post("/admin/broadcasts")
def admin_send_broadcast():
    require_admin_api("staff:manage")
    store = _selected_store()
    return jsonify(send_customer_broadcast(_json_body(), current_app.config, store=store))


@api_bp.get("/admin/staff")
def admin_staff_profiles():
    require_admin_api("staff:manage")
    return jsonify({
        "roles": role_options_payload(),
        "staff": [serialize_staff_profile(user) for user in list_staff_profiles()],
    })


@api_bp.post("/admin/staff")
def admin_create_staff_profile():
    require_admin_api("staff:manage")
    return jsonify(serialize_staff_profile(create_staff_profile(_json_body()))), 201


@api_bp.patch("/admin/staff/<int:user_id>")
def admin_update_staff_profile(user_id):
    require_admin_api("staff:manage")
    user = update_staff_profile(user_id, _json_body(), actor=current_user)
    return jsonify(serialize_staff_profile(user))


@api_bp.delete("/admin/staff/<int:user_id>")
def admin_delete_staff_profile(user_id):
    require_admin_api("staff:manage")
    delete_staff_profile(user_id, actor=current_user)
    return "", 204


@api_bp.post("/admin/categories")
def admin_create_category():
    require_admin_api("menu:manage")
    store = _selected_store()
    return jsonify(serialize_category(create_category(_json_body(), store=store))), 201


@api_bp.patch("/admin/categories/<int:category_id>")
def admin_update_category(category_id):
    require_admin_api("menu:manage")
    store = _selected_store()
    return jsonify(serialize_category(update_category(category_id, _json_body(), store=store)))


@api_bp.post("/admin/menu-items")
def admin_create_menu_item():
    require_admin_api("menu:manage")
    store = _selected_store()
    return jsonify(serialize_menu_item(create_menu_item(_json_body(), store=store))), 201


@api_bp.patch("/admin/menu-items/<int:item_id>")
def admin_update_menu_item(item_id):
    require_admin_api("menu:manage")
    store = _selected_store()
    return jsonify(serialize_menu_item(update_menu_item(item_id, _json_body(), store=store)))


@api_bp.delete("/admin/menu-items/<int:item_id>")
def admin_delete_menu_item(item_id):
    require_admin_api("menu:manage")
    delete_menu_item(item_id)
    return jsonify({"deleted": True})


@api_bp.post("/admin/menu-items/<int:item_id>/image")
def admin_upload_menu_image(item_id):
    require_admin_api("menu:manage")
    filename = save_menu_image(
        request.files.get("image"),
        current_app.config["UPLOAD_FOLDER"],
        current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
    )
    return jsonify(serialize_menu_item(set_menu_item_image(item_id, filename)))


@api_bp.get("/admin/tables")
def admin_tables():
    require_admin_api("tables:manage")
    store = _selected_store()
    include_inactive = request.args.get("include_inactive") == "1"
    return jsonify(
        [
            serialize_table(table)
            for table in list_tables(include_inactive=include_inactive, store=store)
        ]
    )


@api_bp.post("/admin/tables")
def admin_create_table():
    require_admin_api("tables:manage")
    store = _selected_store()
    return jsonify(serialize_table(create_table(_json_body(), store=store))), 201


@api_bp.patch("/admin/tables/<int:table_id>")
def admin_update_table(table_id):
    require_admin_api("tables:manage")
    store = _selected_store()
    return jsonify(serialize_table(update_table(table_id, _json_body(), store=store)))
