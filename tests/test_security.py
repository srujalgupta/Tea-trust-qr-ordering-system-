import re

import pytest

from app import create_app
from app.extensions import db
from app.services.auth_service import validate_password_strength
from app.services.errors import ValidationError
from app.services.sample_data import seed_sample_data
from app.services.security import _rate_buckets


def csrf_from(html):
    match = re.search(r'name="csrf-token" content="([^"]+)"', html)
    assert match
    return match.group(1)


def app_client(**config):
    app = create_app("testing")
    app.config.update(config)
    _rate_buckets.clear()
    with app.app_context():
        db.create_all()
        seed_sample_data(app.config)
    return app.test_client()


def test_security_headers_and_strict_csp():
    client = app_client()
    response = client.get("/menu")

    assert response.status_code == 200
    csp = response.headers["Content-Security-Policy"]
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'self'" in csp
    assert "style-src 'self'" in csp
    assert "style=" not in response.get_data(as_text=True)
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_admin_login_throttle_blocks_repeated_attempts():
    client = app_client(AUTH_LOGIN_RATE_LIMIT_REQUESTS=2)
    login_page = client.get("/admin/login")
    token = csrf_from(login_page.get_data(as_text=True))

    for _ in range(2):
        response = client.post(
            "/admin/login",
            data={
                "username": "admin",
                "password": "wrong-password",
                "csrf_token": token,
            },
        )
        assert response.status_code == 200

    blocked = client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "wrong-password",
            "csrf_token": token,
        },
    )
    assert blocked.status_code == 429


def test_staff_password_cannot_be_common_or_username_based():
    app = create_app("testing")
    with app.app_context():
        with pytest.raises(ValidationError):
            validate_password_strength("admin12345", username="admin")
        with pytest.raises(ValidationError):
            validate_password_strength("kitchen12345", username="kitchen")
