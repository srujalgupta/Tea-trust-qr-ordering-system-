from flask_socketio import join_room

from app.extensions import socketio


def register_socket_handlers():
    @socketio.on("customer_join")
    def customer_join(data):
        order_id = str((data or {}).get("order_id", "")).strip()
        if order_id.isdigit():
            join_room(f"order_{order_id}")

    @socketio.on("admin_join")
    def admin_join():
        join_room("admin_orders")
