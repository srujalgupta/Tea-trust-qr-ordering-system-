import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
LOCAL_SQLITE_URI = f"sqlite:///{(INSTANCE_DIR / 'dev.db').as_posix()}"


def _normalize_database_url(database_url):
    if database_url and database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def _positive_int_from_env(name, default):
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(1, value)


def _bool_from_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    PROJECT_NAME = os.getenv("PROJECT_NAME", "Tea Trust Cafe")
    CAFE_NAME = os.getenv("CAFE_NAME", "Tea Trust Cafe")
    CAFE_TAGLINE = os.getenv("CAFE_TAGLINE", "Chai & Eatery")
    CAFE_SUBTITLE = os.getenv("CAFE_SUBTITLE", "An Authentic Tea Experience")
    CAFE_PHONE = os.getenv("CAFE_PHONE", "97275 20006")
    CAFE_TABLE_COUNT = _positive_int_from_env("CAFE_TABLE_COUNT", 6)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    DATABASE_URL = _normalize_database_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or LOCAL_SQLITE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SOCKETIO_ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE", "threading")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    TRUST_PROXY_HEADERS = _bool_from_env("TRUST_PROXY_HEADERS", False)
    SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "qr_cafe_session")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_REFRESH_EACH_REQUEST = False
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=_positive_int_from_env("SESSION_TIMEOUT_MINUTES", 60)
    )
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "app/static/uploads")
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "120"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    AUTH_LOGIN_RATE_LIMIT_REQUESTS = _positive_int_from_env(
        "AUTH_LOGIN_RATE_LIMIT_REQUESTS",
        8,
    )
    AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS = _positive_int_from_env(
        "AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS",
        15 * 60,
    )
    ORDER_CREATE_RATE_LIMIT_REQUESTS = _positive_int_from_env(
        "ORDER_CREATE_RATE_LIMIT_REQUESTS",
        20,
    )
    ORDER_CREATE_RATE_LIMIT_WINDOW_SECONDS = _positive_int_from_env(
        "ORDER_CREATE_RATE_LIMIT_WINDOW_SECONDS",
        10 * 60,
    )
    PASSWORD_MIN_LENGTH = _positive_int_from_env("PASSWORD_MIN_LENGTH", 12)
    SECURITY_CSP_ENABLED = _bool_from_env("SECURITY_CSP_ENABLED", True)
    PAYMENT_CURRENCY = os.getenv("PAYMENT_CURRENCY", "INR")
    CAFE_BANNER_VIDEO_URL = os.getenv("CAFE_BANNER_VIDEO_URL", "")
    CAFE_BANNER_POSTER_URL = os.getenv(
        "CAFE_BANNER_POSTER_URL",
        "/static/brand/tea_trust_menu_page_1.webp",
    )
    CAFE_LIVE_STREAM_EMBED_URL = os.getenv("CAFE_LIVE_STREAM_EMBED_URL", "")
    POS_WEBHOOK_URL = os.getenv("POS_WEBHOOK_URL", "")
    NOTIFICATION_WEBHOOK_URL = os.getenv("NOTIFICATION_WEBHOOK_URL", "")
    BROADCAST_SEND_WORKERS = _positive_int_from_env("BROADCAST_SEND_WORKERS", 8)
    WHATSAPP_CLOUD_API_VERSION = os.getenv("WHATSAPP_CLOUD_API_VERSION", "v25.0")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_BROADCAST_TEMPLATE_NAME = os.getenv("WHATSAPP_BROADCAST_TEMPLATE_NAME", "")
    WHATSAPP_TEMPLATE_LANGUAGE = os.getenv("WHATSAPP_TEMPLATE_LANGUAGE", "en_US")
    WHATSAPP_DEFAULT_COUNTRY_CODE = os.getenv("WHATSAPP_DEFAULT_COUNTRY_CODE", "91")
    WHATSAPP_ALLOW_FREEFORM_TEXT = _bool_from_env("WHATSAPP_ALLOW_FREEFORM_TEXT", False)
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin12345")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")


class DevelopmentConfig(BaseConfig):
    ENV_NAME = "development"
    DEBUG = True


class TestingConfig(BaseConfig):
    ENV_NAME = "testing"
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    ENV_NAME = "production"
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = BaseConfig.DATABASE_URL
    TRUST_PROXY_HEADERS = _bool_from_env("TRUST_PROXY_HEADERS", True)
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


CONFIG_BY_NAME = {
    "dev": DevelopmentConfig,
    "development": DevelopmentConfig,
    "test": TestingConfig,
    "testing": TestingConfig,
    "prod": ProductionConfig,
    "production": ProductionConfig,
}


def get_config(config_name=None):
    selected = (
        config_name
        or os.getenv("FLASK_CONFIG")
        or os.getenv("APP_ENV")
        or "development"
    ).lower()

    try:
        return CONFIG_BY_NAME[selected]
    except KeyError as exc:
        valid_names = ", ".join(sorted(CONFIG_BY_NAME))
        raise RuntimeError(
            f"Unknown config '{selected}'. Valid configs: {valid_names}."
        ) from exc
