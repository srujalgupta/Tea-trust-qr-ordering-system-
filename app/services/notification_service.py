import json
import logging
from urllib import error as urllib_error
from urllib import request as urllib_request

from app.services.errors import ValidationError


logger = logging.getLogger(__name__)


def _truthy(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_config(value):
    return hasattr(value, "get") and not isinstance(value, (str, bytes))


def _notification_settings(config_or_webhook=None):
    if _is_config(config_or_webhook):
        config = config_or_webhook
        api_version = (config.get("WHATSAPP_CLOUD_API_VERSION") or "v25.0").strip()
        if api_version and not api_version.startswith("v"):
            api_version = f"v{api_version}"
        return {
            "environment": config.get("ENV_NAME", ""),
            "webhook_url": config.get("NOTIFICATION_WEBHOOK_URL", ""),
            "whatsapp_api_version": api_version or "v25.0",
            "whatsapp_phone_number_id": config.get("WHATSAPP_PHONE_NUMBER_ID", ""),
            "whatsapp_access_token": config.get("WHATSAPP_ACCESS_TOKEN", ""),
            "whatsapp_broadcast_template_name": config.get(
                "WHATSAPP_BROADCAST_TEMPLATE_NAME",
                "",
            ),
            "whatsapp_template_language": config.get("WHATSAPP_TEMPLATE_LANGUAGE", "en_US"),
            "whatsapp_default_country_code": config.get(
                "WHATSAPP_DEFAULT_COUNTRY_CODE",
                "91",
            ),
            "whatsapp_allow_freeform_text": _truthy(
                config.get("WHATSAPP_ALLOW_FREEFORM_TEXT", False),
            ),
        }

    return {
        "environment": "",
        "webhook_url": config_or_webhook or "",
        "whatsapp_api_version": "v25.0",
        "whatsapp_phone_number_id": "",
        "whatsapp_access_token": "",
        "whatsapp_broadcast_template_name": "",
        "whatsapp_template_language": "en_US",
        "whatsapp_default_country_code": "91",
        "whatsapp_allow_freeform_text": False,
    }


def _whatsapp_configured(settings):
    return bool(
        settings["whatsapp_access_token"]
        and settings["whatsapp_phone_number_id"]
    )


def validate_broadcast_delivery(config):
    settings = _notification_settings(config)
    if _whatsapp_configured(settings):
        if (
            not settings["whatsapp_broadcast_template_name"]
            and not settings["whatsapp_allow_freeform_text"]
        ):
            raise ValidationError(
                "WhatsApp broadcasts require an approved template. Set "
                "WHATSAPP_BROADCAST_TEMPLATE_NAME, or set "
                "WHATSAPP_ALLOW_FREEFORM_TEXT=true only for active 24-hour chats."
            )
        return

    if settings["webhook_url"]:
        return

    if settings["environment"] == "production":
        raise ValidationError(
            "Configure WhatsApp Cloud or NOTIFICATION_WEBHOOK_URL before sending broadcasts."
        )


def _post_json(url, payload, headers):
    request = urllib_request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=12) as response:
            body = response.read().decode("utf-8")
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                data = {"raw": body[:500]}
            return {
                "sent": 200 <= response.status < 300,
                "status": response.status,
                "response": data,
            }
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Provider returned HTTP {exc.code}: {detail}") from exc


def _whatsapp_recipient(phone, default_country_code):
    raw_phone = str(phone or "").strip()
    has_country_prefix = raw_phone.startswith("+")
    digits = "".join(character for character in raw_phone if character.isdigit())
    default_country_code = "".join(
        character for character in str(default_country_code or "") if character.isdigit()
    )
    if not digits:
        raise RuntimeError("Customer phone number is missing.")
    if not has_country_prefix and default_country_code and len(digits) == 10:
        digits = f"{default_country_code}{digits}"
    return digits


def _whatsapp_text_payload(recipient, message):
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message,
        },
    }


def _whatsapp_template_payload(recipient, template_name, language, message):
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language or "en_US"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": message,
                        },
                    ],
                },
            ],
        },
    }


def _send_whatsapp_broadcast(payload, settings):
    message = payload.get("message") or ""
    recipient = _whatsapp_recipient(
        payload.get("phone"),
        settings["whatsapp_default_country_code"],
    )
    template_name = settings["whatsapp_broadcast_template_name"]
    if template_name:
        provider_payload = _whatsapp_template_payload(
            recipient,
            template_name,
            settings["whatsapp_template_language"],
            message,
        )
    elif settings["whatsapp_allow_freeform_text"]:
        provider_payload = _whatsapp_text_payload(recipient, message)
    else:
        raise RuntimeError("WhatsApp broadcast template is not configured.")

    url = (
        "https://graph.facebook.com/"
        f"{settings['whatsapp_api_version']}/"
        f"{settings['whatsapp_phone_number_id']}/messages"
    )
    result = _post_json(
        url,
        provider_payload,
        {"Authorization": f"Bearer {settings['whatsapp_access_token']}"},
    )
    return {
        "mode": "whatsapp_cloud",
        "sent": result["sent"],
        "provider_status": result["status"],
        "provider_response": result["response"],
    }


def _send_webhook(payload, webhook_url):
    result = _post_json(webhook_url, payload, {})
    return {
        "mode": "webhook",
        "sent": result["sent"],
        "provider_status": result["status"],
        "provider_response": result["response"],
    }


def _send(payload, config_or_webhook=None):
    settings = _notification_settings(config_or_webhook)

    if payload.get("event") == "broadcast" and _whatsapp_configured(settings):
        return _send_whatsapp_broadcast(payload, settings)

    if not settings["webhook_url"]:
        logger.info("Notification mock: %s", payload)
        return {"mode": "mock", "sent": True, "payload": payload}

    return _send_webhook(payload, settings["webhook_url"])


def send_order_confirmation(order_data, config_or_webhook=None):
    return _send(
        {
            "channel": "whatsapp_simulation",
            "event": "order_confirmed",
            "phone": order_data.get("customer_phone"),
            "message": f"Order {order_data.get('order_number')} confirmed. Token {order_data.get('token_number')}.",
            "order": order_data,
        },
        config_or_webhook,
    )


def send_order_ready(order_data, config_or_webhook=None):
    return _send(
        {
            "channel": "whatsapp_simulation",
            "event": "order_ready",
            "phone": order_data.get("customer_phone"),
            "message": f"Token {order_data.get('token_number')} is ready for pickup.",
            "order": order_data,
        },
        config_or_webhook,
    )


def send_broadcast_message(contact, message, config_or_webhook=None):
    return _send(
        {
            "channel": "whatsapp",
            "event": "broadcast",
            "phone": contact.phone,
            "message": message,
            "customer": {
                "id": contact.id,
                "name": contact.name or "",
            },
        },
        config_or_webhook,
    )
