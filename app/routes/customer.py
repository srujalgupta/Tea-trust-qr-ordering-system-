from flask import Blueprint, current_app, render_template, request

from app.services.order_service import get_order
from app.services.table_service import get_table


customer_bp = Blueprint("customer", __name__)


@customer_bp.get("/menu")
def menu():
    table = None
    table_id = request.args.get("table")
    if table_id:
        table = get_table(table_id, require_active=True)

    return render_template(
        "customer/menu.html",
        table=table,
        banner_video_url=current_app.config["CAFE_BANNER_VIDEO_URL"],
        banner_poster_url=current_app.config["CAFE_BANNER_POSTER_URL"],
        live_stream_url=current_app.config["CAFE_LIVE_STREAM_EMBED_URL"],
    )


@customer_bp.get("/cart")
def cart():
    table = None
    table_id = request.args.get("table")
    if table_id:
        table = get_table(table_id, require_active=True)

    return render_template("customer/cart.html", table=table, checkout_mode=False)


@customer_bp.get("/checkout")
def checkout():
    table = None
    table_id = request.args.get("table")
    if table_id:
        table = get_table(table_id, require_active=True)

    return render_template("customer/cart.html", table=table, checkout_mode=True)


@customer_bp.get("/order/<int:order_id>")
def order_status(order_id):
    order = get_order(order_id)
    return render_template("customer/order_status.html", order=order, table=order.table)
