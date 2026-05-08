from app import create_app
from app.extensions import db
from app.models import MenuItem
from app.services.menu_service import delete_menu_item
from app.services.order_service import create_order
from app.services.sample_data import seed_sample_data


def test_delete_menu_item_with_order_history_hides_item():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        seed_sample_data(app.config)

        item = MenuItem.query.filter_by(name="Masala Tea (Full)").first()
        create_order(
            {
                "payment_method": "cash",
                "items": [{"menu_item_id": item.id, "quantity": 1}],
            },
            app.config,
        )

        delete_menu_item(item.id)

        item = db.session.get(MenuItem, item.id)
        assert item is not None
        assert item.is_available is False
