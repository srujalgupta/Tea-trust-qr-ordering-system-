from sqlalchemy import inspect, text

from app.extensions import db


def ensure_runtime_schema(app):
    database_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not database_uri.startswith("sqlite"):
        return

    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if "customer_contacts" not in tables:
            db.create_all()
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
        if "users" not in tables:
            return

        columns = {column["name"] for column in inspector.get_columns("users")}
        if "role" not in columns:
            db.session.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR(30) NOT NULL DEFAULT 'owner'")
            )
            db.session.commit()
