# FinTrack API 💰

REST API untuk pencatatan dan analisis pengeluaran harian.  
Dibangun dengan **Flask** + **MySQL**, di-deploy ke **Railway PaaS**.

---

## Fitur Utama

- Autentikasi JWT (register, login)
- CRUD transaksi (pengeluaran & pemasukan)
- Manajemen kategori pengeluaran
- Ringkasan bulanan dan tahunan dengan breakdown per kategori
- Health check endpoint
- Konfigurasi via variabel lingkungan

---

## Endpoint API

| Method | Endpoint                  | Deskripsi                         | Auth |
|--------|---------------------------|-----------------------------------|------|
| GET    | `/health`                 | Status aplikasi & database        | ❌   |
| POST   | `/auth/register`          | Daftar pengguna baru              | ❌   |
| POST   | `/auth/login`             | Login & dapatkan token JWT        | ❌   |
| GET    | `/auth/me`                | Profil pengguna yang login        | ✅   |
| GET    | `/transactions`           | Daftar semua transaksi            | ✅   |
| POST   | `/transactions`           | Tambah transaksi baru             | ✅   |
| GET    | `/transactions/<id>`      | Detail satu transaksi             | ✅   |
| PUT    | `/transactions/<id>`      | Ubah transaksi                    | ✅   |
| DELETE | `/transactions/<id>`      | Hapus transaksi                   | ✅   |
| GET    | `/categories`             | Daftar kategori                   | ✅   |
| POST   | `/categories`             | Tambah kategori baru              | ✅   |
| GET    | `/categories/<id>`        | Detail kategori                   | ✅   |
| PUT    | `/categories/<id>`        | Ubah kategori                     | ✅   |
| DELETE | `/categories/<id>`        | Hapus kategori                    | ✅   |
| GET    | `/summary/monthly`        | Ringkasan bulanan                 | ✅   |
| GET    | `/summary/yearly`         | Ringkasan tahunan per bulan       | ✅   |

---

## Cara Menjalankan Lokal

### 1. Clone & masuk ke direktori
```bash
git clone https://github.com/[username]/fintrack-api.git
cd fintrack-api
```

### 2. Buat virtual environment & install dependency
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 3. Buat file `.env`
```bash
cp .env.example .env
# Edit .env dan isi DATABASE_URL & JWT_SECRET_KEY
```

### 4. Inisialisasi database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. Jalankan server
```bash
python wsgi.py
# API berjalan di http://localhost:5000
```

---

## Deployment ke Railway

1. Push kode ke GitHub
2. Buka [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Pilih repository ini
4. Tambahkan add-on: **New > Database > MySQL**
5. Di tab **Variables**, tambahkan:
   - `JWT_SECRET_KEY` = string acak panjang
   - `FLASK_ENV` = `production`
6. Railway otomatis deploy. URL tersedia di **Settings > Domain**

---

## Contoh Penggunaan

### Register
```bash
curl -X POST https://[url-railway]/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"budi","email":"budi@email.com","password":"rahasia123"}'
```

### Login
```bash
curl -X POST https://[url-railway]/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"budi@email.com","password":"rahasia123"}'
```

### Tambah Transaksi
```bash
curl -X POST https://[url-railway]/transactions \
  -H "Authorization: Bearer [TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{"amount":45000,"description":"Makan siang","date":"2026-05-08","transaction_type":"expense","category_id":1}'
```

### Ringkasan Bulanan
```bash
curl https://[url-railway]/summary/monthly?year=2026&month=5 \
  -H "Authorization: Bearer [TOKEN]"
```

---

## Menjalankan Tes
```bash
pip install pytest
pytest tests/ -v
```

---

## Struktur Proyek
```
fintrack-api/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # SQLAlchemy models
│   └── routes/
│       ├── health.py        # GET /health
│       ├── auth.py          # POST /auth/register, /auth/login
│       ├── transactions.py  # CRUD /transactions
│       ├── categories.py    # CRUD /categories
│       └── summary.py       # GET /summary/monthly, /yearly
├── tests/                   # Unit tests
├── .env.example             # Template konfigurasi
├── Procfile                 # Konfigurasi Railway
├── requirements.txt
└── wsgi.py                  # Entry point
```

---

## Tech Stack
- **Python 3.11**
- **Flask 3.0** — Web framework
- **Flask-SQLAlchemy** — ORM
- **Flask-JWT-Extended** — Autentikasi JWT
- **Flask-Migrate** — Database migration
- **Flask-Bcrypt** — Password hashing
- **MySQL** — Database (add-on Railway)
- **Gunicorn** — WSGI server produksi
- **Railway** — Platform PaaS

---

Tugas Mandiri BBK3CAB3 | Komputasi Awan | Program Studi S1 Sistem Informasi
