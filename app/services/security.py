import secrets
import threading
import time
from collections import defaultdict, deque
from hmac import compare_digest

from flask import abort, request, session


_rate_lock = threading.Lock()
_rate_buckets = defaultdict(deque)


def generate_csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def _csrf_token_from_request():
    return (
        request.headers.get("X-CSRFToken")
        or request.headers.get("X-CSRF-Token")
        or request.form.get("csrf_token")
    )


def _is_csrf_exempt():
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return True
    return request.endpoint in {
        "api.razorpay_webhook",
    }


def _client_key():
    forwarded = request.headers.get("X-Forwarded-For", "")
    ip = forwarded.split(",")[0].strip() if forwarded else request.remote_addr
    return f"{ip or 'unknown'}:{request.path}"


def _enforce_rate_limit(app):
    if request.endpoint == "static":
        return

    limit = app.config["RATE_LIMIT_REQUESTS"]
    window = app.config["RATE_LIMIT_WINDOW_SECONDS"]
    now = time.time()
    key = _client_key()

    with _rate_lock:
        bucket = _rate_buckets[key]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= limit:
            app.logger.warning("Rate limit exceeded for %s", key)
            abort(429, description="Too many requests. Please try again shortly.")
        bucket.append(now)


def _enforce_csrf():
    if _is_csrf_exempt():
        return

    expected = session.get("_csrf_token")
    provided = _csrf_token_from_request()
    if not expected or not provided or not compare_digest(expected, provided):
        abort(400, description="Invalid or missing CSRF token.")


def register_security(app):
    app.jinja_env.globals["csrf_token"] = generate_csrf_token

    @app.before_request
    def security_before_request():
        _enforce_rate_limit(app)
        _enforce_csrf()

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        return response
