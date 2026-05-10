from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Category

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("", methods=["GET"])
@jwt_required()
def get_categories():
    """Mengambil semua kategori milik user yang login."""
    user_id = int(get_jwt_identity())
    categories = Category.query.filter_by(user_id=user_id).order_by(Category.name).all()
    return jsonify({
        "categories": [c.to_dict() for c in categories],
        "total": len(categories),
    }), 200


@categories_bp.route("", methods=["POST"])
@jwt_required()
def create_category():
    """
    Membuat kategori baru.

    Body JSON:
        name (str): Nama kategori
        icon (str): Emoji ikon (opsional)
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or not data.get("name"):
        return jsonify({"error": "Field 'name' wajib diisi"}), 400

    name = data["name"].strip()
    icon = data.get("icon", "💰").strip()

    # Cek duplikat kategori milik user ini
    existing = Category.query.filter_by(user_id=user_id, name=name).first()
    if existing:
        return jsonify({"error": "Kategori dengan nama ini sudah ada"}), 409

    category = Category(name=name, icon=icon, user_id=user_id)
    db.session.add(category)
    db.session.commit()

    return jsonify({
        "message": "Kategori berhasil dibuat",
        "category": category.to_dict(),
    }), 201


@categories_bp.route("/<int:category_id>", methods=["GET"])
@jwt_required()
def get_category(category_id):
    """Mengambil detail satu kategori berdasarkan ID."""
    user_id = int(get_jwt_identity())
    category = Category.query.filter_by(id=category_id, user_id=user_id).first()

    if not category:
        return jsonify({"error": "Kategori tidak ditemukan"}), 404

    return jsonify({"category": category.to_dict()}), 200


@categories_bp.route("/<int:category_id>", methods=["PUT"])
@jwt_required()
def update_category(category_id):
    """
    Mengubah nama atau ikon kategori.

    Body JSON:
        name (str): Nama baru (opsional)
        icon (str): Ikon baru (opsional)
    """
    user_id = int(get_jwt_identity())
    category = Category.query.filter_by(id=category_id, user_id=user_id).first()

    if not category:
        return jsonify({"error": "Kategori tidak ditemukan"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Tidak ada data yang dikirim"}), 400

    if "name" in data and data["name"].strip():
        category.name = data["name"].strip()
    if "icon" in data:
        category.icon = data["icon"].strip()

    db.session.commit()

    return jsonify({
        "message": "Kategori berhasil diperbarui",
        "category": category.to_dict(),
    }), 200


@categories_bp.route("/<int:category_id>", methods=["DELETE"])
@jwt_required()
def delete_category(category_id):
    """Menghapus kategori. Transaksi terkait akan menjadi tanpa kategori."""
    user_id = int(get_jwt_identity())
    category = Category.query.filter_by(id=category_id, user_id=user_id).first()

    if not category:
        return jsonify({"error": "Kategori tidak ditemukan"}), 404

    # Set category_id = NULL pada transaksi yang menggunakan kategori ini
    from app.models import Transaction
    Transaction.query.filter_by(category_id=category_id).update({"category_id": None})

    db.session.delete(category)
    db.session.commit()

    return jsonify({"message": "Kategori berhasil dihapus"}), 200
