from flask_socketio import join_room

from app.extensions import socketio
from app.services.errors import AppError
from app.services.order_service import get_order, verify_customer_order_access


def register_socket_handlers():
    @socketio.on("customer_join")
    def customer_join(data):
        order_id = str((data or {}).get("order_id", "")).strip()
        order_key = str((data or {}).get("order_key", "")).strip()
        if not order_id.isdigit():
            return
        try:
            order = get_order(int(order_id))
            verify_customer_order_access(order, order_key)
        except AppError:
            return
        join_room(f"order_{order_id}")

    @socketio.on("admin_join")
    def admin_join(data=None):
        store_id = str((data or {}).get("store_id", "")).strip()
        if store_id.isdigit():
            join_room(f"admin_orders_store_{store_id}")
            return
        join_room("admin_orders")
