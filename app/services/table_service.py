import re

from app.extensions import db
from app.models import CafeTable
from .errors import NotFoundError, ValidationError
from .serializers import serialize_table


def _slug_for_table(table_number):
    return f"table-{table_number}"


def _normalize_slug(value, table_number):
    slug = (value or _slug_for_table(table_number)).strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    if not slug:
        slug = _slug_for_table(table_number)
    return slug


def _next_table_number():
    existing = {
        number for (number,) in db.session.query(CafeTable.table_number).all()
    }
    table_number = 1
    while table_number in existing:
        table_number += 1
    return table_number


def _unique_slug(base_slug, table_id=None):
    slug = base_slug
    suffix = 2
    while True:
        query = CafeTable.query.filter_by(qr_slug=slug)
        if table_id is not None:
            query = query.filter(CafeTable.id != table_id)
        if not query.first():
            return slug
        slug = f"{base_slug}-{suffix}"
        suffix += 1


def _ensure_table_number_available(table_number, table_id=None):
    query = CafeTable.query.filter_by(table_number=table_number)
    if table_id is not None:
        query = query.filter(CafeTable.id != table_id)
    if query.first():
        raise ValidationError("A table with this number already exists.")


def _bool_value(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return bool(value)


def _validate_table_number(value, required=True):
    if value in {None, ""} and not required:
        return _next_table_number()
    try:
        table_number = int(value)
    except (TypeError, ValueError):
        raise ValidationError("table_number must be a positive integer.") from None
    if table_number <= 0:
        raise ValidationError("table_number must be a positive integer.")
    return table_number


def list_tables(include_inactive=True):
    query = CafeTable.query
    if not include_inactive:
        query = query.filter_by(is_active=True)
    return query.order_by(CafeTable.table_number.asc()).all()


def get_table(table_id, require_active=False):
    try:
        table_id = int(table_id)
    except (TypeError, ValueError):
        raise NotFoundError("Table not found.") from None
    table = db.session.get(CafeTable, table_id)
    if not table or (require_active and not table.is_active):
        raise NotFoundError("Table not found.")
    return table


def create_table(data):
    table_number = _validate_table_number(data.get("table_number"), required=False)
    _ensure_table_number_available(table_number)

    label = (data.get("label") or f"Table {table_number}").strip()
    base_slug = _normalize_slug(data.get("qr_slug"), table_number)
    table = CafeTable(
        table_number=table_number,
        label=label,
        qr_slug=_unique_slug(base_slug),
        is_active=_bool_value(data.get("is_active"), default=True),
    )
    db.session.add(table)
    db.session.commit()
    return table


def update_table(table_id, data):
    table = get_table(table_id)
    if "table_number" in data:
        table_number = _validate_table_number(data.get("table_number"))
        _ensure_table_number_available(table_number, table.id)
        table.table_number = table_number
    if "label" in data:
        table.label = (data.get("label") or f"Table {table.table_number}").strip()
    if "qr_slug" in data:
        table.qr_slug = _unique_slug(_normalize_slug(data.get("qr_slug"), table.table_number), table.id)
    if "is_active" in data:
        table.is_active = _bool_value(data.get("is_active"))
    db.session.commit()
    return table


def tables_payload(include_inactive=True):
    return [serialize_table(table) for table in list_tables(include_inactive)]
