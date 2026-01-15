"""
History & Analytics Page - Riwayat Perhitungan HPP
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import (
    init_db, get_calculation_history, get_hpp_trend, get_unique_product_names
)
from utils.formatters import format_currency

# Page config
st.set_page_config(
    page_title="Riwayat HPP - AI HPP Calculator",
    page_icon="📊",
    layout="wide"
)

# Initialize database
init_db()

# Load custom CSS
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles", "main.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Header
st.title("📊 Riwayat Perhitungan HPP")
st.markdown("Lihat history perhitungan dan analisis tren HPP dari waktu ke waktu.")

# Get currency from settings
currency = st.session_state.get('currency_symbol', 'Rp')

# ===== FILTERS =====
col1, col2, col3 = st.columns(3)

with col1:
    mode_filter = st.selectbox(
        "Filter by Mode",
        options=["Semua", "produksi", "distributor", "service"]
    )

with col2:
    product_names = get_unique_product_names()
    product_filter = st.selectbox(
        "Filter by Produk",
        options=["Semua"] + product_names
    )

with col3:
    limit = st.number_input("Jumlah data", min_value=10, max_value=500, value=50, step=10)

st.divider()

# ===== HISTORY TABLE =====
st.markdown("### 📋 Riwayat Perhitungan")

# Get history data
mode_param = None if mode_filter == "Semua" else mode_filter
history = get_calculation_history(mode=mode_param, limit=limit)

if history:
    # Filter by product name if selected
    if product_filter != "Semua":
        history = [h for h in history if h['name'] == product_filter]

    if history:
        # Create DataFrame for display
        history_data = []
        for h in history:
            history_data.append({
                'Tanggal': h['created_at'][:10] if h['created_at'] else '-',
                'Nama': h['name'],
                'Mode': h['mode'].title(),
                'HPP/Unit': format_currency(h['hpp_per_unit'], currency),
                'Harga Jual': format_currency(h['suggested_price'], currency),
                'Total Cost': format_currency(h['total_cost'], currency),
                'Output': h['output_units'],
                'Margin': f"{h['margin_percent']:.1f}%"
            })

        st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)

        st.divider()

        # ===== HPP TREND CHART =====
        st.markdown("### 📈 Tren HPP per Produk")

        if product_filter != "Semua":
            trend_data = get_hpp_trend(product_filter, days=90)
            if trend_data:
                trend_df = pd.DataFrame(trend_data, columns=['Tanggal', 'HPP'])
                trend_df['Tanggal'] = pd.to_datetime(trend_df['Tanggal'])
                trend_df = trend_df.set_index('Tanggal')

                st.line_chart(trend_df, use_container_width=True)
            else:
                st.info("Belum ada data tren untuk produk ini.")
        else:
            st.info("Pilih produk spesifik di filter untuk melihat tren HPP.")

        st.divider()

        # ===== SUMMARY STATS =====
        st.markdown("### 📊 Ringkasan Statistik")

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)

        with col_s1:
            st.metric("Total Perhitungan", len(history))

        with col_s2:
            avg_hpp = sum(h['hpp_per_unit'] for h in history) / len(history)
            st.metric("Rata-rata HPP", format_currency(avg_hpp, currency))

        with col_s3:
            avg_margin = sum(h['margin_percent'] for h in history) / len(history)
            st.metric("Rata-rata Margin", f"{avg_margin:.1f}%")

        with col_s4:
            total_cost = sum(h['total_cost'] for h in history)
            st.metric("Total Cost", format_currency(total_cost, currency))

        st.divider()

        # ===== MODE DISTRIBUTION =====
        st.markdown("### 🥧 Distribusi per Mode")

        mode_counts = {}
        for h in history:
            mode = h['mode'].title()
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

        mode_df = pd.DataFrame(list(mode_counts.items()), columns=['Mode', 'Count'])
        st.bar_chart(mode_df.set_index('Mode'), use_container_width=True)

    else:
        st.info("Tidak ada data yang cocok dengan filter.")
else:
    st.info("Belum ada riwayat perhitungan. Lakukan perhitungan di halaman utama dan simpan untuk melihat riwayat di sini.")

# Footer
st.divider()
st.markdown(
    "<div style='text-align: center; color: var(--muted-foreground); font-size: 0.875rem;'>"
    "Dibuat oleh <a href='https://www.linkedin.com/in/irfan-yulianto/' target='_blank' style='color: var(--primary); text-decoration: none;'>Irfan Yulianto</a> © 2025"
    "</div>",
    unsafe_allow_html=True
)
