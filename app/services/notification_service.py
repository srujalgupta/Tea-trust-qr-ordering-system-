import json
import logging
from urllib import request as urllib_request


logger = logging.getLogger(__name__)


def _send(payload, webhook_url=None):
    if not webhook_url:
        logger.info("Notification mock: %s", payload)
        return {"mode": "mock", "sent": True, "payload": payload}

    req = urllib_request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=5) as response:
        return {"mode": "webhook", "sent": 200 <= response.status < 300}


def send_order_confirmation(order_data, webhook_url=None):
    return _send(
        {
            "channel": "whatsapp_simulation",
            "event": "order_confirmed",
            "phone": order_data.get("customer_phone"),
            "message": f"Order {order_data.get('order_number')} confirmed. Token {order_data.get('token_number')}.",
            "order": order_data,
        },
        webhook_url,
    )


def send_order_ready(order_data, webhook_url=None):
    return _send(
        {
            "channel": "whatsapp_simulation",
            "event": "order_ready",
            "phone": order_data.get("customer_phone"),
            "message": f"Token {order_data.get('token_number')} is ready for pickup.",
            "order": order_data,
        },
        webhook_url,
    )
