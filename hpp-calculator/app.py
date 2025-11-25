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

# Initialize session state
def init_session_state():
    if 'ingredients_df' not in st.session_state:
        st.session_state.ingredients_df = pd.DataFrame({
            'Ingredient': ['', '', '', '', ''],
            'Qty_per_batch': [0.0, 0.0, 0.0, 0.0, 0.0],
            'Unit': ['kg', 'kg', 'liter', 'pack', 'pack'],
            'Price_per_unit': [0, 0, 0, 0, 0]
        })

    if 'calculation_result' not in st.session_state:
        st.session_state.calculation_result = None

    if 'output_units' not in st.session_state:
        st.session_state.output_units = 50

    if 'target_margin' not in st.session_state:
        st.session_state.target_margin = float(get_setting('default_margin', '40'))

    if 'actual_price' not in st.session_state:
        st.session_state.actual_price = 0.0

    if 'currency_symbol' not in st.session_state:
        st.session_state.currency_symbol = get_setting('currency_symbol', 'Rp')

init_session_state()


# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    # Currency symbol
    currency_input = st.text_input(
        "Currency symbol",
        value=st.session_state.currency_symbol,
        key="currency_input"
    )
    if currency_input != st.session_state.currency_symbol:
        st.session_state.currency_symbol = currency_input

    # Target margin (default)
    st.number_input(
        "Target margin default (%)",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.target_margin,
        step=1.0,
        format="%.2f",
        key="sidebar_margin",
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
            # Convert to DataFrame
            new_df = pd.DataFrame(ingredients)
            new_df.columns = ['Ingredient', 'Qty_per_batch', 'Unit', 'Price_per_unit']

            # Add empty rows
            empty_rows = pd.DataFrame({
                'Ingredient': [''] * 2,
                'Qty_per_batch': [0.0] * 2,
                'Unit': ['kg'] * 2,
                'Price_per_unit': [0] * 2
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

edited_df = st.data_editor(
    st.session_state.ingredients_df,
    column_config={
        "Ingredient": st.column_config.TextColumn(
            "Ingredient",
            help="Nama bahan",
            max_chars=100,
            width="large"
        ),
        "Qty_per_batch": st.column_config.NumberColumn(
            "Qty_per_batch",
            help="Jumlah per batch",
            min_value=0,
            format="%.2f",
            width="medium"
        ),
        "Unit": st.column_config.SelectboxColumn(
            "Unit",
            help="Satuan",
            options=unit_options,
            width="small"
        ),
        "Price_per_unit": st.column_config.NumberColumn(
            "Price_per_unit",
            help="Harga per satuan",
            min_value=0,
            format="%d",
            width="medium"
        )
    },
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True
)

# Update session state with edited data
st.session_state.ingredients_df = edited_df

st.divider()

# ===== OUTPUT SECTION: Output, Margin & Harga Jual =====
st.markdown("### 📦 Output, Margin & Harga Jual")

col1, col2, col3 = st.columns(3)

with col1:
    output_units = st.number_input(
        "Total porsi / unit yang dihasilkan per batch",
        min_value=1,
        value=st.session_state.output_units,
        step=1,
        help="Jumlah unit yang dihasilkan dari 1 batch produksi"
    )
    st.session_state.output_units = output_units

with col2:
    target_margin = st.number_input(
        "Target margin (%) untuk perhitungan ini",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.target_margin,
        step=1.0,
        format="%.2f",
        help="Persentase margin yang diinginkan"
    )
    st.session_state.target_margin = target_margin

with col3:
    actual_price = st.number_input(
        "Harga jual saat ini per porsi (opsional)",
        min_value=0.0,
        value=st.session_state.actual_price,
        step=1000.0,
        format="%.0f",
        help="Kosongkan jika belum ada harga jual"
    )
    st.session_state.actual_price = actual_price

st.markdown("")

# Calculate button
if st.button("🧮 Hitung HPP & Harga Jual", type="primary"):
    # Prepare ingredients data
    ingredients = []
    for _, row in edited_df.iterrows():
        if row['Ingredient'] and str(row['Ingredient']).strip():
            ingredients.append({
                'name': str(row['Ingredient']).strip(),
                'quantity': float(row['Qty_per_batch']) if pd.notna(row['Qty_per_batch']) else 0,
                'unit': str(row['Unit']) if pd.notna(row['Unit']) else 'unit',
                'price_per_unit': float(row['Price_per_unit']) if pd.notna(row['Price_per_unit']) else 0
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
            actual_selling_price=st.session_state.actual_price if st.session_state.actual_price > 0 else None
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
