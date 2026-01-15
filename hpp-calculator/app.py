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
from utils.export import create_excel_report, create_import_template, parse_import_file, create_distributor_template, create_service_template
from utils.pdf_export import create_pdf_report, create_multi_product_pdf_report
from utils.calc_distributor import calculate_distributor_hpp, validate_distributor_inputs
from utils.calc_service import calculate_service_hpp, validate_service_inputs
from database.db import (
    init_db, get_setting, set_setting, 
    save_product_template, get_product_templates, delete_product_template, get_product_template_by_id,
    save_calculation_history, get_calculation_history, get_hpp_trend, get_unique_product_names
)

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

    # ===== PRODUK TERSIMPAN (Save/Load) =====
    st.markdown("### 📁 Produk Tersimpan")

    # Get saved templates
    saved_templates = get_product_templates()

    if saved_templates:
        template_options = {t['name']: t['id'] for t in saved_templates}
        selected_template_name = st.selectbox(
            "Pilih produk tersimpan",
            options=["-- Pilih --"] + list(template_options.keys()),
            key="selected_template"
        )

        col_load, col_delete = st.columns(2)

        with col_load:
            if st.button("📂 Load", use_container_width=True, disabled=(selected_template_name == "-- Pilih --")):
                if selected_template_name != "-- Pilih --":
                    template_id = template_options[selected_template_name]
                    template = get_product_template_by_id(template_id)
                    if template:
                        import json
                        try:
                            loaded_data = json.loads(template['data_json'])
                            mode = template.get('mode', 'produksi')

                            if mode == 'produksi':
                                # Load to ingredients_df
                                st.session_state.ingredients_df = pd.DataFrame(loaded_data)
                                st.session_state.output_units = template.get('output_units', 50)
                            elif mode == 'distributor':
                                st.session_state.distributor_df = pd.DataFrame(loaded_data)
                            elif mode == 'service':
                                st.session_state.service_df = pd.DataFrame(loaded_data)

                            st.success(f"✅ '{selected_template_name}' loaded!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error loading: {e}")

        with col_delete:
            if st.button("🗑️ Hapus", use_container_width=True, disabled=(selected_template_name == "-- Pilih --")):
                if selected_template_name != "-- Pilih --":
                    template_id = template_options[selected_template_name]
                    if delete_product_template(template_id):
                        st.success(f"✅ '{selected_template_name}' dihapus!")
                        st.rerun()
    else:
        st.caption("Belum ada produk tersimpan.")

    st.divider()

    # Excel Template & Import
    st.markdown("### 📥 Excel Templates")

    # Production template
    template_bytes = create_import_template()
    st.download_button(
        label="🍳 Template Produksi (F&B)",
        data=template_bytes,
        file_name="hpp_produksi_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    # Distributor template
    distributor_template = create_distributor_template()
    st.download_button(
        label="📦 Template Distributor",
        data=distributor_template,
        file_name="hpp_distributor_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    # Service template
    service_template = create_service_template()
    st.download_button(
        label="💼 Template Jasa/Service",
        data=service_template,
        file_name="hpp_service_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()

    st.markdown("### 📤 Import Data")

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

# ===== MODE SELECTOR =====
calc_mode = st.radio(
    "Pilih Mode Kalkulator",
    options=["🍳 Produksi (F&B)", "📦 Distributor/Reseller", "💼 Jasa/Service"],
    horizontal=True,
    help="Pilih mode sesuai jenis bisnis Anda"
)

st.divider()

# ===== MODE: PRODUKSI (F&B) =====
if calc_mode == "🍳 Produksi (F&B)":
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

        # ===== Break-Even Analysis =====
        st.markdown("### 📊 Break-Even Analysis")
        
        # Calculate break-even
        fixed_costs = result.get('operational_cost', 0) + result.get('other_cost', 0)
        variable_cost_per_unit = result.get('material_cost', result['total_batch_cost']) / result['output_units']
        selling_price = result['actual_selling_price']
        
        if selling_price > variable_cost_per_unit:
            contribution_margin = selling_price - variable_cost_per_unit
            breakeven_units = int(fixed_costs / contribution_margin) if fixed_costs > 0 else 0
            
            col_be1, col_be2, col_be3 = st.columns(3)
            with col_be1:
                st.metric("Break-Even Point", f"{breakeven_units} unit")
            with col_be2:
                st.metric("Contribution Margin", format_currency(contribution_margin, currency))
            with col_be3:
                profit_at_output = (selling_price - result['hpp_per_unit']) * result['output_units']
                st.metric("Profit per Batch", format_currency(profit_at_output, currency))
            
            # Visual progress
            if breakeven_units > 0:
                progress = min(result['output_units'] / breakeven_units, 1.0) if breakeven_units > 0 else 1.0
                st.progress(progress, text=f"Output: {result['output_units']} / BEP: {breakeven_units} unit")
        else:
            st.warning("⚠️ Harga jual lebih rendah dari biaya variabel per unit!")

        st.divider()

        # ===== What-If Analysis =====
        with st.expander("🔮 What-If Analysis (Simulasi)", expanded=False):
            st.markdown("Simulasikan dampak perubahan biaya terhadap HPP dan harga jual.")
            
            col_w1, col_w2 = st.columns(2)
            
            with col_w1:
                cost_change = st.slider(
                    "Perubahan Biaya Bahan (%)",
                    min_value=-50,
                    max_value=100,
                    value=0,
                    step=5,
                    key="whatif_cost_change"
                )
            
            with col_w2:
                margin_change = st.slider(
                    "Target Margin Baru (%)",
                    min_value=5.0,
                    max_value=80.0,
                    value=float(result['target_margin_percent']),
                    step=5.0,
                    key="whatif_margin"
                )
            
            # Calculate what-if scenario
            new_batch_cost = result['total_batch_cost'] * (1 + cost_change / 100)
            new_hpp = new_batch_cost / result['output_units']
            new_selling_price = new_hpp / (1 - margin_change / 100)
            
            col_r1, col_r2, col_r3 = st.columns(3)
            
            with col_r1:
                hpp_diff = new_hpp - result['hpp_per_unit']
                st.metric(
                    "HPP Baru",
                    format_currency(new_hpp, currency),
                    delta=f"{hpp_diff:+,.0f}".replace(",", "."),
                    delta_color="inverse"
                )
            
            with col_r2:
                price_diff = new_selling_price - result['suggested_selling_price']
                st.metric(
                    "Harga Jual Baru",
                    format_currency(new_selling_price, currency),
                    delta=f"{price_diff:+,.0f}".replace(",", ".")
                )
            
            with col_r3:
                new_profit = new_selling_price - new_hpp
                old_profit = result['suggested_selling_price'] - result['hpp_per_unit']
                profit_diff = new_profit - old_profit
                st.metric(
                    "Profit per Unit",
                    format_currency(new_profit, currency),
                    delta=f"{profit_diff:+,.0f}".replace(",", ".")
                )

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
        st.markdown("### 📥 Export")

        excel_bytes = create_excel_report(
            calculation_result=result,
            product_name="Produk",
            currency_symbol=currency
        )

        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            st.download_button(
                label="📋 Download Excel",
                data=excel_bytes,
                file_name=f"hpp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col_exp2:
            pdf_bytes = create_pdf_report(
                calculation_result=result,
                product_name="Produk",
                currency_symbol=currency,
                mode="produksi"
            )
            if pdf_bytes:
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_bytes,
                    file_name=f"hpp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        st.divider()

        # ===== Simpan Produk =====
        st.markdown("### 💾 Simpan Produk")
        save_name = st.text_input("Nama produk untuk disimpan", placeholder="Contoh: Nasi Goreng Spesial", key="save_produksi_name")
        
        if st.button("💾 Simpan Produk", type="primary", disabled=not save_name):
            import json
            data_to_save = st.session_state.ingredients_df.to_dict('records')
            template_id = save_product_template(
                name=save_name,
                mode="produksi",
                data_json=json.dumps(data_to_save),
                output_units=st.session_state.output_units,
                target_margin=st.session_state.target_margin
            )
            # Also save to calculation history
            save_calculation_history(
                name=save_name,
                mode="produksi",
                hpp_per_unit=result['hpp_per_unit'],
                suggested_price=result['suggested_selling_price'],
                total_cost=result['total_batch_cost'],
                output_units=result['output_units'],
                margin_percent=result['target_margin_percent'],
                data_json=json.dumps(data_to_save)
            )
            st.success(f"✅ Produk '{save_name}' berhasil disimpan!")
            st.rerun()

# ===== MODE: DISTRIBUTOR/RESELLER =====
elif calc_mode == "📦 Distributor/Reseller":
    st.markdown("### 📦 Kalkulator HPP Distributor/Reseller")
    st.markdown("Hitung HPP untuk barang yang dibeli dari supplier untuk dijual kembali.")
    st.caption(f"💡 Target margin: **{st.session_state.target_margin:.1f}%** (ubah di sidebar Settings)")

    # Initialize session state for distributor
    if 'distributor_df' not in st.session_state:
        st.session_state.distributor_df = pd.DataFrame({
            'Nama_Produk': ['', '', ''],
            'Harga_Beli': [0, 0, 0],
            'Quantity': [1, 1, 1],
            'Ongkir': [0, 0, 0],
            'Handling': [0, 0, 0]
        })
    if 'distributor_results' not in st.session_state:
        st.session_state.distributor_results = None

    # Data editor for multiple products
    st.data_editor(
        st.session_state.distributor_df,
        column_config={
            "Nama_Produk": st.column_config.TextColumn("Nama Produk", width=150),
            "Harga_Beli": st.column_config.NumberColumn("Harga Beli/Unit", min_value=0, format="%d", width=110),
            "Quantity": st.column_config.NumberColumn("Qty", min_value=1, format="%d", width=60),
            "Ongkir": st.column_config.NumberColumn("Total Ongkir", min_value=0, format="%d", width=100),
            "Handling": st.column_config.NumberColumn("Handling", min_value=0, format="%d", width=90)
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="distributor_editor"
    )

    # Sync editor state
    if "distributor_editor" in st.session_state:
        editor_state = st.session_state.distributor_editor
        df = st.session_state.distributor_df.copy()
        if "edited_rows" in editor_state:
            for row_idx, changes in editor_state["edited_rows"].items():
                for col, val in changes.items():
                    df.at[int(row_idx), col] = val
        if "added_rows" in editor_state and editor_state["added_rows"]:
            for new_row in editor_state["added_rows"]:
                complete_row = {
                    'Nama_Produk': new_row.get('Nama_Produk', ''),
                    'Harga_Beli': new_row.get('Harga_Beli', 0),
                    'Quantity': new_row.get('Quantity', 1),
                    'Ongkir': new_row.get('Ongkir', 0),
                    'Handling': new_row.get('Handling', 0)
                }
                df = pd.concat([df, pd.DataFrame([complete_row])], ignore_index=True)
        if "deleted_rows" in editor_state and editor_state["deleted_rows"]:
            df = df.drop(index=editor_state["deleted_rows"]).reset_index(drop=True)
        st.session_state.distributor_df = df

    st.markdown("")

    if st.button("🧮 Hitung HPP Distributor", type="primary"):
        results = []
        has_error = False
        for _, row in st.session_state.distributor_df.iterrows():
            if row['Nama_Produk'] and str(row['Nama_Produk']).strip() and row['Harga_Beli'] > 0:
                result = calculate_distributor_hpp(
                    buy_price=float(row['Harga_Beli']),
                    quantity=int(row['Quantity']) if row['Quantity'] > 0 else 1,
                    shipping_cost=float(row['Ongkir']) if pd.notna(row['Ongkir']) else 0,
                    handling_cost=float(row['Handling']) if pd.notna(row['Handling']) else 0,
                    target_margin_percent=st.session_state.target_margin
                )
                result['product_name'] = str(row['Nama_Produk']).strip()
                results.append(result)

        if not results:
            st.error("Minimal 1 produk dengan nama dan harga beli harus diisi.")
        else:
            st.session_state.distributor_results = results
            st.rerun()

    if st.session_state.distributor_results is None:
        st.info("ℹ️ Isi tabel produk di atas, lalu klik **Hitung HPP Distributor**.")
    else:
        results = st.session_state.distributor_results
        currency = st.session_state.currency_symbol

        st.success(f"Perhitungan berhasil untuk {len(results)} produk ✅")

        # Create results table
        results_data = []
        total_investment = 0
        total_potential_profit = 0
        for r in results:
            results_data.append({
                'Produk': r['product_name'],
                'HPP/Unit': format_currency(r['hpp_per_unit'], currency),
                'Harga Jual': format_currency(r['suggested_selling_price'], currency),
                'Profit/Unit': format_currency(r['profit_per_unit'], currency),
                'Investasi': format_currency(r['total_investment'], currency),
                'Breakeven': f"{r['breakeven_units']} unit"
            })
            total_investment += r['total_investment']
            total_potential_profit += r['profit_per_unit'] * r['quantity']

        st.dataframe(pd.DataFrame(results_data), use_container_width=True, hide_index=True)

        st.divider()
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Total Investasi", format_currency(total_investment, currency))
        with col_s2:
            st.metric("Total Potensi Profit", format_currency(total_potential_profit, currency))

        st.divider()

        # ===== Simpan Produk Distributor =====
        st.markdown("### 💾 Simpan Data")
        save_name = st.text_input("Nama untuk disimpan", placeholder="Contoh: Stok Januari 2026", key="save_distributor_name")
        
        if st.button("💾 Simpan", type="primary", disabled=not save_name, key="save_dist_btn"):
            import json
            data_to_save = st.session_state.distributor_df.to_dict('records')
            save_product_template(
                name=save_name,
                mode="distributor",
                data_json=json.dumps(data_to_save),
                output_units=1,
                target_margin=st.session_state.target_margin
            )
            # Save to history
            avg_hpp = sum(r['hpp_per_unit'] for r in results) / len(results)
            save_calculation_history(
                name=save_name,
                mode="distributor",
                hpp_per_unit=avg_hpp,
                suggested_price=sum(r['suggested_selling_price'] for r in results) / len(results),
                total_cost=total_investment,
                output_units=len(results),
                margin_percent=st.session_state.target_margin,
                data_json=json.dumps(data_to_save)
            )
            st.success(f"✅ '{save_name}' berhasil disimpan!")
            st.rerun()

# ===== MODE: JASA/SERVICE =====
elif calc_mode == "💼 Jasa/Service":
    st.markdown("### 💼 Kalkulator HPP Jasa/Service")
    st.markdown("Hitung HPP untuk layanan berdasarkan waktu kerja dan material.")
    st.caption(f"💡 Target margin: **{st.session_state.target_margin:.1f}%** (ubah di sidebar Settings)")

    # Initialize session state for service
    if 'service_df' not in st.session_state:
        st.session_state.service_df = pd.DataFrame({
            'Nama_Layanan': ['', '', ''],
            'Durasi_Menit': [60, 60, 60],
            'Tarif_Jam': [50000, 50000, 50000],
            'Material': [0, 0, 0],
            'Alat': [0, 0, 0]
        })
    if 'service_results' not in st.session_state:
        st.session_state.service_results = None

    # Data editor for multiple services
    st.data_editor(
        st.session_state.service_df,
        column_config={
            "Nama_Layanan": st.column_config.TextColumn("Nama Layanan", width=150),
            "Durasi_Menit": st.column_config.NumberColumn("Durasi (menit)", min_value=1, format="%d", width=100),
            "Tarif_Jam": st.column_config.NumberColumn("Tarif/Jam", min_value=0, format="%d", width=100),
            "Material": st.column_config.NumberColumn("Material", min_value=0, format="%d", width=90),
            "Alat": st.column_config.NumberColumn("Alat", min_value=0, format="%d", width=80)
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="service_editor"
    )

    # Sync editor state
    if "service_editor" in st.session_state:
        editor_state = st.session_state.service_editor
        df = st.session_state.service_df.copy()
        if "edited_rows" in editor_state:
            for row_idx, changes in editor_state["edited_rows"].items():
                for col, val in changes.items():
                    df.at[int(row_idx), col] = val
        if "added_rows" in editor_state and editor_state["added_rows"]:
            for new_row in editor_state["added_rows"]:
                complete_row = {
                    'Nama_Layanan': new_row.get('Nama_Layanan', ''),
                    'Durasi_Menit': new_row.get('Durasi_Menit', 60),
                    'Tarif_Jam': new_row.get('Tarif_Jam', 50000),
                    'Material': new_row.get('Material', 0),
                    'Alat': new_row.get('Alat', 0)
                }
                df = pd.concat([df, pd.DataFrame([complete_row])], ignore_index=True)
        if "deleted_rows" in editor_state and editor_state["deleted_rows"]:
            df = df.drop(index=editor_state["deleted_rows"]).reset_index(drop=True)
        st.session_state.service_df = df

    st.markdown("")

    if st.button("🧮 Hitung HPP Jasa", type="primary"):
        results = []
        for _, row in st.session_state.service_df.iterrows():
            if row['Nama_Layanan'] and str(row['Nama_Layanan']).strip():
                result = calculate_service_hpp(
                    duration_minutes=float(row['Durasi_Menit']) if row['Durasi_Menit'] > 0 else 60,
                    labor_rate_per_hour=float(row['Tarif_Jam']) if pd.notna(row['Tarif_Jam']) else 0,
                    material_cost=float(row['Material']) if pd.notna(row['Material']) else 0,
                    equipment_cost=float(row['Alat']) if pd.notna(row['Alat']) else 0,
                    target_margin_percent=st.session_state.target_margin
                )
                result['service_name'] = str(row['Nama_Layanan']).strip()
                results.append(result)

        if not results:
            st.error("Minimal 1 layanan dengan nama harus diisi.")
        else:
            st.session_state.service_results = results
            st.rerun()

    if st.session_state.service_results is None:
        st.info("ℹ️ Isi tabel layanan di atas, lalu klik **Hitung HPP Jasa**.")
    else:
        results = st.session_state.service_results
        currency = st.session_state.currency_symbol

        st.success(f"Perhitungan berhasil untuk {len(results)} layanan ✅")

        # Create results table
        results_data = []
        for r in results:
            results_data.append({
                'Layanan': r['service_name'],
                'Durasi': f"{r['duration_minutes']:.0f} menit",
                'HPP': format_currency(r['hpp_per_service'], currency),
                'Harga Jual': format_currency(r['suggested_selling_price'], currency),
                'Profit': format_currency(r['profit_per_service'], currency)
            })

        st.dataframe(pd.DataFrame(results_data), use_container_width=True, hide_index=True)

        st.divider()

        # Show average metrics
        avg_hpp = sum(r['hpp_per_service'] for r in results) / len(results)
        avg_profit = sum(r['profit_per_service'] for r in results) / len(results)
        avg_hourly = sum(r['potential_hourly_profit'] for r in results) / len(results)

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("Rata-rata HPP", format_currency(avg_hpp, currency))
        with col_s2:
            st.metric("Rata-rata Profit", format_currency(avg_profit, currency))
        with col_s3:
            st.metric("Rata-rata Profit/Jam", format_currency(avg_hourly, currency))

        st.divider()

        # ===== Simpan Layanan =====
        st.markdown("### 💾 Simpan Data")
        save_name = st.text_input("Nama untuk disimpan", placeholder="Contoh: Daftar Layanan Salon", key="save_service_name")
        
        if st.button("💾 Simpan", type="primary", disabled=not save_name, key="save_svc_btn"):
            import json
            data_to_save = st.session_state.service_df.to_dict('records')
            save_product_template(
                name=save_name,
                mode="service",
                data_json=json.dumps(data_to_save),
                output_units=len(results),
                target_margin=st.session_state.target_margin
            )
            # Save to history
            save_calculation_history(
                name=save_name,
                mode="service",
                hpp_per_unit=avg_hpp,
                suggested_price=sum(r['suggested_selling_price'] for r in results) / len(results),
                total_cost=sum(r['hpp_per_service'] for r in results),
                output_units=len(results),
                margin_percent=st.session_state.target_margin,
                data_json=json.dumps(data_to_save)
            )
            st.success(f"✅ '{save_name}' berhasil disimpan!")
            st.rerun()

# Footer
st.divider()
st.markdown(
    "<div style='text-align: center; color: var(--muted-foreground); font-size: 0.875rem;'>"
    "Dibuat oleh <a href='https://www.linkedin.com/in/irfan-yulianto/' target='_blank' style='color: var(--primary); text-decoration: none;'>Irfan Yulianto</a> © 2025"
    "</div>",
    unsafe_allow_html=True
)
