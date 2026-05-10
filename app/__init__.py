import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

# Load .env jika ada (untuk development lokal)
load_dotenv()

# Inisialisasi ekstensi (belum terikat ke app)
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
bcrypt = Bcrypt()


def create_app():
    """Application Factory Pattern - membuat dan mengkonfigurasi Flask app."""
    app = Flask(__name__)

    # ── Konfigurasi utama ──────────────────────────────────────────────────
    # Coba ambil dari DATABASE_URL dulu, jika tidak ada, coba SQLALCHEMY_DATABASE_URI
    database_url = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///fintrack.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-fallback")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # Token tidak expired (bisa diubah)

    # ── Ikat ekstensi ke app ───────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # ── Registrasi Blueprint (modular routing) ─────────────────────────────
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.transactions import transactions_bp
    from app.routes.categories import categories_bp
    from app.routes.summary import summary_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(transactions_bp, url_prefix="/transactions")
    app.register_blueprint(categories_bp, url_prefix="/categories")
    app.register_blueprint(summary_bp, url_prefix="/summary")

    # ── Error handler global ───────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint tidak ditemukan"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method tidak diizinkan"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Terjadi kesalahan pada server"}), 500

    # Error handler JWT
    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        return jsonify({"error": "Token tidak ada atau tidak valid", "detail": reason}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({"error": "Token sudah kadaluarsa"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({"error": "Token tidak valid", "detail": reason}), 422

    return app
