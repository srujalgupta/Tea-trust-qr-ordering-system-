from app.extensions import socketio
from .serializers import serialize_order


def emit_order_created(order):
    payload = serialize_order(order)
    socketio.emit("order_created", payload, room="admin_orders")
    socketio.emit("order_updated", payload, room=f"order_{order.id}")


def emit_order_updated(order):
    payload = serialize_order(order)
    socketio.emit("order_updated", payload, room="admin_orders")
    socketio.emit("order_updated", payload, room=f"order_{order.id}")
