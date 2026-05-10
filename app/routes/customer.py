from flask import Blueprint, current_app, render_template, request

from app.services.order_service import get_order, verify_customer_order_access
from app.services.table_service import get_table
from app.services.store_service import get_store
from app.services.wait_time_service import estimate_wait_for_order


customer_bp = Blueprint("customer", __name__)


def _store_and_table_from_request():
    table = None
    table_id = request.args.get("table")
    if table_id:
        table = get_table(table_id, require_active=True)
        return table.store, table

    store = get_store(request.args.get("store") or request.args.get("store_id"))
    return store, table


@customer_bp.get("/menu")
def menu():
    store, table = _store_and_table_from_request()

    return render_template(
        "customer/menu.html",
        store=store,
        table=table,
        banner_video_url=current_app.config["CAFE_BANNER_VIDEO_URL"],
        banner_poster_url=current_app.config["CAFE_BANNER_POSTER_URL"],
        live_stream_url=current_app.config["CAFE_LIVE_STREAM_EMBED_URL"],
    )


@customer_bp.get("/cart")
def cart():
    store, table = _store_and_table_from_request()

    return render_template("customer/cart.html", store=store, table=table, checkout_mode=False)


@customer_bp.get("/checkout")
def checkout():
    store, table = _store_and_table_from_request()

    return render_template("customer/cart.html", store=store, table=table, checkout_mode=True)


@customer_bp.get("/order/<int:order_id>")
def order_status(order_id):
    order = get_order(order_id)
    verify_customer_order_access(order, request.args.get("key"))
    return render_template(
        "customer/order_status.html",
        order=order,
        wait_estimate=estimate_wait_for_order(order),
        store=order.store,
        table=order.table,
    )
