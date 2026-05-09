import click

from app.extensions import db
from app.models import CustomerContact, DailyToken, Order, OrderItem, Payment
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
    @click.option("--yes", is_flag=True, help="Confirm deleting all orders and related rows.")
    @click.option(
        "--keep-customers",
        is_flag=True,
        help="Keep customer contact records while clearing order history.",
    )
    def reset_orders(yes, keep_customers):
        if not yes:
            raise click.UsageError("Add --yes to confirm clearing all order history.")

        before = {
            "orders": Order.query.count(),
            "order_items": OrderItem.query.count(),
            "payments": Payment.query.count(),
            "daily_tokens": DailyToken.query.count(),
            "customer_contacts": CustomerContact.query.count(),
        }

        if not keep_customers:
            CustomerContact.query.delete(synchronize_session=False)
        DailyToken.query.delete(synchronize_session=False)
        Payment.query.delete(synchronize_session=False)
        OrderItem.query.delete(synchronize_session=False)
        Order.query.delete(synchronize_session=False)
        db.session.commit()

        after = {
            "orders": Order.query.count(),
            "order_items": OrderItem.query.count(),
            "payments": Payment.query.count(),
            "daily_tokens": DailyToken.query.count(),
            "customer_contacts": CustomerContact.query.count(),
        }
        click.echo(f"Before: {before}")
        click.echo(f"After: {after}")
