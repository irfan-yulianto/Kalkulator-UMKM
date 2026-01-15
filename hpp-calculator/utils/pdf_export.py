"""
PDF Export utilities for HPP Calculator.
Creates professional PDF reports for calculation results.
"""

import io
from datetime import datetime
from typing import Dict, List


def create_pdf_report(
    calculation_result: Dict,
    product_name: str = "Produk",
    currency_symbol: str = "Rp",
    mode: str = "produksi"
) -> bytes:
    """
    Create a professional PDF report for HPP calculation.
    
    Args:
        calculation_result: Dictionary containing calculation results
        product_name: Name of the product/service
        currency_symbol: Currency symbol to use
        mode: Calculator mode (produksi, distributor, service)
        
    Returns:
        PDF file as bytes
    """
    try:
        from fpdf import FPDF
    except ImportError:
        # Return empty bytes if fpdf not installed
        return b""
    
    class PDFReport(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 16)
            self.cell(0, 10, 'Laporan HPP - AI HPP Calculator', align='C', ln=True)
            self.set_font('Helvetica', '', 10)
            self.cell(0, 5, f'Tanggal: {datetime.now().strftime("%d/%m/%Y %H:%M")}', align='C', ln=True)
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.cell(0, 10, f'Halaman {self.page_no()}/{{nb}} | Dibuat oleh AI HPP Calculator', align='C')
    
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Format currency helper
    def fmt_currency(value):
        return f"{currency_symbol} {value:,.0f}".replace(",", ".")
    
    # ===== PRODUCT INFO =====
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, f'Produk: {product_name}', ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f'Mode: {mode.title()}', ln=True)
    pdf.ln(5)
    
    # ===== SUMMARY BOX =====
    pdf.set_fill_color(240, 248, 255)  # Light blue
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, 'RINGKASAN PERHITUNGAN', ln=True, fill=True)
    
    pdf.set_font('Helvetica', '', 11)
    
    if mode == "produksi":
        summary_items = [
            ("Total Biaya per Batch", fmt_currency(calculation_result.get('total_batch_cost', 0))),
            ("Jumlah Output", f"{calculation_result.get('output_units', 0)} porsi"),
            ("Target Margin", f"{calculation_result.get('target_margin_percent', 0):.1f}%"),
            ("", ""),
            ("HPP per Porsi", fmt_currency(calculation_result.get('hpp_per_unit', 0))),
            ("Harga Jual Disarankan", fmt_currency(calculation_result.get('suggested_selling_price', 0))),
        ]
    elif mode == "distributor":
        summary_items = [
            ("Harga Beli per Unit", fmt_currency(calculation_result.get('buy_price', 0))),
            ("Ongkir per Unit", fmt_currency(calculation_result.get('shipping_per_unit', 0))),
            ("Handling per Unit", fmt_currency(calculation_result.get('handling_per_unit', 0))),
            ("", ""),
            ("HPP per Unit", fmt_currency(calculation_result.get('hpp_per_unit', 0))),
            ("Harga Jual Disarankan", fmt_currency(calculation_result.get('suggested_selling_price', 0))),
            ("Profit per Unit", fmt_currency(calculation_result.get('profit_per_unit', 0))),
        ]
    else:  # service
        summary_items = [
            ("Durasi Layanan", f"{calculation_result.get('duration_minutes', 0):.0f} menit"),
            ("Biaya Tenaga Kerja", fmt_currency(calculation_result.get('labor_cost', 0))),
            ("Biaya Material", fmt_currency(calculation_result.get('material_cost', 0))),
            ("Biaya Alat", fmt_currency(calculation_result.get('equipment_cost', 0))),
            ("", ""),
            ("HPP per Layanan", fmt_currency(calculation_result.get('hpp_per_service', 0))),
            ("Harga Jual Disarankan", fmt_currency(calculation_result.get('suggested_selling_price', 0))),
        ]
    
    for label, value in summary_items:
        if label:
            pdf.cell(90, 8, label)
            pdf.cell(0, 8, value, ln=True)
        else:
            pdf.ln(3)
    
    pdf.ln(5)
    
    # ===== INGREDIENTS/PRODUCTS TABLE (for produksi mode) =====
    if mode == "produksi" and 'ingredients' in calculation_result:
        pdf.set_fill_color(226, 232, 240)  # Light gray
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, 'DETAIL BAHAN', ln=True, fill=True)
        
        # Table header
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(50, 8, 'Nama Bahan', 1)
        pdf.cell(25, 8, 'Qty', 1, align='C')
        pdf.cell(20, 8, 'Unit', 1, align='C')
        pdf.cell(35, 8, 'Harga/Unit', 1, align='R')
        pdf.cell(35, 8, 'Subtotal', 1, align='R')
        pdf.cell(25, 8, 'Kontribusi', 1, ln=True, align='R')
        
        # Table data
        pdf.set_font('Helvetica', '', 9)
        for ing in calculation_result['ingredients']:
            pdf.cell(50, 7, ing['name'][:25], 1)
            pdf.cell(25, 7, str(ing['quantity']), 1, align='C')
            pdf.cell(20, 7, ing['unit'], 1, align='C')
            pdf.cell(35, 7, fmt_currency(ing['price_per_unit']), 1, align='R')
            pdf.cell(35, 7, fmt_currency(ing['line_cost']), 1, align='R')
            pdf.cell(25, 7, f"{ing['contribution_percent']:.1f}%", 1, ln=True, align='R')
    
    pdf.ln(10)
    
    # ===== MARGIN ANALYSIS =====
    pdf.set_fill_color(254, 243, 199)  # Light yellow
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, 'ANALISIS MARGIN', ln=True, fill=True)
    
    pdf.set_font('Helvetica', '', 11)
    
    if 'actual_selling_price' in calculation_result:
        actual_price = calculation_result.get('actual_selling_price', 0)
        actual_margin = calculation_result.get('actual_margin_percent', 0)
        target_margin = calculation_result.get('target_margin_percent', 0)
        gap = calculation_result.get('gap_vs_target', 0)
        
        pdf.cell(90, 8, "Harga Jual Aktual")
        pdf.cell(0, 8, fmt_currency(actual_price), ln=True)
        pdf.cell(90, 8, "Margin Aktual")
        pdf.cell(0, 8, f"{actual_margin:.1f}%", ln=True)
        pdf.cell(90, 8, "Gap vs Target")
        pdf.cell(0, 8, f"{gap:+.1f} pp", ln=True)
        
        # Status
        pdf.ln(5)
        status = calculation_result.get('margin_status', 'warning')
        if status == 'success':
            pdf.set_text_color(22, 163, 74)  # Green
            pdf.cell(0, 8, "Status: Margin sehat dan mendekati target", ln=True)
        elif status == 'warning':
            pdf.set_text_color(202, 138, 4)  # Yellow
            pdf.cell(0, 8, "Status: Margin mendekati target, bisa dioptimalkan", ln=True)
        else:
            pdf.set_text_color(220, 38, 38)  # Red
            pdf.cell(0, 8, "Status: Margin di bawah target! Perlu evaluasi", ln=True)
        
        pdf.set_text_color(0, 0, 0)  # Reset to black
    
    # Save to bytes
    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output.getvalue()


