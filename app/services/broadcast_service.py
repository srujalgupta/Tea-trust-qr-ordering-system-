from concurrent.futures import ThreadPoolExecutor, as_completed
from types import SimpleNamespace

from app.services.customer_service import list_customer_contacts
from app.services.errors import ValidationError
from app.services.notification_service import (
    send_broadcast_message,
    validate_broadcast_delivery,
)


def send_customer_broadcast(data, config):
    message = (data.get("message") or "").strip()
    if len(message) < 5:
        raise ValidationError("Broadcast message must be at least 5 characters.")
    if len(message) > 500:
        raise ValidationError("Broadcast message must be 500 characters or fewer.")

    validate_broadcast_delivery(config)

    contacts = [
        SimpleNamespace(id=contact.id, name=contact.name or "", phone=contact.phone)
        for contact in list_customer_contacts(marketing_only=True)
        if contact.phone
    ]
    sent = 0
    failed = 0
    modes = set()
    failures = []

    def send_one(contact):
        return send_broadcast_message(contact, message, config)

    max_workers = min(int(config.get("BROADCAST_SEND_WORKERS", 8)), len(contacts) or 1)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(send_one, contact): contact for contact in contacts}
        completed = as_completed(futures)
        for future in completed:
            contact = futures[future]
            try:
                result = future.result()
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
        "workers": max_workers,
        "failures": failures[:10],
    }
