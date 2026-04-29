import click

from app.extensions import db
from app.services.auth_service import ensure_admin_user
from app.services.sample_data import seed_sample_data


def register_commands(app):
    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("seed-data")
    def seed_data():
        seed_sample_data(app.config)
        click.echo("Tea Trust Cafe menu, tables, and admin user are ready.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--email", default="")
    @click.password_option()
    def create_admin(username, email, password):
        _, created = ensure_admin_user(username, password, email or None)
        click.echo("Admin created." if created else "Admin already exists.")
