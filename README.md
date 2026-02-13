# 📦 SIMIGD - Sistem Informasi Manajemen Inventaris Gudang Delima Jaya

![Django](https://img.shields.io/badge/Django-5.2.4-green.svg)
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Sistem Informasi Manajemen Inventaris Gudang (SIMIGD) adalah aplikasi web berbasis Django untuk mengelola inventaris gudang PT Delima Jaya. Aplikasi ini menyediakan fitur lengkap untuk manajemen stok barang, transaksi masuk/keluar, permintaan barang produksi, serta pelaporan untuk manajemen.

Projek Praktik Lapang

---

## ✨ Fitur Utama

### 👨‍💼 **Administrator**
- ✅ Manajemen pengguna (CRUD user dengan role-based access)
- ✅ Reset password pengguna
- ✅ Dashboard monitoring sistem
- ✅ Akses penuh ke semua fitur sistem

### 📦 **Pegawai Gudang**
- ✅ **Manajemen Master Data**
  - Kategori barang
  - Data supplier
  - Master barang/item
- ✅ **Transaksi Barang**
  - Barang masuk (incoming)
  - Barang keluar (outgoing)
  - Approval permintaan barang dari produksi
- ✅ **Monitoring Stok**
  - Status stok real-time (In Stock, Low Stock, Out of Stock)
  - Alert stok menipis
  - Riwayat transaksi per item

### 🏭 **Pegawai Produksi**
- ✅ Buat permintaan barang
- ✅ Monitor status permintaan (Pending, Approved, Rejected, Completed)
- ✅ Lihat ketersediaan stok
- ✅ Riwayat permintaan

### 👔 **Direktur**
- ✅ **Dashboard Eksekutif**
  - Grafik transaksi 7 hari terakhir
  - Distribusi status stok (Pie Chart)
  - Statistik lengkap inventaris
- ✅ **Laporan Lengkap**
  - Laporan stok barang
  - Laporan barang masuk
  - Laporan barang keluar
  - Laporan permintaan barang
  - Export ke PDF
- ✅ **Histori Aktivitas**
  - Timeline semua transaksi sistem
  - Filter by type, date range

---

## 🛠️ Teknologi yang Digunakan

### Backend
- **Django 5.2.4** - Web Framework
- **Django REST Framework** - API Development
- **SQLite** - Database
- **ReportLab** - PDF Generation

### Frontend
- **Bootstrap 5** - UI Framework
- **Bootstrap Icons** - Icon Library
- **Chart.js** - Data Visualization
- **Crispy Forms** - Enhanced Forms

---

## 📋 Prasyarat

Pastikan sistem Anda telah terinstal:
- Python 3.8 atau lebih tinggi
- pip (Python package manager)
- Git (opsional)

---

## 🚀 Instalasi & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd simigd
```

### 2. Buat Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Jalankan Migrasi Database
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Buat User Admin (Opsional)
User admin sudah tersedia dengan kredensial default (lihat di bawah), atau buat user baru:
```bash
python manage.py shell
>>> from inventory.models import User
>>> User.objects.create(name='Admin', username='admin', password='password123', role='admin')
>>> exit()
```

### 6. Jalankan Development Server
```bash
python manage.py runserver
```

Aplikasi dapat diakses di: **http://127.0.0.1:8000/**

---

## 👤 Kredensial Default

Gunakan akun berikut untuk login:

| Role | Username | Password |
|------|----------|----------|
| Administrator | `Admin` | `12345678` |

> ⚠️ **Penting:** Segera ubah password default setelah login pertama kali untuk keamanan!

---

## 📁 Struktur Project

```
simigd/
├── inventory/                  # Main application
│   ├── models.py              # Database models
│   ├── views.py               # Main views (Dashboard, Login, User Management)
│   ├── inventory_views.py     # Warehouse views
│   ├── production_views.py    # Production views
│   ├── directur_views.py      # Director views (Reports, History)
│   ├── forms.py               # Form definitions
│   ├── mixins.py              # Authentication mixins
│   ├── urls.py                # URL routing
│   ├── admin.py               # Django admin config
│   ├── templates/             # HTML templates
│   │   ├── base.html
│   │   ├── login.html
│   │   └── inventory/
│   │       ├── admin/         # User management templates
│   │       ├── warehouse/     # Warehouse templates
│   │       ├── production/    # Production templates
│   │       └── director/      # Director templates
│   └── static/                # Static files (CSS, JS, Images)
│       └── inventory/
│           └── images/
├── simigd/                    # Project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── db.sqlite3                 # SQLite database
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🔐 Role-Based Access Control

Sistem menggunakan 4 level akses pengguna:

| Role | Akses |
|------|-------|
| **Admin** | Full access - manajemen user, semua fitur gudang & produksi |
| **Pegawai Gudang** | CRUD master data, transaksi barang, approval permintaan |
| **Pegawai Produksi** | Buat & monitor permintaan barang |
| **Direktur** | Read-only dashboard, laporan lengkap, histori aktivitas |

---

## 📊 Fitur Dashboard

### Statistik Real-time
- Total barang aktif
- Status stok (In Stock, Low Stock, Out of Stock)
- Total stok (unit)
- Transaksi barang masuk/keluar bulan ini
- Permintaan pending & approved

### Visualisasi Data
- **Pie Chart**: Distribusi status stok
- **Line Chart**: Tren transaksi 7 hari terakhir

---

## 📄 Laporan yang Tersedia

1. **Laporan Stok Barang**
   - Daftar lengkap item dengan stok terkini
   - Status stok dan kategori
   - Export ke PDF

2. **Laporan Barang Masuk**
   - Transaksi incoming dengan detail supplier
   - Filter by date range
   - Export ke PDF

3. **Laporan Barang Keluar**
   - Transaksi outgoing dengan tujuan
   - Filter by date range
   - Export ke PDF

4. **Laporan Permintaan Barang**
   - Status permintaan produksi
   - Statistik approval/rejection
   - Export ke PDF

---

## 🎯 Cara Penggunaan

### Login
1. Buka browser dan akses `http://127.0.0.1:8000/`
2. Masukkan username dan password
3. Sistem akan redirect ke dashboard sesuai role

### Manajemen Barang (Pegawai Gudang)
1. **Tambah Kategori**: Menu Kategori → Tambah Kategori
2. **Tambah Supplier**: Menu Supplier → Tambah Supplier
3. **Tambah Item**: Menu Barang → Tambah Barang
4. **Transaksi Masuk**: Menu Barang Masuk → Tambah Transaksi
5. **Transaksi Keluar**: Menu Barang Keluar → Tambah Transaksi

### Permintaan Barang (Pegawai Produksi)
1. Menu Permintaan → Buat Permintaan
2. Pilih barang dan masukkan jumlah
3. Tunggu approval dari gudang/admin

### Approval Permintaan (Pegawai Gudang/Admin)
1. Menu Permintaan → Lihat daftar pending
2. Klik detail permintaan
3. Approve atau Reject dengan catatan

### Lihat Laporan (Direktur)
1. Menu Laporan → Pilih jenis laporan
2. Set filter jika diperlukan
3. Klik "Export PDF" untuk download

---

## 🔧 Konfigurasi

### Database
Default menggunakan SQLite. Untuk production, ubah di `simigd/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Static Files
Untuk production, jalankan:
```bash
python manage.py collectstatic
```

---

## 🐛 Troubleshooting

### Server tidak bisa diakses
```bash
# Pastikan tidak ada proses yang menggunakan port 8000
# Atau jalankan di port lain
python manage.py runserver 8080
```

### Template not found error
```bash
# Pastikan struktur folder templates sudah benar
# Jalankan ulang server
python manage.py runserver
```

### Migration error
```bash
# Reset migrations (development only!)
python manage.py migrate --run-syncdb
```

---

## 📝 Development Notes

### Menambah User Baru via Shell
```python
python manage.py shell
>>> from inventory.models import User
>>> User.objects.create(
...     name='Nama Lengkap',
...     username='username',
...     password='password123',
...     role='pegawai_gudang',  # atau 'pegawai_produksi', 'direktur', 'admin'
...     is_active=True
... )
```

### Role Choices
- `admin` - Administrator
- `pegawai_gudang` - Pegawai Gudang
- `pegawai_produksi` - Pegawai Produksi
- `direktur` - Direktur

---

## 🤝 Kontribusi

Kontribusi selalu diterima! Untuk berkontribusi:
1. Fork repository ini
2. Buat branch fitur (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

---

## 👨‍💻 Author

Alfandi Ahmad

---

<div align="center">
  <strong>Made with ❤️ by Delima Jaya IT Team</strong>
</div>
