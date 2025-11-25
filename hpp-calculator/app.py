"""
AI HPP Calculator - Harga Pokok Penjualan Calculator
Platform web-based untuk membantu UKM dan business owners menghitung HPP/COGS
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.calculations import calculate_all, get_top_contributors, validate_ingredients
from utils.formatters import format_currency, format_percentage, format_gap, format_unit_options
from utils.export import create_excel_report, create_import_template, parse_import_file
from database.db import init_db, get_setting, set_setting

# Page config
st.set_page_config(
    page_title="AI HPP Calculator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "styles", "main.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize database
init_db()

# Initialize session state with default values
def init_session_state():
    defaults = {
        'ingredients_df': pd.DataFrame({
            'Nama_Barang': ['', '', '', '', ''],
            'Qty_Bahan': [0.0, 0.0, 0.0, 0.0, 0.0],
            'Satuan': ['gram', 'kg', 'ml', 'pcs', 'pcs'],
            'Qty_Jumlah': [0, 0, 0, 0, 0],
            'Harga': [0, 0, 0, 0, 0],
            'Subtotal': [0, 0, 0, 0, 0]
        }),
        'calculation_result': None,
        'output_units': 50,
        'target_margin': float(get_setting('default_margin', '40')),
        'actual_price': 0.0,
        'currency_symbol': get_setting('currency_symbol', 'Rp'),
        'operational_cost': 0.0,
        'other_cost': 0.0,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()


# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    # Currency symbol - menggunakan key untuk auto-bind session state
    st.text_input(
        "Currency symbol",
        key="currency_symbol"
    )

    # Target margin (default) - menggunakan key untuk auto-bind session state
    st.number_input(
        "Target margin default (%)",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        format="%.2f",
        key="target_margin",
        help="Margin default untuk perhitungan baru"
    )

    st.caption("Margin ini digunakan untuk menghitung harga jual yang disarankan.")

    st.divider()

    # Excel Template & Import
    st.markdown("### 📥 Excel Template & Import")

    # Download template button
    template_bytes = create_import_template()
    st.download_button(
        label="📋 Download Excel template",
        data=template_bytes,
        file_name="hpp_ingredient_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.markdown("**Upload Excel/CSV bahan (opsional)**")

    # File uploader
    uploaded_file = st.file_uploader(
        "Drag and drop file here",
        type=['xlsx', 'xls', 'csv'],
        help="Limit 200MB per file • XLSX, XLS, CSV",
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        # Parse the uploaded file
        file_content = uploaded_file.getvalue()
        ingredients, errors = parse_import_file(file_content, uploaded_file.name)

        if errors:
            for error in errors:
                st.error(error)

        if ingredients:
            # Convert to DataFrame dengan struktur baru dari parse_import_file
            # Format: nama_barang, qty_bahan, satuan, qty_jumlah, harga
            new_df = pd.DataFrame(ingredients)

            # Rename columns to match app DataFrame structure (capitalize)
            new_df = new_df.rename(columns={
                'nama_barang': 'Nama_Barang',
                'qty_bahan': 'Qty_Bahan',
                'satuan': 'Satuan',
                'qty_jumlah': 'Qty_Jumlah',
                'harga': 'Harga'
            })

            # Calculate subtotals: Qty_Jumlah × Harga
            new_df['Subtotal'] = new_df.apply(
                lambda row: round(float(row['Qty_Jumlah'] or 0) * float(row['Harga'] or 0), 0),
                axis=1
            )

            # Reorder columns
            new_df = new_df[['Nama_Barang', 'Qty_Bahan', 'Satuan', 'Qty_Jumlah', 'Harga', 'Subtotal']]

            # Add empty rows
            empty_rows = pd.DataFrame({
                'Nama_Barang': [''] * 2,
                'Qty_Bahan': [0.0] * 2,
                'Satuan': ['pcs'] * 2,
                'Qty_Jumlah': [0] * 2,
                'Harga': [0] * 2,
                'Subtotal': [0] * 2
            })
            st.session_state.ingredients_df = pd.concat([new_df, empty_rows], ignore_index=True)
            st.success(f"✅ {len(ingredients)} bahan berhasil diimport!")
            st.rerun()


# ===== MAIN CONTENT =====
st.markdown("# 🧠 AI HPP Calculator")
st.markdown("Hitung **HPP (Harga Pokok Produksi / COGS)** per porsi dengan cepat dan terstruktur.")

st.divider()

# ===== INPUT SECTION: Bahan & Biaya per Batch =====
st.markdown("### 📦 Bahan & Biaya per Batch")
st.markdown(
    "Isi atau sesuaikan tabel berikut dengan bahan yang digunakan untuk **1x batch produksi**. "
    "Anda juga bisa meng-upload dari Excel/CSV via sidebar."
)

# Editable data table
unit_options = format_unit_options()

# Function untuk menghitung subtotal sederhana
def calculate_subtotals(df):
    """
    Hitung subtotal untuk setiap baris.
    Formula: Subtotal = Qty_Jumlah × Harga

    Qty_Bahan dan Satuan hanya untuk referensi, tidak mempengaruhi kalkulasi subtotal.
    """
    df = df.copy()
    df['Subtotal'] = df.apply(
        lambda row: round(
            float(row['Qty_Jumlah'] or 0) * float(row['Harga'] or 0), 0
        ),
        axis=1
    )
    return df

# Callback untuk update ingredients saat data berubah
def on_ingredients_change():
    """Sync editor state ke ingredients_df dan hitung subtotal"""
    if "ingredients_editor" in st.session_state:
        editor_state = st.session_state.ingredients_editor
        df = st.session_state.ingredients_df.copy()

        # Kolom yang tidak boleh diedit manual (calculated fields)
        readonly_cols = ['Subtotal']

        # Apply edited rows
        if "edited_rows" in editor_state:
            for row_idx, changes in editor_state["edited_rows"].items():
                for col, val in changes.items():
                    if col not in readonly_cols:
                        df.at[int(row_idx), col] = val

        # Apply added rows
        if "added_rows" in editor_state and editor_state["added_rows"]:
            for new_row in editor_state["added_rows"]:
                # Fill defaults for missing columns
                complete_row = {
                    'Nama_Barang': new_row.get('Nama_Barang', ''),
                    'Qty_Bahan': new_row.get('Qty_Bahan', 0.0),
                    'Satuan': new_row.get('Satuan', 'pcs'),
                    'Qty_Jumlah': new_row.get('Qty_Jumlah', 0),
                    'Harga': new_row.get('Harga', 0),
                    'Subtotal': 0
                }
                df = pd.concat([df, pd.DataFrame([complete_row])], ignore_index=True)

        # Apply deleted rows
        if "deleted_rows" in editor_state and editor_state["deleted_rows"]:
            df = df.drop(index=editor_state["deleted_rows"]).reset_index(drop=True)

        # Recalculate subtotals: Qty_Jumlah × Harga
        df = calculate_subtotals(df)
        st.session_state.ingredients_df = df

# Pastikan subtotal dihitung sebelum display
st.session_state.ingredients_df = calculate_subtotals(st.session_state.ingredients_df)

# Tooltip penjelasan formula
st.caption("💡 **Subtotal** = Qty Jumlah × Harga (Qty Bahan & Satuan hanya untuk referensi)")

# Data editor dengan on_change callback - kolom compact
st.data_editor(
    st.session_state.ingredients_df,
    column_config={
        "Nama_Barang": st.column_config.TextColumn(
            "Nama Barang",
            help="Nama bahan/ingredient",
            max_chars=100,
            width=150
        ),
        "Qty_Bahan": st.column_config.NumberColumn(
            "Qty",
            help="Jumlah bahan per kemasan (contoh: 250 gram/bungkus)",
            min_value=0,
            format="%.1f",
            width=70
        ),
        "Satuan": st.column_config.SelectboxColumn(
            "Satuan",
            help="Satuan ukuran bahan",
            options=unit_options,
            width=80
        ),
        "Qty_Jumlah": st.column_config.NumberColumn(
            "Jml",
            help="Jumlah kemasan yang dibeli",
            min_value=0,
            format="%d",
            width=60
        ),
        "Harga": st.column_config.NumberColumn(
            "Harga",
            help="Harga per kemasan (Rp)",
            min_value=0,
            format="%d",
            width=90
        ),
        "Subtotal": st.column_config.NumberColumn(
            "Subtotal",
            help="Subtotal = Jml × Harga",
            format="%d",
            width=100,
            disabled=True
        )
    },
    column_order=["Nama_Barang", "Qty_Bahan", "Satuan", "Qty_Jumlah", "Harga", "Subtotal"],
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="ingredients_editor",
    on_change=on_ingredients_change
)

st.divider()

# ===== BIAYA OPERASIONAL & LAIN-LAIN =====
st.markdown("### 💼 Biaya Operasional & Lain-lain")
st.markdown("Tambahkan biaya di luar bahan baku seperti tenaga kerja, listrik, gas, packaging, dll.")

col_op1, col_op2 = st.columns(2)

with col_op1:
    st.number_input(
        "Biaya Operasional per Batch",
        min_value=0.0,
        step=1000.0,
        format="%.0f",
        help="Contoh: tenaga kerja, listrik, gas, air, sewa tempat",
        key="operational_cost"
    )

with col_op2:
    st.number_input(
        "Biaya Lain-lain per Batch",
        min_value=0.0,
        step=1000.0,
        format="%.0f",
        help="Contoh: packaging, label, overhead, transportasi",
        key="other_cost"
    )

st.divider()

# ===== OUTPUT SECTION: Output, Margin & Harga Jual =====
st.markdown("### 📦 Output, Margin & Harga Jual")

col1, col2, col3 = st.columns(3)

with col1:
    st.number_input(
        "Total porsi / unit yang dihasilkan per batch",
        min_value=1,
        step=1,
        help="Jumlah unit yang dihasilkan dari 1 batch produksi",
        key="output_units"
    )

with col2:
    # Target margin sudah di-bind via sidebar, tampilkan saja info
    st.markdown(f"**Target margin: {st.session_state.target_margin:.1f}%**")
    st.caption("Ubah di sidebar Settings")

with col3:
    st.number_input(
        "Harga jual saat ini per porsi (opsional)",
        min_value=0.0,
        step=1000.0,
        format="%.0f",
        help="Kosongkan jika belum ada harga jual",
        key="actual_price"
    )

st.markdown("")

# Calculate button
if st.button("🧮 Hitung HPP & Harga Jual", type="primary"):
    # Prepare ingredients data dari session state
    ingredients = []
    for _, row in st.session_state.ingredients_df.iterrows():
        if row['Nama_Barang'] and str(row['Nama_Barang']).strip():
            qty_bahan = float(row['Qty_Bahan']) if pd.notna(row['Qty_Bahan']) else 0
            qty_jumlah = int(row['Qty_Jumlah']) if pd.notna(row['Qty_Jumlah']) else 0
            harga = float(row['Harga']) if pd.notna(row['Harga']) else 0

            # Total bahan = Qty_Bahan × Qty_Jumlah (untuk perhitungan HPP)
            total_bahan = qty_bahan * qty_jumlah if qty_jumlah > 0 else qty_bahan

            ingredients.append({
                'name': str(row['Nama_Barang']).strip(),
                'quantity': total_bahan,  # Total bahan yang dipakai
                'unit': str(row['Satuan']) if pd.notna(row['Satuan']) else 'pcs',
                # price_per_unit = Harga / Qty_Bahan untuk per satuan bahan
                'price_per_unit': harga / qty_bahan if qty_bahan > 0 else harga
            })

    # Validate
    is_valid, errors = validate_ingredients(ingredients)

    if not is_valid:
        for error in errors:
            st.error(error)
    else:
        # Calculate
        result = calculate_all(
            ingredients=ingredients,
            output_units=st.session_state.output_units,
            target_margin_percent=st.session_state.target_margin,
            actual_selling_price=st.session_state.actual_price if st.session_state.actual_price > 0 else None,
            operational_cost=st.session_state.operational_cost,
            other_cost=st.session_state.other_cost
        )
        st.session_state.calculation_result = result
        st.rerun()

# Show info if no calculation yet
if st.session_state.calculation_result is None:
    st.info("ℹ️ Isi tabel bahan, total porsi, dan (opsional) harga jual saat ini, lalu klik tombol **Hitung HPP & Harga Jual**.")

st.divider()

# ===== RESULTS SECTION =====
if st.session_state.calculation_result is not None:
    result = st.session_state.calculation_result
    currency = st.session_state.currency_symbol

    # Success message
    st.success("Perhitungan berhasil ✅")

    # ===== Ringkasan Hasil =====
    st.markdown("### 📊 Ringkasan Hasil")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total biaya per batch",
            value=format_currency(result['total_batch_cost'], currency)
        )

    with col2:
        st.metric(
            label="HPP per porsi",
            value=format_currency(result['hpp_per_unit'], currency)
        )

    with col3:
        st.metric(
            label=f"Harga jual disarankan ({result['target_margin_percent']:.0f}% margin)",
            value=format_currency(result['suggested_selling_price'], currency)
        )

    # Breakdown biaya
    if result['operational_cost'] > 0 or result['other_cost'] > 0:
        st.markdown("**Breakdown Biaya per Batch:**")
        col_b1, col_b2, col_b3 = st.columns(3)

        with col_b1:
            st.markdown(f"• Bahan Baku: **{format_currency(result['material_cost'], currency)}**")

        with col_b2:
            st.markdown(f"• Operasional: **{format_currency(result['operational_cost'], currency)}**")

        with col_b3:
            st.markdown(f"• Lain-lain: **{format_currency(result['other_cost'], currency)}**")

    st.divider()

    # ===== Analisis Margin Saat Ini =====
    st.markdown("### 📈 Analisis Margin Saat Ini")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Harga jual saat ini",
            value=format_currency(result['actual_selling_price'], currency)
        )

    with col2:
        st.metric(
            label="Margin aktual (%)",
            value=f"{result['actual_margin_percent']:.1f}%"
        )

    with col3:
        st.metric(
            label="Gap vs target (persen poin)",
            value=format_gap(result['gap_vs_target'])
        )

    # Status indicator
    status = result['margin_status']
    if status == 'success':
        st.success("🟢 Margin sehat dan mendekati target.")
    elif status == 'warning':
        st.warning("🟡 Margin mendekati target, bisa dioptimalkan.")
    else:
        st.error("🔴 Margin di bawah target! Perlu evaluasi harga atau biaya.")

    st.divider()

    # ===== Detail Perhitungan per Bahan =====
    st.markdown("### 🔍 Detail Perhitungan per Bahan")

    # Create detail DataFrame
    detail_data = []
    for ing in result['ingredients']:
        detail_data.append({
            'Bahan': ing['name'],
            'Qty per batch': ing['quantity'],
            'Unit': ing['unit'],
            'Harga per unit': format_currency(ing['price_per_unit'], currency),
            'Total biaya': format_currency(ing['line_cost'], currency),
            'Kontribusi ke total HPP': f"{ing['contribution_percent']:.1f}%"
        })

    detail_df = pd.DataFrame(detail_data)
    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    st.divider()

    # ===== Top 3 Kontributor Biaya =====
    st.markdown("### 🏆 Top 3 Kontributor Biaya")

    top_contributors = get_top_contributors(result['ingredients'], 3)

    for ing in top_contributors:
        st.markdown(
            f"• **{ing['name']}**: {format_currency(ing['line_cost'], currency)} "
            f"({ing['contribution_percent']:.1f}% dari total biaya)"
        )

    st.divider()

    # ===== Export ke Excel =====
    st.markdown("### 📥 Export ke Excel")

    excel_bytes = create_excel_report(
        calculation_result=result,
        product_name="Produk",
        currency_symbol=currency
    )

    st.download_button(
        label="📋 Download HPP report (Excel)",
        data=excel_bytes,
        file_name=f"hpp_calculation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Footer
st.divider()
st.markdown(
    "<div style='text-align: center; color: #6B7280; font-size: 0.875rem;'>"
    "Dibuat oleh <a href='https://www.linkedin.com/in/irfan-yulianto/' target='_blank' style='color: #dc2626; text-decoration: none;'>Irfan Yulianto</a> © 2025"
    "</div>",
    unsafe_allow_html=True
)