def create_multi_product_pdf_report(
    results: List[Dict],
    title: str = "Laporan HPP Multi-Produk",
    currency_symbol: str = "Rp",
    mode: str = "distributor"
) -> bytes:
    """
    Create a PDF report for multiple products/services.
    
    Args:
        results: List of calculation result dictionaries
        title: Report title
        currency_symbol: Currency symbol
        mode: Calculator mode
        
    Returns:
        PDF file as bytes
    """
    try:
        from fpdf import FPDF
    except ImportError:
        return b""
    
    class PDFReport(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 16)
            self.cell(0, 10, title, align='C', ln=True)
            self.set_font('Helvetica', '', 10)
            self.cell(0, 5, f'Tanggal: {datetime.now().strftime("%d/%m/%Y %H:%M")}', align='C', ln=True)
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.cell(0, 10, f'Halaman {self.page_no()}/{{nb}} | AI HPP Calculator', align='C')
    
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    def fmt_currency(value):
        return f"{currency_symbol} {value:,.0f}".replace(",", ".")
    
    # Summary
    pdf.set_fill_color(240, 248, 255)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, f'RINGKASAN - {len(results)} Item', ln=True, fill=True)
    pdf.ln(5)
    
    # Table header
    pdf.set_font('Helvetica', 'B', 9)
    if mode == "distributor":
        pdf.cell(40, 8, 'Produk', 1)
        pdf.cell(30, 8, 'HPP/Unit', 1, align='R')
        pdf.cell(35, 8, 'Harga Jual', 1, align='R')
        pdf.cell(30, 8, 'Profit/Unit', 1, align='R')
        pdf.cell(35, 8, 'Investasi', 1, align='R')
        pdf.cell(20, 8, 'BEP', 1, ln=True, align='C')
    else:  # service
        pdf.cell(50, 8, 'Layanan', 1)
        pdf.cell(25, 8, 'Durasi', 1, align='C')
        pdf.cell(35, 8, 'HPP', 1, align='R')
        pdf.cell(35, 8, 'Harga Jual', 1, align='R')
        pdf.cell(35, 8, 'Profit', 1, ln=True, align='R')
    
    # Table data
    pdf.set_font('Helvetica', '', 9)
    total_investment = 0
    total_profit = 0
    
    for r in results:
        if mode == "distributor":
            name = r.get('product_name', 'Produk')[:20]
            pdf.cell(40, 7, name, 1)
            pdf.cell(30, 7, fmt_currency(r.get('hpp_per_unit', 0)), 1, align='R')
            pdf.cell(35, 7, fmt_currency(r.get('suggested_selling_price', 0)), 1, align='R')
            pdf.cell(30, 7, fmt_currency(r.get('profit_per_unit', 0)), 1, align='R')
            pdf.cell(35, 7, fmt_currency(r.get('total_investment', 0)), 1, align='R')
            pdf.cell(20, 7, str(r.get('breakeven_units', 0)), 1, ln=True, align='C')
            total_investment += r.get('total_investment', 0)
            total_profit += r.get('profit_per_unit', 0) * r.get('quantity', 1)
        else:  # service
            name = r.get('service_name', 'Layanan')[:25]
            pdf.cell(50, 7, name, 1)
            pdf.cell(25, 7, f"{r.get('duration_minutes', 0):.0f} min", 1, align='C')
            pdf.cell(35, 7, fmt_currency(r.get('hpp_per_service', 0)), 1, align='R')
            pdf.cell(35, 7, fmt_currency(r.get('suggested_selling_price', 0)), 1, align='R')
            pdf.cell(35, 7, fmt_currency(r.get('profit_per_service', 0)), 1, ln=True, align='R')
    
    # Totals
    pdf.ln(10)
    pdf.set_font('Helvetica', 'B', 11)
    if mode == "distributor":
        pdf.cell(90, 8, "Total Investasi:")
        pdf.cell(0, 8, fmt_currency(total_investment), ln=True)
        pdf.cell(90, 8, "Total Potensi Profit:")
        pdf.cell(0, 8, fmt_currency(total_profit), ln=True)
    
    # Save
    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output.getvalue()
