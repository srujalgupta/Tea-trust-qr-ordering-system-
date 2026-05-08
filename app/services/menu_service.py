from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models import Category, MenuItem, OrderItem
from .errors import NotFoundError, ValidationError
from .serializers import serialize_category, serialize_menu_item


def _clean_text(value, field, max_length=None, required=False):
    value = (value or "").strip()
    if required and not value:
        raise ValidationError(f"{field} is required.")
    if max_length and len(value) > max_length:
        raise ValidationError(f"{field} must be {max_length} characters or fewer.")
    return value


def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_price(value):
    try:
        price = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        raise ValidationError("price must be a valid number.") from None
    if price < 0:
        raise ValidationError("price cannot be negative.")
    return price


def _parse_int(value, field, default=None, minimum=None):
    if value in (None, ""):
        if default is not None:
            return default
        raise ValidationError(f"{field} is required.")
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a whole number.") from None
    if minimum is not None and number < minimum:
        raise ValidationError(f"{field} must be at least {minimum}.")
    return number


def list_categories(include_inactive=False):
    query = Category.query
    if not include_inactive:
        query = query.filter_by(is_active=True)
    return query.order_by(Category.display_order.asc(), Category.name.asc()).all()


def list_menu_items(category_id=None, search=None, include_unavailable=False):
    query = MenuItem.query.join(Category)
    if category_id:
        query = query.filter(MenuItem.category_id == category_id)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            db.or_(
                MenuItem.name.ilike(like),
                MenuItem.description.ilike(like),
                MenuItem.tags.ilike(like),
            )
        )
    if not include_unavailable:
        query = query.filter(MenuItem.is_available.is_(True), Category.is_active.is_(True))
    return query.order_by(Category.display_order.asc(), MenuItem.name.asc()).all()


def menu_payload(category_id=None, search=None, include_unavailable=False):
    return {
        "categories": [serialize_category(category) for category in list_categories(include_unavailable)],
        "items": [
            serialize_menu_item(item)
            for item in list_menu_items(category_id, search, include_unavailable)
        ],
    }


def get_category(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        raise NotFoundError("Category not found.")
    return category


def get_menu_item(item_id):
    item = db.session.get(MenuItem, item_id)
    if not item:
        raise NotFoundError("Menu item not found.")
    return item


def create_category(data):
    category = Category(
        name=_clean_text(data.get("name"), "name", 120, required=True),
        description=_clean_text(data.get("description"), "description", 255),
        display_order=_parse_int(data.get("display_order"), "display_order", default=0),
        is_active=_parse_bool(data.get("is_active"), True),
    )
    db.session.add(category)
    db.session.commit()
    return category


def update_category(category_id, data):
    category = get_category(category_id)
    if "name" in data:
        category.name = _clean_text(data.get("name"), "name", 120, required=True)
    if "description" in data:
        category.description = _clean_text(data.get("description"), "description", 255)
    if "display_order" in data:
        category.display_order = _parse_int(
            data.get("display_order"),
            "display_order",
            default=0,
        )
    if "is_active" in data:
        category.is_active = _parse_bool(data.get("is_active"), category.is_active)
    db.session.commit()
    return category


def create_menu_item(data):
    category = get_category(_parse_int(data.get("category_id"), "category_id", minimum=1))
    item = MenuItem(
        category=category,
        name=_clean_text(data.get("name"), "name", 160, required=True),
        description=_clean_text(data.get("description"), "description"),
        price=_parse_price(data.get("price")),
        is_available=_parse_bool(data.get("is_available"), True),
        is_veg=_parse_bool(data.get("is_veg"), True),
        is_bestseller=_parse_bool(data.get("is_bestseller"), False),
        tags=_clean_text(data.get("tags"), "tags", 255),
    )
    db.session.add(item)
    db.session.commit()
    return item


def update_menu_item(item_id, data):
    item = get_menu_item(item_id)
    if "category_id" in data:
        item.category = get_category(
            _parse_int(data.get("category_id"), "category_id", minimum=1)
        )
    if "name" in data:
        item.name = _clean_text(data.get("name"), "name", 160, required=True)
    if "description" in data:
        item.description = _clean_text(data.get("description"), "description")
    if "price" in data:
        item.price = _parse_price(data.get("price"))
    if "is_available" in data:
        item.is_available = _parse_bool(data.get("is_available"), item.is_available)
    if "is_veg" in data:
        item.is_veg = _parse_bool(data.get("is_veg"), item.is_veg)
    if "is_bestseller" in data:
        item.is_bestseller = _parse_bool(data.get("is_bestseller"), item.is_bestseller)
    if "tags" in data:
        item.tags = _clean_text(data.get("tags"), "tags", 255)
    db.session.commit()
    return item


def delete_menu_item(item_id):
    item = get_menu_item(item_id)
    has_order_history = db.session.query(OrderItem.id).filter_by(menu_item_id=item.id).first()
    if has_order_history:
        item.is_available = False
        db.session.commit()
        return
    db.session.delete(item)
    db.session.commit()


def set_menu_item_image(item_id, filename):
    item = get_menu_item(item_id)
    item.image_filename = filename
    db.session.commit()
    return item
