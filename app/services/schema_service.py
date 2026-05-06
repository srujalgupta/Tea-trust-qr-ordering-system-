from sqlalchemy import inspect, text

from app.extensions import db


def ensure_runtime_schema(app):
    database_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not database_uri.startswith("sqlite"):
        return

    with app.app_context():
        inspector = inspect(db.engine)
        if "users" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("users")}
        if "role" not in columns:
            db.session.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR(30) NOT NULL DEFAULT 'owner'")
            )
            db.session.commit()
