ORDER_STATUSES = (
    "payment_pending",
    "pending",
    "preparing",
    "ready",
    "completed",
    "cancelled",
)

TOKEN_STATUSES = ("pending", "preparing", "ready", "completed")

PAYMENT_STATUSES = (
    "not_required",
    "created",
    "pending",
    "paid",
    "failed",
    "cash_pending",
    "refunded",
)

PAYMENT_METHODS = ("cash", "razorpay")

PAYMENT_PROVIDERS = ("cash", "razorpay", "mock")

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
