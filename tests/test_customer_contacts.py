from app import create_app
from app.extensions import db
from app.models import CustomerContact
from app.services.broadcast_service import send_customer_broadcast
from app.services.order_service import create_order
from app.services.sample_data import seed_sample_data


def test_customer_contact_is_saved_and_updated_from_orders():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        seed_sample_data(app.config)
        menu_item_id = 1

        create_order(
            {
                "payment_method": "cash",
                "customer_name": "Asha",
                "customer_phone": "+91 98765 43210",
                "marketing_opt_in": True,
                "items": [{"menu_item_id": menu_item_id, "quantity": 1}],
            },
            app.config,
        )
        create_order(
            {
                "payment_method": "cash",
                "customer_name": "Asha Patel",
                "customer_phone": "+919876543210",
                "items": [{"menu_item_id": menu_item_id, "quantity": 2}],
            },
            app.config,
        )

        contacts = CustomerContact.query.all()
        assert len(contacts) == 1
        assert contacts[0].name == "Asha Patel"
        assert contacts[0].phone == "+919876543210"
        assert contacts[0].marketing_opt_in is True
        assert contacts[0].order_count == 2


def test_broadcast_sends_only_to_opted_in_contacts():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        seed_sample_data(app.config)

        create_order(
            {
                "payment_method": "cash",
                "customer_name": "Asha",
                "customer_phone": "9876543210",
                "marketing_opt_in": True,
                "items": [{"menu_item_id": 1, "quantity": 1}],
            },
            app.config,
        )
        create_order(
            {
                "payment_method": "cash",
                "customer_name": "No Broadcast",
                "customer_phone": "9123456780",
                "items": [{"menu_item_id": 1, "quantity": 1}],
            },
            app.config,
        )

        result = send_customer_broadcast(
            {"message": "Fresh tea offer is live today."},
            app.config,
        )

        assert result["recipient_count"] == 1
        assert result["sent"] == 1
        assert result["failed"] == 0
