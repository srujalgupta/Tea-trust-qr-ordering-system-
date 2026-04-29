from datetime import datetime, timezone


def build_health_payload(app):
    return {
        "status": "ok",
        "service": app.config["PROJECT_NAME"],
        "environment": app.config["ENV_NAME"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
