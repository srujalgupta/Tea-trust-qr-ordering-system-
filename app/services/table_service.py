from flask import current_app, has_app_context

from app.extensions import db
from app.models import CafeTable
from .errors import NotFoundError, ValidationError
from .serializers import serialize_table


def _slug_for_table(table_number):
    return f"table-{table_number}"


def _table_count_limit():
    if has_app_context():
        return int(current_app.config.get("CAFE_TABLE_COUNT", 6))
    return 6


def _validate_table_number(value):
    try:
        table_number = int(value)
    except (TypeError, ValueError):
        raise ValidationError("table_number must be a positive integer.") from None
    if table_number <= 0:
        raise ValidationError("table_number must be a positive integer.")

    table_limit = _table_count_limit()
    if table_number > table_limit:
        raise ValidationError(f"This cafe is configured for {table_limit} tables.")
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
    table_number = _validate_table_number(data.get("table_number"))

    label = (data.get("label") or f"Table {table_number}").strip()
    table = CafeTable(
        table_number=table_number,
        label=label,
        qr_slug=(data.get("qr_slug") or _slug_for_table(table_number)).strip(),
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(table)
    db.session.commit()
    return table


def update_table(table_id, data):
    table = get_table(table_id)
    if "table_number" in data:
        table.table_number = _validate_table_number(data.get("table_number"))
    if "label" in data:
        table.label = (data.get("label") or "").strip()
    if "qr_slug" in data:
        table.qr_slug = (data.get("qr_slug") or "").strip()
    if "is_active" in data:
        table.is_active = bool(data.get("is_active"))
    db.session.commit()
    return table


def tables_payload(include_inactive=True):
    return [serialize_table(table) for table in list_tables(include_inactive)]
