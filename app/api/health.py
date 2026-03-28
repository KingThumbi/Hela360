# app/api/health.py
from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.get("/health")
def health_check():
    return jsonify({"ok": True, "service": "hela360", "status": "healthy"})