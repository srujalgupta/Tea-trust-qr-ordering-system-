from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import CafeTable, MenuItem, Store
from app.services.menu_service import menu_payload
from app.services.order_service import create_order, list_orders
from app.services.sample_data import seed_sample_data
from app.services.user_service import create_staff_profile


def csrf_from(html):
    import re

    match = re.search(r'name="csrf-token" content="([^"]+)"', html)
    assert match
    return match.group(1)


def test_seeded_stores_keep_menus_tables_and_orders_separate():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        seed_sample_data(app.config)

        store_1 = Store.query.filter_by(slug="store-1").first()
        store_2 = Store.query.filter_by(slug="store-2").first()
        store_2_id = store_2.id
        assert store_1 is not None
        assert store_2 is not None

        store_1_table = CafeTable.query.filter_by(store_id=store_1.id, table_number=1).first()
        store_2_table = CafeTable.query.filter_by(store_id=store_2.id, table_number=1).first()
        assert store_1_table.id != store_2_table.id

        store_1_tea = MenuItem.query.filter_by(
            store_id=store_1.id,
            name="Masala Tea (Full)",
        ).first()
        store_2_tea = MenuItem.query.filter_by(
            store_id=store_2.id,
            name="Masala Tea (Full)",
        ).first()
        assert store_1_tea.id != store_2_tea.id

        store_2_tea.price = Decimal("55.00")
        db.session.commit()

        store_1_menu = menu_payload(store=store_1)
        store_2_menu = menu_payload(store=store_2)
        store_1_payload_tea = next(
            item for item in store_1_menu["items"] if item["name"] == "Masala Tea (Full)"
        )
        store_2_payload_tea = next(
            item for item in store_2_menu["items"] if item["name"] == "Masala Tea (Full)"
        )
        assert store_1_payload_tea["price"] == 40.0
        assert store_2_payload_tea["price"] == 55.0

        order, _ = create_order(
            {
                "store_id": store_2_id,
                "table_id": store_2_table.id,
                "payment_method": "cash",
                "items": [{"menu_item_id": store_2_tea.id, "quantity": 1}],
            },
            app.config,
        )

        assert list_orders(store=store_1) == []
        assert [store_order.id for store_order in list_orders(store=store_2)] == [order.id]


def test_store_locked_staff_cannot_access_other_store_orders():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        seed_sample_data(app.config)

        store_1 = Store.query.filter_by(slug="store-1").first()
        store_2 = Store.query.filter_by(slug="store-2").first()
        store_2_id = store_2.id
        store_1_item = MenuItem.query.filter_by(store_id=store_1.id).first()
        store_1_table = CafeTable.query.filter_by(store_id=store_1.id, table_number=1).first()
        store_2_item = MenuItem.query.filter_by(store_id=store_2.id).first()
        store_2_table = CafeTable.query.filter_by(store_id=store_2.id, table_number=1).first()

        create_order(
            {
                "store_id": store_1.id,
                "table_id": store_1_table.id,
                "payment_method": "cash",
                "items": [{"menu_item_id": store_1_item.id, "quantity": 1}],
            },
            app.config,
        )
        create_order(
            {
                "store_id": store_2.id,
                "table_id": store_2_table.id,
                "payment_method": "cash",
                "items": [{"menu_item_id": store_2_item.id, "quantity": 1}],
            },
            app.config,
        )
        create_staff_profile(
            {
                "username": "store2kitchen",
                "password": "StoreTwoKitchen2026!",
                "role": "kitchen",
                "store_id": store_2_id,
            }
        )

    client = app.test_client()
    login_page = client.get("/admin/login")
    token = csrf_from(login_page.get_data(as_text=True))
    login = client.post(
        "/admin/login",
        data={
            "username": "store2kitchen",
            "password": "StoreTwoKitchen2026!",
            "csrf_token": token,
        },
    )
    assert login.status_code in {200, 302}

    denied = client.get("/api/v1/admin/orders?store=store-1")
    assert denied.status_code == 403

    allowed = client.get("/api/v1/admin/orders?store=store-2")
    assert allowed.status_code == 200
    assert len(allowed.json) == 1
    assert allowed.json[0]["store_id"] == store_2_id
