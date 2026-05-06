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

    excessive_order = client.post(
        "/api/v1/orders",
        json={
            "payment_method": "cash",
            "customer_name": "Smoke Test",
            "items": [
                {"menu_item_id": first_item["id"], "quantity": 20},
                {"menu_item_id": first_item["id"], "quantity": 20},
            ],
        },
        headers={"X-CSRFToken": token},
    )
    assert excessive_order.status_code == 400
    assert "Quantity per item cannot exceed 25" in excessive_order.get_data(as_text=True)

    order = client.post(
        "/api/v1/orders",
        json={
            "payment_method": "cash",
            "customer_name": "Smoke Test",
            "customer_phone": "98765 43210",
            "marketing_opt_in": True,
            "items": [{"menu_item_id": first_item["id"], "quantity": 1}],
        },
        headers={"X-CSRFToken": token},
    )
    assert order.status_code == 201, order.get_data(as_text=True)
    order_id = order.json["id"]
    order_key = order.json["order_number"]
    assert order.json["token_number"] == 1
    assert order.json["payment_method"] == "cash"
    assert order.json["payment_status"] == "cash_pending"
    assert order.json["customer_phone"] == "9876543210"

    non_counter_order = client.post(
        "/api/v1/orders",
        json={
            "payment_method": "online",
            "customer_name": "Smoke Test",
            "items": [{"menu_item_id": first_item["id"], "quantity": 1}],
        },
        headers={"X-CSRFToken": token},
    )
    assert non_counter_order.status_code == 400
    assert "Only pay-at-counter orders are supported" in non_counter_order.get_data(as_text=True)

    status = client.get(f"/api/v1/orders/{order_id}?key={order_key}")
    assert status.status_code == 200
    assert status.json["status"] == "pending"

    missing_order_key = client.get(f"/api/v1/orders/{order_id}")
    assert missing_order_key.status_code == 404

    login = client.post(
        "/admin/login?next=https://example.com/phishing",
        data={
            "username": "admin",
            "password": "admin12345",
            "csrf_token": token,
        },
    )
    assert login.status_code in {200, 302}
    assert "example.com" not in (login.headers.get("Location") or "")

    admin_home = client.get("/admin/dashboard")
    assert admin_home.status_code == 200
    token = csrf_from(admin_home.get_data(as_text=True))

    customers = client.get("/api/v1/admin/customers?marketing_only=1")
    assert customers.status_code == 200
    assert customers.json[0]["name"] == "Smoke Test"
    assert customers.json[0]["phone"] == "9876543210"
    assert customers.json[0]["marketing_opt_in"] is True

    broadcast = client.post(
        "/api/v1/admin/broadcasts",
        json={"message": "Today special chai offer is live."},
        headers={"X-CSRFToken": token},
    )
    assert broadcast.status_code == 200, broadcast.get_data(as_text=True)
    assert broadcast.json["sent"] == 1
    assert broadcast.json["recipient_count"] == 1

    bad_category = client.post(
        "/api/v1/admin/categories",
        json={"name": "Broken", "display_order": "soon"},
        headers={"X-CSRFToken": token},
    )
    assert bad_category.status_code == 400

    bad_item = client.post(
        "/api/v1/admin/menu-items",
        json={"name": "Broken", "price": "10", "category_id": "later"},
        headers={"X-CSRFToken": token},
    )
    assert bad_item.status_code == 400

    completed = client.patch(
        f"/api/v1/admin/orders/{order_id}/status",
        json={"status": "completed"},
        headers={"X-CSRFToken": token},
    )
    assert completed.status_code == 200, completed.get_data(as_text=True)
    assert completed.json["payment_status"] == "paid"

    table = client.post(
        "/api/v1/admin/tables",
        json={"label": "Patio Table"},
        headers={"X-CSRFToken": token},
    )
    assert table.status_code == 201, table.get_data(as_text=True)
    assert table.json["table_number"] == 7
    assert table.json["qr_image_url"].startswith("/qr/table/")

    qr_image = client.get(table.json["qr_image_url"])
    assert qr_image.status_code == 200, qr_image.get_data(as_text=True)
    assert qr_image.mimetype == "image/png"

    staff = client.post(
        "/api/v1/admin/staff",
        json={
            "username": "kitchen",
            "password": "StaffTea2026!",
            "role": "kitchen",
        },
        headers={"X-CSRFToken": token},
    )
    assert staff.status_code == 201, staff.get_data(as_text=True)
    assert staff.json["role"] == "kitchen"

    logout = client.post("/admin/logout", data={"csrf_token": token})
    assert logout.status_code in {200, 302}

    login_page = client.get("/admin/login")
    assert login_page.status_code == 200
    token = csrf_from(login_page.get_data(as_text=True))

    kitchen_login = client.post(
        "/admin/login",
        data={
            "username": "kitchen",
            "password": "StaffTea2026!",
            "csrf_token": token,
        },
    )
    assert kitchen_login.status_code in {200, 302}

    kitchen_page = client.get("/admin/kitchen")
    assert kitchen_page.status_code == 200
    token = csrf_from(kitchen_page.get_data(as_text=True))

    menu_denied = client.get("/admin/menu")
    assert menu_denied.status_code == 403

    api_denied = client.post(
        "/api/v1/admin/menu-items",
        json={"name": "Blocked", "price": "10", "category_id": 1},
        headers={"X-CSRFToken": token},
    )
    assert api_denied.status_code == 403
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
