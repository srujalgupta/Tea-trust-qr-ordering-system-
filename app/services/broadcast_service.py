from app.services.customer_service import list_customer_contacts
from app.services.errors import ValidationError
from app.services.notification_service import send_broadcast_message


def send_customer_broadcast(data, config):
    message = (data.get("message") or "").strip()
    if len(message) < 5:
        raise ValidationError("Broadcast message must be at least 5 characters.")
    if len(message) > 500:
        raise ValidationError("Broadcast message must be 500 characters or fewer.")

    contacts = [
        contact for contact in list_customer_contacts(marketing_only=True)
        if contact.phone
    ]
    sent = 0
    failed = 0
    modes = set()
    failures = []

    for contact in contacts:
        try:
            result = send_broadcast_message(
                contact,
                message,
                config.get("NOTIFICATION_WEBHOOK_URL"),
            )
        except Exception as exc:
            failed += 1
            failures.append({"phone": contact.phone, "error": str(exc)[:160]})
            continue

        modes.add(result.get("mode", "unknown"))
        if result.get("sent"):
            sent += 1
        else:
            failed += 1
            failures.append({"phone": contact.phone, "error": "Provider rejected the message."})

    return {
        "recipient_count": len(contacts),
        "sent": sent,
        "failed": failed,
        "mode": ", ".join(sorted(modes)) if modes else "none",
        "failures": failures[:10],
    }
