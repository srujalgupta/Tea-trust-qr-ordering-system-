import click

from app.extensions import db
from app.models import CustomerContact, DailyToken, Order, OrderItem, Payment, Store
from app.services.auth_service import ensure_admin_user
from app.services.sample_data import seed_sample_data
from app.services.schema_service import ensure_runtime_schema


def register_commands(app):
    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        ensure_runtime_schema(app)
        click.echo("Database tables created and upgraded.")

    @app.cli.command("seed-data")
    def seed_data():
        ensure_runtime_schema(app)
        seed_sample_data(app.config)
        click.echo("Tea Trust Cafe menu, tables, and admin user are ready.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--email", default="")
    @click.password_option()
    def create_admin(username, email, password):
        _, created = ensure_admin_user(username, password, email or None)
        click.echo("Admin created." if created else "Admin already exists.")

    @app.cli.command("reset-orders")
    @click.option("--yes", is_flag=True, help="Confirm deleting matching orders and related rows.")
    @click.option(
        "--store",
        "store_ref",
        default=None,
        help="Limit the reset to one store by id, slug, or name.",
    )
    @click.option(
        "--keep-customers",
        is_flag=True,
        help="Keep customer contact records while clearing order history.",
    )
    def reset_orders(yes, store_ref, keep_customers):
        if not yes:
            raise click.UsageError("Add --yes to confirm clearing matching order history.")

        store = _resolve_store(store_ref) if store_ref else None
        before = _reset_counts(store)

        _delete_order_history(store=store, keep_customers=keep_customers)
        db.session.commit()

        after = _reset_counts(store)
        if store:
            click.echo(f"Store: {store.name} ({store.slug})")
        click.echo(f"Before: {before}")
        click.echo(f"After: {after}")


def _resolve_store(store_ref):
    store_ref = (store_ref or "").strip()
    store = None
    if store_ref.isdigit():
        store = db.session.get(Store, int(store_ref))
    if store is None:
        store = Store.query.filter_by(slug=store_ref).first()
    if store is None:
        store = Store.query.filter_by(name=store_ref).first()
    if store is None:
        raise click.UsageError(f"Store '{store_ref}' was not found.")
    return store


def _order_ids_for_store(store):
    return db.select(Order.id).where(Order.store_id == store.id)


def _reset_counts(store=None):
    if store is None:
        return {
            "orders": Order.query.count(),
            "order_items": OrderItem.query.count(),
            "payments": Payment.query.count(),
            "daily_tokens": DailyToken.query.count(),
            "customer_contacts": CustomerContact.query.count(),
        }

    order_ids = _order_ids_for_store(store)
    return {
        "orders": Order.query.filter_by(store_id=store.id).count(),
        "order_items": OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).count(),
        "payments": Payment.query.filter(Payment.order_id.in_(order_ids)).count(),
        "daily_tokens": DailyToken.query.filter(DailyToken.order_id.in_(order_ids)).count(),
        "customer_contacts": CustomerContact.query.filter_by(store_id=store.id).count(),
    }


def _delete_order_history(store=None, keep_customers=False):
    if store is None:
        if keep_customers:
            CustomerContact.query.update(
                {CustomerContact.last_order_id: None},
                synchronize_session=False,
            )
        else:
            CustomerContact.query.delete(synchronize_session=False)
        DailyToken.query.delete(synchronize_session=False)
        Payment.query.delete(synchronize_session=False)
        OrderItem.query.delete(synchronize_session=False)
        Order.query.delete(synchronize_session=False)
        return

    order_ids = _order_ids_for_store(store)
    if keep_customers:
        CustomerContact.query.filter_by(store_id=store.id).update(
            {CustomerContact.last_order_id: None},
            synchronize_session=False,
        )
    else:
        CustomerContact.query.filter_by(store_id=store.id).delete(synchronize_session=False)
    DailyToken.query.filter(DailyToken.order_id.in_(order_ids)).delete(synchronize_session=False)
    Payment.query.filter(Payment.order_id.in_(order_ids)).delete(synchronize_session=False)
    OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).delete(synchronize_session=False)
    Order.query.filter_by(store_id=store.id).delete(synchronize_session=False)
