import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.extensions import db
from app.services.sample_data import seed_sample_data


def csrf_from(html):
    match = re.search(r'name="csrf-token" content="([^"]+)"', html)
    if not match:
        raise RuntimeError("CSRF token was not found in HTML.")
    return match.group(1)


def main():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        seed_sample_data(app.config)

    client = app.test_client()
    menu_page = client.get("/menu")
    assert menu_page.status_code == 200
    token = csrf_from(menu_page.get_data(as_text=True))

    cart_page = client.get("/cart")
    assert cart_page.status_code == 200

    checkout_page = client.get("/checkout")
    assert checkout_page.status_code == 200

    menu = client.get("/api/v1/menu")
    assert menu.status_code == 200
    first_item = menu.json["items"][0]

    order = client.post(
        "/api/v1/orders",
        json={
            "payment_method": "cash",
            "customer_name": "Smoke Test",
            "items": [{"menu_item_id": first_item["id"], "quantity": 1}],
        },
        headers={"X-CSRFToken": token},
    )
    assert order.status_code == 201, order.get_data(as_text=True)
    order_id = order.json["id"]
    assert order.json["token_number"] == 1

    status = client.get(f"/api/v1/orders/{order_id}")
    assert status.status_code == 200
    assert status.json["status"] == "pending"
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
