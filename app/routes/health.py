from flask import Blueprint, current_app, jsonify

from app.services.health_service import build_health_payload


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return jsonify(build_health_payload(current_app)), 200
