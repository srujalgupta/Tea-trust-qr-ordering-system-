from decimal import Decimal


def money_to_float(value):
    if value is None:
        return 0.0
    return float(Decimal(value).quantize(Decimal("0.01")))


def serialize_store(store):
    return {
        "id": store.id,
        "name": store.name,
        "slug": store.slug,
        "address": store.address or "",
        "phone": store.phone or "",
        "is_active": store.is_active,
    }


def serialize_category(category):
    return {
        "id": category.id,
        "store_id": category.store_id,
        "name": category.name,
        "description": category.description,
        "display_order": category.display_order,
        "is_active": category.is_active,
    }


def serialize_menu_item(item):
    tags = [tag.strip() for tag in (item.tags or "").split(",") if tag.strip()]
    if item.is_veg and "veg" not in tags:
        tags.insert(0, "veg")
    if item.is_bestseller and "bestseller" not in tags:
        tags.append("bestseller")

    return {
        "id": item.id,
        "store_id": item.store_id,
        "category_id": item.category_id,
        "category_name": item.category.name if item.category else None,
        "name": item.name,
        "description": item.description or "",
        "price": money_to_float(item.price),
        "image_url": f"/static/uploads/{item.image_filename}" if item.image_filename else "",
        "is_available": item.is_available,
        "is_veg": item.is_veg,
        "is_bestseller": item.is_bestseller,
        "tags": tags,
    }


def serialize_table(table):
    return {
        "id": table.id,
        "store_id": table.store_id,
        "store_name": table.store.name if table.store else "",
        "store_slug": table.store.slug if table.store else "",
        "table_number": table.table_number,
        "label": table.label or f"Table {table.table_number}",
        "qr_slug": table.qr_slug,
        "is_active": table.is_active,
        "menu_url": (
            f"/menu?store={table.store.slug}&table={table.id}"
            if table.store
            else f"/menu?table={table.id}"
        ),
        "qr_image_url": f"/qr/table/{table.id}.png",
    }


def serialize_staff_profile(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "role": user.role,
        "role_label": user.role_label,
        "active": user.active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def serialize_customer_contact(contact):
    return {
        "id": contact.id,
        "store_id": contact.store_id,
        "store_name": contact.store.name if contact.store else "",
        "name": contact.name or "",
        "phone": contact.phone,
        "marketing_opt_in": contact.marketing_opt_in,
        "order_count": contact.order_count,
        "total_spend": money_to_float(contact.total_spend),
        "first_order_at": contact.first_order_at.isoformat() if contact.first_order_at else None,
        "last_order_at": contact.last_order_at.isoformat() if contact.last_order_at else None,
        "last_order_id": contact.last_order_id,
    }


def serialize_payment(payment):
    return {
        "id": payment.id,
        "provider": payment.provider,
        "amount": money_to_float(payment.amount),
        "currency": payment.currency,
        "status": payment.status,
    }


def serialize_order(order):
    token = order.daily_token
    return {
        "id": order.id,
        "order_number": order.order_number,
        "store_id": order.store_id,
        "store_name": order.store.name if order.store else "",
        "store_slug": order.store.slug if order.store else "",
        "table_id": order.table_id,
        "table_label": order.table.label if order.table and order.table.label else (
            f"Table {order.table.table_number}" if order.table else None
        ),
        "customer_name": order.customer_name or "",
        "customer_phone": order.customer_phone or "",
        "notes": order.notes or "",
        "subtotal_amount": money_to_float(order.subtotal_amount),
        "tax_amount": money_to_float(order.tax_amount),
        "total_amount": money_to_float(order.total_amount),
        "currency": order.currency,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "status": order.status,
        "token_number": token.token_number if token else None,
        "token_status": token.status if token else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        "items": [
            {
                "id": item.id,
                "menu_item_id": item.menu_item_id,
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit_price": money_to_float(item.unit_price),
                "line_total": money_to_float(item.line_total),
            }
            for item in order.items
        ],
        "payments": [serialize_payment(payment) for payment in order.payments],
    }
