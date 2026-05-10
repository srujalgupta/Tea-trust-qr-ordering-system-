import re

from app import create_app
from app.extensions import db
from app.models import MenuItem, Store
from app.services.order_service import create_order
from app.services.sample_data import seed_sample_data


def csrf_from(html):
    match = re.search(r'name="csrf-token" content="([^"]+)"', html)
    assert match
    return match.group(1)


def test_cart_wait_estimate_uses_cart_items_and_pending_orders():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        seed_sample_data(app.config)
        store = Store.query.filter_by(slug="store-1").one()
        menu_item = MenuItem.query.filter_by(store_id=store.id).first()
        store_id = store.id
        menu_item_id = menu_item.id

    client = app.test_client()
    cart_page = client.get("/cart?store=store-1")
    token = csrf_from(cart_page.get_data(as_text=True))

    first_estimate = client.post(
        "/api/v1/orders/wait-estimate",
        json={
            "store_id": store_id,
            "items": [{"menu_item_id": menu_item_id, "quantity": 1}],
        },
        headers={"X-CSRFToken": token},
    )
    assert first_estimate.status_code == 200
    assert first_estimate.json["cart_item_count"] == 1
    assert first_estimate.json["queue_order_count"] == 0

    with app.app_context():
        create_order(
            {
                "store_id": store_id,
                "payment_method": "cash",
                "items": [{"menu_item_id": menu_item_id, "quantity": 2}],
            },
            app.config,
        )

    queued_estimate = client.post(
        "/api/v1/orders/wait-estimate",
        json={
            "store_id": store_id,
            "items": [{"menu_item_id": menu_item_id, "quantity": 3}],
        },
        headers={"X-CSRFToken": token},
    )
    assert queued_estimate.status_code == 200
    assert queued_estimate.json["cart_item_count"] == 3
    assert queued_estimate.json["queue_order_count"] == 1
    assert queued_estimate.json["queue_item_count"] == 2
    assert (
        queued_estimate.json["estimated_wait_minutes_min"]
        > first_estimate.json["estimated_wait_minutes_min"]
    )
    assert queued_estimate.json["estimated_wait_label"].startswith("Estimated wait:")
