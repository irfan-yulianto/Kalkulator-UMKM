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
- **Ingredient**: Nama bahan
- **Qty_per_batch**: Jumlah per batch produksi
- **Unit**: Satuan (kg, liter, pcs, dll)
- **Price_per_unit**: Harga per satuan

### 2. Konfigurasi Output

- **Total porsi/unit**: Jumlah unit yang dihasilkan per batch
- **Target margin (%)**: Persentase margin yang diinginkan
- **Harga jual saat ini**: (Opsional) Untuk analisis margin aktual

### 3. Hitung HPP

Klik tombol **"Hitung HPP & Harga Jual"** untuk melihat:
- Total biaya per batch
- HPP per unit
- Harga jual disarankan
- Analisis margin
- Detail kontribusi per bahan

### 4. Export Hasil

Download laporan dalam format Excel dengan klik **"Download HPP report (Excel)"**

## Import dari Excel/CSV

1. Download template dari sidebar
2. Isi data bahan sesuai format
3. Upload file melalui sidebar
4. Data akan otomatis terisi di tabel

### Format Template

| Ingredient | Qty_per_batch | Unit | Price_per_unit |
|------------|---------------|------|----------------|
| Ayam Karkas | 10 | kg | 40000 |
| Tepung | 2 | kg | 20000 |
| Minyak | 3 | liter | 15000 |

## Formula Perhitungan

```
Line Cost = Quantity × Price per Unit
Total Batch Cost = Σ Line Costs
HPP per Unit = Total Batch Cost ÷ Output Units
Margin Amount = HPP per Unit × (Target Margin % ÷ 100)
Selling Price = HPP per Unit + Margin Amount
Actual Margin % = ((Selling Price - HPP) ÷ HPP) × 100
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
