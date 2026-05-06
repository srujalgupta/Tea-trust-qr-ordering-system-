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
    return False


def _client_ip():
    return request.remote_addr or "unknown"


def _rate_key(scope):
    return f"{scope}:{_client_ip()}:{request.path}"


def _rate_limited(key, limit, window, now):
    bucket = _rate_buckets[key]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


def _enforce_rate_limit(app):
    if request.endpoint == "static":
        return

    limit = app.config["RATE_LIMIT_REQUESTS"]
    window = app.config["RATE_LIMIT_WINDOW_SECONDS"]
    now = time.time()
    key = _rate_key("request")

    with _rate_lock:
        if _rate_limited(key, limit, window, now):
            app.logger.warning("Rate limit exceeded for %s", key)
            abort(429, description="Too many requests. Please try again shortly.")


def _enforce_login_rate_limit(app):
    if request.endpoint != "admin.login" or request.method != "POST":
        return

    limit = app.config["AUTH_LOGIN_RATE_LIMIT_REQUESTS"]
    window = app.config["AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS"]
    username = (request.form.get("username") or "").strip().lower()[:80] or "blank"
    now = time.time()
    keys = [
        f"login-ip:{_client_ip()}",
        f"login-user:{username}",
    ]

    with _rate_lock:
        for key in keys:
            if _rate_limited(key, limit, window, now):
                app.logger.warning("Admin login rate limit exceeded for %s", key)
                abort(429, description="Too many login attempts. Please try again later.")


def _enforce_order_rate_limit(app):
    if request.endpoint != "api.create_customer_order" or request.method != "POST":
        return

    limit = app.config["ORDER_CREATE_RATE_LIMIT_REQUESTS"]
    window = app.config["ORDER_CREATE_RATE_LIMIT_WINDOW_SECONDS"]
    now = time.time()
    key = f"order-create:{_client_ip()}"

    with _rate_lock:
        if _rate_limited(key, limit, window, now):
            app.logger.warning("Customer order rate limit exceeded for %s", key)
            abort(429, description="Too many orders submitted. Please try again later.")


def _enforce_csrf():
    if _is_csrf_exempt():
        return

    expected = session.get("_csrf_token")
    provided = _csrf_token_from_request()
    if not expected or not provided or not compare_digest(expected, provided):
        abort(400, description="Invalid or missing CSRF token.")


def _content_security_policy(app):
    if not app.config.get("SECURITY_CSP_ENABLED", True):
        return None

    directives = [
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-ancestors 'self'",
        "form-action 'self'",
        "script-src 'self' https://cdn.socket.io",
        "style-src 'self'",
        "img-src 'self' data: blob: https:",
        "font-src 'self' data:",
        "media-src 'self' https:",
        "frame-src 'self' https:",
        "connect-src 'self' ws: wss:",
    ]
    if app.config["ENV_NAME"] == "production":
        directives.append("upgrade-insecure-requests")
    return "; ".join(directives)


def _admin_cache_headers(response):
    if request.path.startswith("/admin") or request.path.startswith("/api/v1/admin"):
        response.headers.setdefault("Cache-Control", "no-store, max-age=0")
        response.headers.setdefault("Pragma", "no-cache")
        response.headers.setdefault("Expires", "0")


def register_security(app):
    app.jinja_env.globals["csrf_token"] = generate_csrf_token

    @app.before_request
    def security_before_request():
        if not session.permanent:
            session.permanent = True
        _enforce_rate_limit(app)
        _enforce_login_rate_limit(app)
        _enforce_order_rate_limit(app)
        _enforce_csrf()

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("X-XSS-Protection", "0")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        csp = _content_security_policy(app)
        if csp:
            response.headers.setdefault("Content-Security-Policy", csp)
        if request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        _admin_cache_headers(response)
        return response
