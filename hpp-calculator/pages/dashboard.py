"""
Dashboard Page - Overview of all HPP data
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import (
    init_db, get_product_templates, get_calculation_history, get_unique_product_names
)
from utils.formatters import format_currency

# Page config
st.set_page_config(
    page_title="Dashboard - AI HPP Calculator",
    page_icon="🏠",
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

# Get currency
currency = st.session_state.get('currency_symbol', 'Rp')

# Header
st.title("🏠 Dashboard")
st.markdown("Ringkasan dan overview data HPP Anda.")

st.divider()

# ===== SUMMARY METRICS =====
templates = get_product_templates()
history = get_calculation_history(limit=100)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📁 Produk Tersimpan", len(templates))

with col2:
    st.metric("📊 Total Perhitungan", len(history))

with col3:
    if history:
        avg_margin = sum(h['margin_percent'] for h in history) / len(history)
        st.metric("📈 Rata-rata Margin", f"{avg_margin:.1f}%")
    else:
        st.metric("📈 Rata-rata Margin", "N/A")

with col4:
    unique_products = get_unique_product_names()
    st.metric("🏷️ Produk Unik", len(unique_products))

st.divider()

# ===== PRODUCTS BY MODE =====
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📦 Produk per Mode")
    
    if templates:
        mode_counts = {}
        for t in templates:
            mode = t.get('mode', 'produksi').title()
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        mode_df = pd.DataFrame(list(mode_counts.items()), columns=['Mode', 'Jumlah'])
        st.bar_chart(mode_df.set_index('Mode'), use_container_width=True)
    else:
        st.info("Belum ada produk tersimpan.")

with col_right:
    st.markdown("### 📋 Produk Tersimpan Terbaru")
    
    if templates:
        recent = templates[:5]
        for t in recent:
            mode_icon = {"produksi": "🍳", "distributor": "📦", "service": "💼"}.get(t.get('mode', 'produksi'), "📄")
            st.markdown(f"- {mode_icon} **{t['name']}** ({t.get('mode', 'produksi').title()})")
    else:
        st.info("Belum ada produk tersimpan.")

st.divider()

# ===== TOP PRODUCTS BY HPP =====
st.markdown("### 🏆 Top 5 Produk dengan HPP Tertinggi")

if history:
    # Get unique latest calculations per product
    product_hpp = {}
    for h in history:
        name = h['name']
        if name not in product_hpp or h['hpp_per_unit'] > product_hpp[name]:
            product_hpp[name] = h['hpp_per_unit']
    
    # Sort and get top 5
    sorted_products = sorted(product_hpp.items(), key=lambda x: x[1], reverse=True)[:5]
    
    if sorted_products:
        top_data = []
        for name, hpp in sorted_products:
            top_data.append({
                'Produk': name,
                'HPP': format_currency(hpp, currency)
            })
        st.dataframe(pd.DataFrame(top_data), use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data.")
else:
    st.info("Belum ada riwayat perhitungan.")

st.divider()

# ===== MARGIN DISTRIBUTION =====
st.markdown("### 📊 Distribusi Margin")

if history:
    margins = [h['margin_percent'] for h in history]
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        low_margin = len([m for m in margins if m < 20])
        st.metric("❌ Margin < 20%", low_margin)
    
    with col_m2:
        mid_margin = len([m for m in margins if 20 <= m < 30])
        st.metric("⚠️ Margin 20-30%", mid_margin)
    
    with col_m3:
        good_margin = len([m for m in margins if 30 <= m < 50])
        st.metric("✅ Margin 30-50%", good_margin)
    
    with col_m4:
        high_margin = len([m for m in margins if m >= 50])
        st.metric("🚀 Margin > 50%", high_margin)
else:
    st.info("Belum ada data untuk analisis margin.")

st.divider()

# ===== RECENT CALCULATIONS =====
st.markdown("### 🕒 Perhitungan Terakhir")

if history:
    recent_history = history[:10]
    history_data = []
    for h in recent_history:
        history_data.append({
            'Tanggal': h['created_at'][:10] if h['created_at'] else '-',
            'Nama': h['name'],
            'Mode': h.get('mode', 'produksi').title(),
            'HPP': format_currency(h['hpp_per_unit'], currency),
            'Margin': f"{h['margin_percent']:.1f}%"
        })
    
    st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)
else:
    st.info("Belum ada riwayat perhitungan. Lakukan perhitungan di halaman utama.")

# Footer
st.divider()
st.markdown(
    "<div style='text-align: center; color: var(--muted-foreground); font-size: 0.875rem;'>"
    "Dibuat oleh <a href='https://www.linkedin.com/in/irfan-yulianto/' target='_blank' style='color: var(--primary); text-decoration: none;'>Irfan Yulianto</a> © 2025"
    "</div>",
    unsafe_allow_html=True
)
