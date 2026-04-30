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
    assert "checkout.razorpay.com" not in checkout_page.get_data(as_text=True)

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
    assert order.json["payment_method"] == "cash"
    assert order.json["payment_status"] == "cash_pending"

    online_order = client.post(
        "/api/v1/orders",
        json={
            "payment_method": "razorpay",
            "customer_name": "Smoke Test",
            "items": [{"menu_item_id": first_item["id"], "quantity": 1}],
        },
        headers={"X-CSRFToken": token},
    )
    assert online_order.status_code == 400
    assert "Online payment is disabled" in online_order.get_data(as_text=True)

    status = client.get(f"/api/v1/orders/{order_id}")
    assert status.status_code == 200
    assert status.json["status"] == "pending"

    login = client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "admin12345",
            "csrf_token": token,
        },
    )
    assert login.status_code in {200, 302}

    completed = client.patch(
        f"/api/v1/admin/orders/{order_id}/status",
        json={"status": "completed"},
        headers={"X-CSRFToken": token},
    )
    assert completed.status_code == 200, completed.get_data(as_text=True)
    assert completed.json["payment_status"] == "paid"

    external = client.post(
        "/api/v1/admin/external-orders",
        json={
            "platform": "swiggy",
            "platform_order_id": "SWG-1001",
            "customer_name": "Delivery Guest",
            "total_amount": "249",
            "items_text": "Masala chai\nCheese sandwich",
        },
        headers={"X-CSRFToken": token},
    )
    assert external.status_code == 201, external.get_data(as_text=True)
    assert external.json["platform_label"] == "Swiggy"

    external_list = client.get("/api/v1/admin/external-orders")
    assert external_list.status_code == 200
    assert any(row["platform_order_id"] == "SWG-1001" for row in external_list.json)
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
