from datetime import datetime
from app import db


class User(db.Model):
    """Model pengguna aplikasi."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi ke tabel lain
    categories = db.relationship("Category", backref="user", lazy=True, cascade="all, delete-orphan")
    transactions = db.relationship("Transaction", backref="user", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<User {self.username}>"


class Category(db.Model):
    """Model kategori pengeluaran (milik masing-masing user)."""
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(10), default="💰")   # Emoji ikon opsional
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi ke transaksi
    transactions = db.relationship("Transaction", backref="category", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Category {self.name}>"


class Transaction(db.Model):
    """Model transaksi / catatan pengeluaran."""
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)                      # Jumlah uang (Rupiah)
    description = db.Column(db.String(200), nullable=False)           # Keterangan
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    transaction_type = db.Column(db.String(10), default="expense")    # 'expense' atau 'income'
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "description": self.description,
            "date": self.date.isoformat(),
            "transaction_type": self.transaction_type,
            "category": self.category.to_dict() if self.category else None,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Transaction {self.id} - {self.amount}>"
