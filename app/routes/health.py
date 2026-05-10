from flask import Blueprint, jsonify
from sqlalchemy import text
from app import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health Check Endpoint.
    Memeriksa status aplikasi dan koneksi database.
    Tidak memerlukan autentikasi.
    """
    db_status = "connected"
    db_error = None

    try:
        # Coba eksekusi query sederhana ke database
        db.session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "disconnected"
        db_error = str(e)

    response = {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "version": "1.0.0",
        "app": "FinTrack API",
    }

    if db_error:
        response["db_error"] = db_error

    status_code = 200 if db_status == "connected" else 503
    return jsonify(response), status_code
