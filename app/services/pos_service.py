import json
import logging
from urllib import request as urllib_request


logger = logging.getLogger(__name__)


def send_order_to_pos(order_data, webhook_url=None):
    if not webhook_url:
        logger.info("POS mock accepted order %s", order_data.get("order_number"))
        return {"mode": "mock", "sent": True}

    payload = json.dumps(order_data).encode("utf-8")
    req = urllib_request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=5) as response:
        return {
            "mode": "webhook",
            "sent": 200 <= response.status < 300,
            "status_code": response.status,
        }
