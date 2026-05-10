from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db, bcrypt
from app.models import User, Category

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Mendaftarkan pengguna baru.

    Body JSON:
        username (str): Username unik
        email    (str): Email unik
        password (str): Password minimal 6 karakter
    """
    data = request.get_json()

    # Validasi field wajib
    required = ["username", "email", "password"]
    for field in required:
        if not data or not data.get(field):
            return jsonify({"error": f"Field '{field}' wajib diisi"}), 400

    username = data["username"].strip()
    email = data["email"].strip().lower()
    password = data["password"]

    if len(password) < 6:
        return jsonify({"error": "Password minimal 6 karakter"}), 400

    # Cek apakah username atau email sudah terdaftar
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username sudah digunakan"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email sudah digunakan"}), 409

    # Hash password dan simpan user baru
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, email=email, password_hash=password_hash)

    db.session.add(user)
    db.session.flush()  # Dapatkan user.id sebelum commit

    # Buat kategori default untuk user baru
    default_categories = [
        ("Makanan & Minuman", "🍔"),
        ("Transportasi", "🚗"),
        ("Belanja", "🛍️"),
        ("Hiburan", "🎮"),
        ("Tagihan & Utilitas", "💡"),
        ("Kesehatan", "💊"),
        ("Lainnya", "📦"),
    ]
    for name, icon in default_categories:
        cat = Category(name=name, icon=icon, user_id=user.id)
        db.session.add(cat)

    db.session.commit()

    return jsonify({
        "message": "Registrasi berhasil",
        "user": user.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login dan mendapatkan JWT access token.

    Body JSON:
        email    (str): Email terdaftar
        password (str): Password
    """
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email dan password wajib diisi"}), 400

    email = data["email"].strip().lower()
    password = data["password"]

    user = User.query.filter_by(email=email).first()

    # Validasi user dan password
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Email atau password salah"}), 401

    # Buat JWT token dengan user_id sebagai identity
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Login berhasil",
        "access_token": access_token,
        "user": user.to_dict(),
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    """
    Mendapatkan profil user yang sedang login.
    Memerlukan JWT token.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    return jsonify({"user": user.to_dict()}), 200
