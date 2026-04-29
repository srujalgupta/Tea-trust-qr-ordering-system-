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
