from decimal import Decimal


def money_to_float(value):
    if value is None:
        return 0.0
    return float(Decimal(value).quantize(Decimal("0.01")))


def serialize_category(category):
    return {
        "id": category.id,
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
        "table_number": table.table_number,
        "label": table.label or f"Table {table.table_number}",
        "qr_slug": table.qr_slug,
        "is_active": table.is_active,
        "menu_url": f"/menu?table={table.id}",
    }


def serialize_payment(payment):
    return {
        "id": payment.id,
        "provider": payment.provider,
        "provider_order_id": payment.provider_order_id,
        "provider_payment_id": payment.provider_payment_id,
        "amount": money_to_float(payment.amount),
        "currency": payment.currency,
        "status": payment.status,
    }


def serialize_order(order):
    token = order.daily_token
    return {
        "id": order.id,
        "order_number": order.order_number,
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
