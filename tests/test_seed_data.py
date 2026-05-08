from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import CafeTable, Category, MenuItem
from app.services.sample_data import seed_sample_data


def test_seed_data_preserves_admin_menu_and_table_changes():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        seed_sample_data(app.config)

        tea = MenuItem.query.filter_by(name="Masala Tea (Full)").first()
        tea.price = Decimal("44.00")
        tea.is_available = False
        tea.tags = "client edited"

        custom_category = Category(
            name="Client Specials",
            description="Owner-managed items",
            display_order=99,
            is_active=True,
        )
        db.session.add(custom_category)
        db.session.flush()
        db.session.add(
            MenuItem(
                category=custom_category,
                name="Rose Chai",
                description="Limited item",
                price=Decimal("88.00"),
                tags="special",
                is_available=True,
            )
        )

        added_table = CafeTable(
            table_number=20,
            label="Private Room",
            qr_slug="private-room",
            is_active=True,
        )
        disabled_table = CafeTable.query.filter_by(table_number=1).first()
        disabled_table.is_active = False
        db.session.add(added_table)
        db.session.commit()

        seed_sample_data(app.config)

        tea = MenuItem.query.filter_by(name="Masala Tea (Full)").first()
        assert tea.price == Decimal("44.00")
        assert tea.is_available is False
        assert tea.tags == "client edited"

        custom_category = Category.query.filter_by(name="Client Specials").first()
        assert custom_category.is_active is True
        assert MenuItem.query.filter_by(name="Rose Chai").first().is_available is True

        assert CafeTable.query.filter_by(table_number=20).first().is_active is True
        assert CafeTable.query.filter_by(table_number=1).first().is_active is False
