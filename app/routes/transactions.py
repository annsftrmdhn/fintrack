from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Transaction, Category

transactions_bp = Blueprint("transactions", __name__)


def parse_date(date_str):
    """Mengubah string tanggal (YYYY-MM-DD) menjadi objek date."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


@transactions_bp.route("", methods=["GET"])
@jwt_required()
def get_transactions():
    """
    Mengambil semua transaksi milik user.

    Query params (opsional):
        month     (int): Filter bulan (1-12)
        year      (int): Filter tahun (mis. 2026)
        category  (int): Filter berdasarkan category_id
        type      (str): Filter tipe: 'income' atau 'expense'
        page      (int): Nomor halaman (default 1)
        per_page  (int): Jumlah data per halaman (default 20)
    """
    user_id = int(get_jwt_identity())

    query = Transaction.query.filter_by(user_id=user_id)

    # Filter opsional
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    category_id = request.args.get("category", type=int)
    tx_type = request.args.get("type")

    if year:
        query = query.filter(db.extract("year", Transaction.date) == year)
    if month:
        query = query.filter(db.extract("month", Transaction.date) == month)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if tx_type in ("income", "expense"):
        query = query.filter_by(transaction_type=tx_type)

    # Urutkan dari terbaru
    query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())

    # Paginasi
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)  # Maksimal 100 per halaman

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "transactions": [t.to_dict() for t in paginated.items],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": paginated.total,
            "pages": paginated.pages,
        },
    }), 200


@transactions_bp.route("", methods=["POST"])
@jwt_required()
def create_transaction():
    """
    Menambahkan transaksi baru.

    Body JSON:
        amount           (float): Jumlah uang (wajib, > 0)
        description      (str):   Keterangan (wajib)
        date             (str):   Tanggal YYYY-MM-DD (wajib)
        transaction_type (str):   'expense' atau 'income' (default 'expense')
        category_id      (int):   ID kategori (opsional)
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()

    # Validasi field wajib
    required = ["amount", "description", "date"]
    for field in required:
        if not data or data.get(field) is None:
            return jsonify({"error": f"Field '{field}' wajib diisi"}), 400

    amount = data["amount"]
    description = data["description"].strip()
    date_str = data["date"]
    tx_type = data.get("transaction_type", "expense")
    category_id = data.get("category_id")

    # Validasi nilai
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "Amount harus berupa angka positif"}), 400

    if not description:
        return jsonify({"error": "Description tidak boleh kosong"}), 400

    tx_date = parse_date(date_str)
    if not tx_date:
        return jsonify({"error": "Format tanggal tidak valid, gunakan YYYY-MM-DD"}), 400

    if tx_type not in ("income", "expense"):
        return jsonify({"error": "transaction_type harus 'income' atau 'expense'"}), 400

    # Validasi category milik user ini
    if category_id:
        cat = Category.query.filter_by(id=category_id, user_id=user_id).first()
        if not cat:
            return jsonify({"error": "Kategori tidak ditemukan"}), 404

    transaction = Transaction(
        amount=amount,
        description=description,
        date=tx_date,
        transaction_type=tx_type,
        category_id=category_id,
        user_id=user_id,
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        "message": "Transaksi berhasil ditambahkan",
        "transaction": transaction.to_dict(),
    }), 201


@transactions_bp.route("/<int:transaction_id>", methods=["GET"])
@jwt_required()
def get_transaction(transaction_id):
    """Mengambil detail satu transaksi berdasarkan ID."""
    user_id = int(get_jwt_identity())
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()

    if not transaction:
        return jsonify({"error": "Transaksi tidak ditemukan"}), 404

    return jsonify({"transaction": transaction.to_dict()}), 200


@transactions_bp.route("/<int:transaction_id>", methods=["PUT"])
@jwt_required()
def update_transaction(transaction_id):
    """
    Mengubah data transaksi.
    Semua field bersifat opsional — hanya field yang dikirim yang akan diubah.
    """
    user_id = int(get_jwt_identity())
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()

    if not transaction:
        return jsonify({"error": "Transaksi tidak ditemukan"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Tidak ada data yang dikirim"}), 400

    # Update field jika ada dalam request
    if "amount" in data:
        if not isinstance(data["amount"], (int, float)) or data["amount"] <= 0:
            return jsonify({"error": "Amount harus berupa angka positif"}), 400
        transaction.amount = data["amount"]

    if "description" in data:
        if not data["description"].strip():
            return jsonify({"error": "Description tidak boleh kosong"}), 400
        transaction.description = data["description"].strip()

    if "date" in data:
        tx_date = parse_date(data["date"])
        if not tx_date:
            return jsonify({"error": "Format tanggal tidak valid, gunakan YYYY-MM-DD"}), 400
        transaction.date = tx_date

    if "transaction_type" in data:
        if data["transaction_type"] not in ("income", "expense"):
            return jsonify({"error": "transaction_type harus 'income' atau 'expense'"}), 400
        transaction.transaction_type = data["transaction_type"]

    if "category_id" in data:
        if data["category_id"] is None:
            transaction.category_id = None
        else:
            cat = Category.query.filter_by(id=data["category_id"], user_id=user_id).first()
            if not cat:
                return jsonify({"error": "Kategori tidak ditemukan"}), 404
            transaction.category_id = data["category_id"]

    transaction.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "message": "Transaksi berhasil diperbarui",
        "transaction": transaction.to_dict(),
    }), 200


@transactions_bp.route("/<int:transaction_id>", methods=["DELETE"])
@jwt_required()
def delete_transaction(transaction_id):
    """Menghapus transaksi berdasarkan ID."""
    user_id = int(get_jwt_identity())
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()

    if not transaction:
        return jsonify({"error": "Transaksi tidak ditemukan"}), 404

    db.session.delete(transaction)
    db.session.commit()

    return jsonify({"message": "Transaksi berhasil dihapus"}), 200
