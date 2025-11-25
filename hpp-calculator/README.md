# AI HPP Calculator

Platform web-based untuk membantu UKM dan business owners menghitung **Harga Pokok Penjualan (HPP/COGS)** dengan akurat berdasarkan material cost, quantity per batch, dan target margin.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Fitur Utama

- **Kalkulasi HPP Real-time** - Hitung HPP per unit secara otomatis
- **Input Bahan Dinamis** - Tambah/hapus bahan dengan mudah
- **Analisis Margin** - Bandingkan margin aktual vs target
- **Import Excel/CSV** - Upload data bahan dari spreadsheet
- **Export Laporan** - Download hasil perhitungan ke Excel
- **Top 3 Kontributor Biaya** - Identifikasi bahan dengan biaya tertinggi
- **Indonesian Localization** - Interface dalam Bahasa Indonesia
- **Mobile Responsive** - Dapat diakses dari smartphone

## Screenshot

```
┌─────────────────────────────────────────────────────────────┐
│  🧠 AI HPP Calculator                                       │
│  Hitung HPP per porsi dengan cepat dan terstruktur         │
├─────────────────────────────────────────────────────────────┤
│  📦 Bahan & Biaya per Batch                                │
│  [Data Editor Table]                                        │
├─────────────────────────────────────────────────────────────┤
│  📦 Output, Margin & Harga Jual                            │
│  [Total Porsi]  [Target Margin]  [Harga Jual Aktual]       │
│  [🧮 Hitung HPP & Harga Jual]                              │
├─────────────────────────────────────────────────────────────┤
│  📊 Ringkasan Hasil                                         │
│  📈 Analisis Margin Saat Ini                               │
│  🔍 Detail Perhitungan per Bahan                           │
│  🏆 Top 3 Kontributor Biaya                                │
│  📥 Export ke Excel                                         │
└─────────────────────────────────────────────────────────────┘
```

## Instalasi

### Prerequisites

- Python 3.9 atau lebih baru
- pip (Python package manager)

### Langkah Instalasi

1. **Clone repository**
   ```bash
   git clone https://github.com/your-username/hpp-calculator.git
   cd hpp-calculator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Jalankan aplikasi**
   ```bash
   streamlit run app.py
   ```

4. **Buka browser**
   ```
   http://localhost:8501
   ```

## Penggunaan

### 1. Input Bahan

Isi tabel bahan dengan:
- **Nama Barang**: Nama bahan
- **Qty Bahan**: Jumlah per kemasan (misal: 250 gram/bungkus)
- **Satuan**: Satuan bahan (gram, kg, ml, liter, pcs, dll)
- **Qty Jumlah**: Jumlah kemasan yang dibeli (misal: beli 2 bungkus)
- **Harga**: Harga per kemasan
- **Subtotal**: Dihitung otomatis (Qty Jumlah × Harga)

### 2. Konfigurasi Output & Biaya Tambahan

- **Biaya Operasional**: Biaya listrik, gas, air, dll per batch
- **Biaya Lain-lain**: Biaya kemasan, label, transport, dll per batch
- **Total porsi/unit**: Jumlah unit yang dihasilkan per batch
- **Target margin (%)**: Persentase margin yang diinginkan
- **Harga jual saat ini**: (Opsional) Untuk analisis margin aktual

### 3. Hitung HPP

Klik tombol **"Hitung HPP & Harga Jual"** untuk melihat:
- Total biaya per batch (Bahan + Operasional + Lain-lain)
- HPP per unit
- Harga jual disarankan
- Analisis margin (aktual vs target)
- Detail kontribusi per bahan
- Top 3 kontributor biaya tertinggi

### 4. Export Hasil

Download laporan dalam format Excel dengan klik **"Download HPP report (Excel)"**

## Import dari Excel/CSV

1. Download template dari sidebar
2. Isi data bahan sesuai format
3. Upload file melalui sidebar
4. Data akan otomatis terisi di tabel

### Format Template

| Nama_Barang | Qty_Bahan | Satuan | Qty_Jumlah | Harga |
|-------------|-----------|--------|------------|-------|
| Tepung Terigu | 250 | gram | 2 | 15000 |
| Ayam Karkas | 1 | kg | 3 | 40000 |
| Minyak Goreng | 1 | liter | 2 | 20000 |

**Keterangan:**
- `Qty_Bahan`: Jumlah per kemasan (misal: 250 gram/bungkus)
- `Qty_Jumlah`: Jumlah kemasan yang dibeli
- `Harga`: Harga per kemasan
- **Subtotal = Qty_Jumlah × Harga** (Qty_Bahan hanya sebagai referensi)

## Formula Perhitungan

```
Subtotal per Bahan   = Qty_Jumlah × Harga
Total Biaya Bahan    = Σ Subtotal per Bahan
Total Batch Cost     = Biaya Bahan + Biaya Operasional + Biaya Lain-lain

HPP per Unit         = Total Batch Cost ÷ Output Units
Margin Amount        = HPP per Unit × (Target Margin % ÷ 100)
Harga Jual           = HPP per Unit + Margin Amount

Margin Aktual %      = ((Harga Jual - HPP) ÷ HPP) × 100
Gap vs Target        = Margin Aktual % - Target Margin %
```

## Struktur Project

```
hpp-calculator/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # Documentation
├── database/
│   ├── __init__.py
│   ├── db.py             # SQLite connection & settings
│   └── models.py         # Database CRUD operations
├── utils/
│   ├── __init__.py
│   ├── calculations.py   # HPP calculation logic
│   ├── formatters.py     # Currency & number formatting
│   └── export.py         # Excel export & import
├── components/
│   └── __init__.py
├── styles/
│   └── main.css          # Custom CSS styling
├── data/
│   └── hpp_calculator.db # SQLite database
└── templates/
    └── (Excel templates)
```

## Tech Stack

- **Frontend**: Streamlit
- **Styling**: Custom CSS (shadcn/ui inspired)
- **Database**: SQLite
- **Export**: OpenPyXL, XlsxWriter
- **Data Processing**: Pandas

## Konfigurasi

### Settings (Sidebar)

- **Currency symbol**: Simbol mata uang (default: Rp)
- **Target margin default**: Margin default untuk perhitungan baru

### Environment Variables (Opsional)

```bash
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
```

## Kontribusi

1. Fork repository
2. Buat branch fitur (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Kontak

**Irfan Yulianto** - [LinkedIn](https://www.linkedin.com/in/irfan-yulianto/)

---

Made with ❤️ for Indonesian UMKM
