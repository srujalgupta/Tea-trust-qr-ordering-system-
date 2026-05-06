ORDER_STATUSES = (
    "pending",
    "preparing",
    "ready",
    "completed",
    "cancelled",
)

TOKEN_STATUSES = ("pending", "preparing", "ready", "completed")

PAYMENT_STATUSES = (
    "cash_pending",
    "paid",
    "refunded",
)

PAYMENT_METHODS = ("cash",)

PAYMENT_PROVIDERS = ("cash",)


def sql_values(values):
    return "(" + ", ".join(f"'{value}'" for value in values) + ")"


ORDER_STATUS_SQL = sql_values(ORDER_STATUSES)
PAYMENT_STATUS_SQL = sql_values(PAYMENT_STATUSES)
PAYMENT_METHOD_SQL = sql_values(PAYMENT_METHODS)
PAYMENT_PROVIDER_SQL = sql_values(PAYMENT_PROVIDERS)

STAFF_ROLES = ("owner", "manager", "counter", "kitchen", "menu")

STAFF_ROLE_LABELS = {
    "owner": "Owner",
    "manager": "Manager",
    "counter": "Counter",
    "kitchen": "Kitchen",
    "menu": "Menu Manager",
}

ROLE_PERMISSIONS = {
    "owner": {"*"},
    "manager": {
        "analytics:view",
        "dashboard:view",
        "menu:manage",
        "orders:update",
        "orders:view",
        "settings:view",
        "tables:manage",
    },
    "counter": {
        "analytics:view",
        "dashboard:view",
        "orders:update",
        "orders:view",
        "tables:manage",
    },
    "kitchen": {
        "orders:update",
        "orders:view",
    },
    "menu": {
        "menu:manage",
    },
}
