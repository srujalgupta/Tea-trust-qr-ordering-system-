import re

from app.extensions import db
from app.models import Store
from .errors import NotFoundError, ValidationError


DEFAULT_STORES = (
    {"name": "Store 1", "slug": "store-1"},
    {"name": "Store 2", "slug": "store-2"},
)


def normalize_store_slug(value, fallback="store"):
    slug = (value or fallback or "store").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug or "store"


def _unique_store_slug(base_slug, store_id=None):
    slug = normalize_store_slug(base_slug)
    suffix = 2
    while True:
        query = Store.query.filter_by(slug=slug)
        if store_id is not None:
            query = query.filter(Store.id != store_id)
        if not query.first():
            return slug
        slug = f"{base_slug}-{suffix}"
        suffix += 1


def ensure_default_stores():
    stores = []
    for store_data in DEFAULT_STORES:
        store = Store.query.filter_by(slug=store_data["slug"]).first()
        if not store:
            store = Store(
                name=store_data["name"],
                slug=store_data["slug"],
                is_active=True,
            )
            db.session.add(store)
        else:
            store.name = store.name or store_data["name"]
            store.is_active = True if store.is_active is None else store.is_active
        stores.append(store)
    db.session.flush()
    return stores


def list_stores(include_inactive=False):
    query = Store.query
    if not include_inactive:
        query = query.filter_by(is_active=True)
    return query.order_by(Store.id.asc()).all()


def get_default_store():
    store = Store.query.filter_by(is_active=True).order_by(Store.id.asc()).first()
    if store:
        return store

    stores = ensure_default_stores()
    db.session.commit()
    return stores[0]


def get_store(reference=None, require_active=True):
    if reference in (None, ""):
        return get_default_store()

    text = str(reference).strip()
    query = Store.query
    if text.isdigit():
        store = query.filter(Store.id == int(text)).first()
    else:
        store = query.filter(Store.slug == normalize_store_slug(text)).first()

    if not store or (require_active and not store.is_active):
        raise NotFoundError("Store not found.")
    return store


def store_from_request_args(args, require_active=True):
    return get_store(
        args.get("store")
        or args.get("store_id")
        or args.get("location")
        or args.get("location_id"),
        require_active=require_active,
    )


def validate_store_match(actual_store_id, expected_store, message):
    if expected_store and int(actual_store_id) != int(expected_store.id):
        raise ValidationError(message)
