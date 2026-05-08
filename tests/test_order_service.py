import pytest

from app import create_app
from app.extensions import db
from app.models import MenuItem
from app.services.errors import ValidationError
from app.services.order_service import create_order
from app.services.sample_data import seed_sample_data


def test_order_rejects_items_from_inactive_categories():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        seed_sample_data(app.config)

        item = MenuItem.query.filter_by(name="Masala Tea (Full)").first()
        item.category.is_active = False
        db.session.commit()

        with pytest.raises(ValidationError, match="currently unavailable"):
            create_order(
                {
                    "payment_method": "cash",
                    "items": [{"menu_item_id": item.id, "quantity": 1}],
                },
                app.config,
            )
