import threading
from datetime import datetime

from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import DailyToken
from .errors import ValidationError


_token_lock = threading.Lock()


def _today():
    return datetime.now().date()


def _acquire_database_day_lock(token_date):
    bind = db.session.get_bind()
    if bind and bind.dialect.name == "postgresql":
        lock_id = int(token_date.strftime("%Y%m%d"))
        db.session.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": lock_id})


def generate_daily_token_for_order(order):
    if order.daily_token:
        return order.daily_token

    token_date = _today()
    with _token_lock:
        _acquire_database_day_lock(token_date)
        max_number = (
            db.session.query(func.max(DailyToken.token_number))
            .filter(DailyToken.token_date == token_date)
            .scalar()
            or 0
        )
        token = DailyToken(
            token_date=token_date,
            token_number=max_number + 1,
            order=order,
            status="pending",
        )
        db.session.add(token)
        try:
            db.session.flush()
        except IntegrityError as exc:
            raise ValidationError("Could not generate token safely. Please retry.") from exc
        return token


def sync_token_status(order, status):
    if not order.daily_token:
        return None
    order.daily_token.status = status
    return order.daily_token
