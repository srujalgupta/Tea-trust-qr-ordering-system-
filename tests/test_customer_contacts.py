import json
from types import SimpleNamespace

import pytest

from app import create_app
from app.extensions import db
from app.models import CustomerContact
from app.services.errors import ValidationError
from app.services.broadcast_service import send_customer_broadcast
from app.services.notification_service import (
    send_broadcast_message,
    validate_broadcast_delivery,
)
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


def test_production_broadcast_requires_delivery_provider():
    app = create_app("testing")
    app.config.update(
        ENV_NAME="production",
        NOTIFICATION_WEBHOOK_URL="",
        WHATSAPP_ACCESS_TOKEN="",
        WHATSAPP_PHONE_NUMBER_ID="",
    )

    with app.app_context():
        with pytest.raises(ValidationError, match="Configure WhatsApp Cloud"):
            send_customer_broadcast({"message": "Fresh tea offer is live today."}, app.config)


def test_broadcast_webhook_works_with_incomplete_whatsapp_config(monkeypatch):
    app = create_app("testing")
    app.config.update(
        NOTIFICATION_WEBHOOK_URL="https://example.test/notifications",
        WHATSAPP_ACCESS_TOKEN="test-token",
        WHATSAPP_PHONE_NUMBER_ID="123456",
        WHATSAPP_BROADCAST_TEMPLATE_NAME="",
    )
    sent_request = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return b'{"ok":true}'

    def fake_urlopen(request, timeout):
        sent_request["url"] = request.full_url
        sent_request["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.notification_service.urllib_request.urlopen",
        fake_urlopen,
    )

    validate_broadcast_delivery(app.config)
    result = send_broadcast_message(
        SimpleNamespace(id=1, name="Asha", phone="9876543210"),
        "Fresh tea offer is live today.",
        app.config,
    )

    assert result["sent"] is True
    assert result["mode"] == "webhook"
    assert sent_request["url"] == "https://example.test/notifications"
    assert sent_request["body"]["event"] == "broadcast"


def test_whatsapp_broadcast_uses_template_payload(monkeypatch):
    app = create_app("testing")
    app.config.update(
        WHATSAPP_ACCESS_TOKEN="test-token",
        WHATSAPP_PHONE_NUMBER_ID="123456",
        WHATSAPP_BROADCAST_TEMPLATE_NAME="cafe_broadcast",
        WHATSAPP_TEMPLATE_LANGUAGE="en_US",
        WHATSAPP_DEFAULT_COUNTRY_CODE="91",
    )
    sent_request = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return b'{"messages":[{"id":"wamid.test"}]}'

    def fake_urlopen(request, timeout):
        sent_request["url"] = request.full_url
        sent_request["body"] = json.loads(request.data.decode("utf-8"))
        sent_request["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.notification_service.urllib_request.urlopen",
        fake_urlopen,
    )

    result = send_broadcast_message(
        SimpleNamespace(id=1, name="Asha", phone="9876543210"),
        "Fresh tea offer is live today.",
        app.config,
    )

    assert result["sent"] is True
    assert result["mode"] == "whatsapp_cloud"
    assert sent_request["url"].endswith("/v25.0/123456/messages")
    assert sent_request["timeout"] == 12
    assert sent_request["body"]["to"] == "919876543210"
    assert sent_request["body"]["type"] == "template"
    assert sent_request["body"]["template"]["name"] == "cafe_broadcast"
    assert sent_request["body"]["template"]["components"][0]["parameters"][0]["text"] == (
        "Fresh tea offer is live today."
    )
