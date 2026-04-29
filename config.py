import os
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


class BaseConfig:
    PROJECT_NAME = os.getenv("PROJECT_NAME", "Tea Trust Cafe")
    CAFE_NAME = os.getenv("CAFE_NAME", "TEA Trust Cafe")
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
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "app/static/uploads")
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "120"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    PAYMENT_CURRENCY = os.getenv("PAYMENT_CURRENCY", "INR")
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    RAZORPAY_FORCE_MOCK = os.getenv("RAZORPAY_FORCE_MOCK", "false").lower() == "true"
    CAFE_BANNER_VIDEO_URL = os.getenv("CAFE_BANNER_VIDEO_URL", "")
    CAFE_BANNER_POSTER_URL = os.getenv(
        "CAFE_BANNER_POSTER_URL",
        "/static/brand/tea_trust_menu_page_1.webp",
    )
    CAFE_LIVE_STREAM_EMBED_URL = os.getenv("CAFE_LIVE_STREAM_EMBED_URL", "")
    POS_WEBHOOK_URL = os.getenv("POS_WEBHOOK_URL", "")
    NOTIFICATION_WEBHOOK_URL = os.getenv("NOTIFICATION_WEBHOOK_URL", "")
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
    SESSION_COOKIE_SECURE = True


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
