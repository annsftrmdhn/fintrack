from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from app import db
from app.models import Transaction, Category

summary_bp = Blueprint("summary", __name__)


@summary_bp.route("/monthly", methods=["GET"])
@jwt_required()
def monthly_summary():
    """
    Ringkasan pengeluaran dan pemasukan per bulan.

    Query params:
        year  (int): Tahun (default: tahun sekarang)
        month (int): Bulan 1-12 (default: bulan sekarang)
    """
    user_id = int(get_jwt_identity())
    now = datetime.utcnow()

    year = request.args.get("year", now.year, type=int)
    month = request.args.get("month", now.month, type=int)

    if not (1 <= month <= 12):
        return jsonify({"error": "Bulan harus antara 1 dan 12"}), 400

    # Filter transaksi bulan & tahun ini
    base_query = Transaction.query.filter(
        Transaction.user_id == user_id,
        db.extract("year", Transaction.date) == year,
        db.extract("month", Transaction.date) == month,
    )

    # Total pengeluaran
    total_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        db.extract("year", Transaction.date) == year,
        db.extract("month", Transaction.date) == month,
        Transaction.transaction_type == "expense",
    ).scalar() or 0

    # Total pemasukan
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        db.extract("year", Transaction.date) == year,
        db.extract("month", Transaction.date) == month,
        Transaction.transaction_type == "income",
    ).scalar() or 0

    # Pengeluaran per kategori
    by_category = db.session.query(
        Category.name,
        Category.icon,
        func.sum(Transaction.amount).label("total"),
    ).join(Transaction, Transaction.category_id == Category.id).filter(
        Transaction.user_id == user_id,
        db.extract("year", Transaction.date) == year,
        db.extract("month", Transaction.date) == month,
        Transaction.transaction_type == "expense",
    ).group_by(Category.name, Category.icon).order_by(func.sum(Transaction.amount).desc()).all()

    # Hitung persentase per kategori
    category_breakdown = []
    for row in by_category:
        percentage = round((row.total / total_expense * 100), 1) if total_expense > 0 else 0
        category_breakdown.append({
            "category": row.name,
            "icon": row.icon,
            "total": row.total,
            "percentage": percentage,
        })

    # Transaksi tanpa kategori
    uncategorized = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        db.extract("year", Transaction.date) == year,
        db.extract("month", Transaction.date) == month,
        Transaction.transaction_type == "expense",
        Transaction.category_id.is_(None),
    ).scalar() or 0

    if uncategorized > 0:
        category_breakdown.append({
            "category": "Tanpa Kategori",
            "icon": "❓",
            "total": uncategorized,
            "percentage": round((uncategorized / total_expense * 100), 1) if total_expense > 0 else 0,
        })

    return jsonify({
        "period": {
            "year": year,
            "month": month,
            "label": datetime(year, month, 1).strftime("%B %Y"),
        },
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": total_income - total_expense,
        "by_category": category_breakdown,
        "transaction_count": base_query.count(),
    }), 200


@summary_bp.route("/yearly", methods=["GET"])
@jwt_required()
def yearly_summary():
    """
    Ringkasan pengeluaran per bulan dalam satu tahun.

    Query params:
        year (int): Tahun (default: tahun sekarang)
    """
    user_id = int(get_jwt_identity())
    year = request.args.get("year", datetime.utcnow().year, type=int)

    monthly_data = []
    for month in range(1, 13):
        expense = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            db.extract("year", Transaction.date) == year,
            db.extract("month", Transaction.date) == month,
            Transaction.transaction_type == "expense",
        ).scalar() or 0

        income = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            db.extract("year", Transaction.date) == year,
            db.extract("month", Transaction.date) == month,
            Transaction.transaction_type == "income",
        ).scalar() or 0

        monthly_data.append({
            "month": month,
            "month_name": datetime(year, month, 1).strftime("%b"),
            "expense": expense,
            "income": income,
            "net": income - expense,
        })

    total_expense = sum(m["expense"] for m in monthly_data)
    total_income = sum(m["income"] for m in monthly_data)

    return jsonify({
        "year": year,
        "monthly": monthly_data,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": total_income - total_expense,
    }), 200
