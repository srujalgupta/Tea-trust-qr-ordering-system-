from sqlalchemy import inspect, text

from app.extensions import db
from app.models.constants import TOKEN_STATUSES


def ensure_runtime_schema(app):
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if "customer_contacts" not in tables:
            db.create_all()
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
        if "stores" not in tables:
            db.create_all()
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
        if "users" not in tables:
            return

        _ensure_default_store_rows()
        _ensure_store_columns()
        _drop_legacy_unique_indexes()
        _ensure_store_indexes()

        columns = _columns("users")
        if "role" not in columns:
            db.session.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR(30) NOT NULL DEFAULT 'owner'")
            )
            db.session.commit()


def _columns(table_name):
    return {column["name"] for column in inspect(db.engine).get_columns(table_name)}


def _add_column(table_name, column_name, definition):
    if column_name in _columns(table_name):
        return False
    db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {definition}"))
    return True


def _ensure_default_store_rows():
    bind = db.session.get_bind()
    if bind and bind.dialect.name == "postgresql":
        statement = """
            INSERT INTO stores
                (id, name, slug, address, phone, is_active, created_at, updated_at)
            VALUES
                (1, 'Store 1', 'store-1', NULL, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (2, 'Store 2', 'store-2', NULL, NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
        """
    else:
        statement = """
            INSERT OR IGNORE INTO stores
                (id, name, slug, address, phone, is_active, created_at, updated_at)
            VALUES
                (1, 'Store 1', 'store-1', NULL, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (2, 'Store 2', 'store-2', NULL, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
    db.session.execute(text(statement))
    db.session.commit()


def _ensure_store_columns():
    table_names = set(inspect(db.engine).get_table_names())
    if "categories" in table_names:
        _add_column("categories", "store_id", "store_id INTEGER NOT NULL DEFAULT 1")
    if "menu_items" in table_names:
        _add_column("menu_items", "store_id", "store_id INTEGER NOT NULL DEFAULT 1")
        db.session.execute(
            text(
                """
                UPDATE menu_items
                SET store_id = COALESCE(
                    (SELECT categories.store_id FROM categories WHERE categories.id = menu_items.category_id),
                    store_id,
                    1
                )
                """
            )
        )
    if "tables" in table_names:
        _add_column("tables", "store_id", "store_id INTEGER NOT NULL DEFAULT 1")
    if "orders" in table_names:
        _add_column("orders", "store_id", "store_id INTEGER NOT NULL DEFAULT 1")
        db.session.execute(
            text(
                """
                UPDATE orders
                SET store_id = COALESCE(
                    (SELECT tables.store_id FROM tables WHERE tables.id = orders.table_id),
                    store_id,
                    1
                )
                """
            )
        )
    if "daily_tokens" in table_names:
        if "store_id" not in _columns("daily_tokens"):
            if _is_sqlite():
                _rebuild_daily_tokens_with_store()
            else:
                _add_column(
                    "daily_tokens",
                    "store_id",
                    "store_id INTEGER NOT NULL DEFAULT 1",
                )
                db.session.execute(
                    text(
                        """
                        UPDATE daily_tokens
                        SET store_id = COALESCE(
                            (SELECT orders.store_id FROM orders WHERE orders.id = daily_tokens.order_id),
                            store_id,
                            1
                        )
                        """
                    )
                )
    if "customer_contacts" in table_names:
        _add_column(
            "customer_contacts",
            "store_id",
            "store_id INTEGER NOT NULL DEFAULT 1",
        )
    if "users" in table_names:
        _add_column("users", "store_id", "store_id INTEGER")
        db.session.execute(
            text(
                """
                UPDATE users
                SET store_id = 1
                WHERE COALESCE(role, 'owner') != 'owner'
                  AND store_id IS NULL
                """
            )
        )
    db.session.commit()


def _drop_legacy_unique_indexes():
    if _is_postgresql():
        for table_name, constraint_name in (
            ("categories", "categories_name_key"),
            ("tables", "tables_table_number_key"),
            ("tables", "tables_qr_slug_key"),
            ("daily_tokens", "uq_daily_tokens_date_number"),
            ("customer_contacts", "customer_contacts_phone_key"),
        ):
            db.session.execute(
                text(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}")
            )

    for index_name in (
        "ix_categories_name",
        "ix_tables_table_number",
        "ix_tables_qr_slug",
        "ix_customer_contacts_phone",
        "ix_daily_tokens_date_status",
    ):
        db.session.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
    db.session.commit()


def _ensure_store_indexes():
    statements = (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_store_name ON categories (store_id, name)",
        "CREATE INDEX IF NOT EXISTS ix_categories_store_order ON categories (store_id, display_order)",
        "CREATE INDEX IF NOT EXISTS ix_menu_items_store_available ON menu_items (store_id, is_available)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_tables_store_number ON tables (store_id, table_number)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_tables_store_slug ON tables (store_id, qr_slug)",
        "CREATE INDEX IF NOT EXISTS ix_orders_store_status_created ON orders (store_id, status, created_at)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_daily_tokens_store_date_number ON daily_tokens (store_id, token_date, token_number)",
        "CREATE INDEX IF NOT EXISTS ix_daily_tokens_store_date_status ON daily_tokens (store_id, token_date, status)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_customer_contacts_store_phone ON customer_contacts (store_id, phone)",
        "CREATE INDEX IF NOT EXISTS ix_users_store_id ON users (store_id)",
    )
    tables = set(inspect(db.engine).get_table_names())
    for statement in statements:
        table_name = statement.split(" ON ", 1)[1].split(" ", 1)[0]
        if table_name in tables:
            db.session.execute(text(statement))
    db.session.commit()


def _is_sqlite():
    bind = db.session.get_bind()
    return bool(bind and bind.dialect.name == "sqlite")


def _is_postgresql():
    bind = db.session.get_bind()
    return bool(bind and bind.dialect.name == "postgresql")


def _rebuild_daily_tokens_with_store():
    status_sql = ", ".join(f"'{status}'" for status in TOKEN_STATUSES)
    db.session.execute(text("ALTER TABLE daily_tokens RENAME TO daily_tokens_old"))
    db.session.execute(
        text(
            f"""
            CREATE TABLE daily_tokens (
                id INTEGER NOT NULL,
                store_id INTEGER NOT NULL DEFAULT 1,
                token_date DATE NOT NULL,
                token_number INTEGER NOT NULL,
                order_id INTEGER NOT NULL,
                status VARCHAR(30) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                PRIMARY KEY (id),
                UNIQUE (store_id, token_date, token_number),
                UNIQUE (order_id),
                CHECK (token_number > 0),
                CHECK (status IN ({status_sql})),
                FOREIGN KEY(store_id) REFERENCES stores (id) ON DELETE CASCADE,
                FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE
            )
            """
        )
    )
    db.session.execute(
        text(
            """
            INSERT INTO daily_tokens
                (id, store_id, token_date, token_number, order_id, status, created_at, updated_at)
            SELECT
                id,
                COALESCE((SELECT orders.store_id FROM orders WHERE orders.id = daily_tokens_old.order_id), 1),
                token_date,
                token_number,
                order_id,
                status,
                created_at,
                updated_at
            FROM daily_tokens_old
            """
        )
    )
    db.session.execute(text("DROP TABLE daily_tokens_old"))
    db.session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_daily_tokens_store_date_status "
            "ON daily_tokens (store_id, token_date, status)"
        )
    )
    db.session.execute(
        text("CREATE INDEX IF NOT EXISTS ix_daily_tokens_token_date ON daily_tokens (token_date)")
    )
    db.session.execute(
        text("CREATE INDEX IF NOT EXISTS ix_daily_tokens_status ON daily_tokens (status)")
    )
