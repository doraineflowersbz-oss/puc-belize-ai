import os
import streamlit as st
from google import generativeai as genai
from PIL import Image
import json
import re

# Herramientas de ReportLab para la exportación del paquete PUC en PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="PUC Belize AI Engine Pro", layout="wide")
st.title("⚡ Sistema de Ingeniería Eléctrica Automatizado - PUC Belize")
st.subheader("Cálculos y planos con cumplimiento estricto del NEC 2023 sin alucinaciones")

api_key = st.sidebar.text_input("Introduce tu Gemini API Key:", type="password")

# --- MOTOR DE REGLAS MATEMÁTICAS ESTÁTICAS NEC 2023 (CERO ALUCINACIONES) ---
def run_nec_2023_engine(raw_data, facility_type):
    calcs = {}
    
    # Datos base extraídos del plano
    area = float(raw_data.get('area_sqft', 0))
    outlets = int(raw_data.get('outlet_count', 0))
    ac_va = float(raw_data.get('ac_total_va', 0))
    
    if facility_type == "Dwelling (Residencial)":
        # NEC 2023 Art. 220.11 & 220.14: Carga general de iluminación y tomacorrientes (3 VA por sq ft)
        general_load = area * 3.0
        # NEC 2023 Art. 220.52: Circuitos de pequeños electrodomésticos y lavandería (1500 VA c/u)
        appliance_load = 3000.0 + 1500.0  # 2 de cocina + 1 de lavandería obligatorios
        
        total_connected_general = general_load + appliance_load
        
        # Aplicación estricta de Factores de Demanda (NEC 2023 Tabla 220.42)
        if total_connected_general <= 3000:
            demand_general = total_connected_general
        elif total_connected_general <= 120000:
            demand_general = 3000 + ((total_connected_general - 3000) * 0.35)
        else:
            demand_general = 3000 + (117000 * 0.35) + ((total_connected_general - 120000) * 0.25)
            
        # NEC 2023 Art. 220.50 & 440.32: Carga de Climatización (A/C) al 100%
        total_calculated_va = demand_general + ac_va
        # Servicio residencial monofásico estándar 120/240V en Belice
        feeder_amps = total_calculated_va / 240.0
        
    else:
        # Non-Dwelling (Comercial / Oficinas)
        # NEC 2023 Tabla 220.12: Carga de iluminación comercial basada en área (Ej: 3.5 VA/sq ft)
        lighting_va = area * 3.5
        # NEC 2023 Art. 220.14(I): Tomacorrientes comerciales a 180 VA por salida dúplex
        receptacle_va = outlets * 180.0
        
        # NEC 2023 Tabla 220.44: Factor de demanda comercial para tomacorrientes
        if receptacle_va <= 10000:
            demand_receptacles = receptacle_va
        else:
            demand_receptacles = 10000 + ((receptacle_va - 10000) * 0.5)
            
        # NEC 2023 Art. 440.32: Carga continua de A/C comercial dimensionada al 125%
        ac_continuous_load = ac_va * 1.25
        total_calculated_va = lighting_va + demand_receptacles + ac_continuous_load
        # Servicio comercial trifásico estándar 115/230V en Belice
        feeder_amps = total_calculated_va / (230.0 * 1.732)
        
    calcs['total_va'] = total_calculated_va
    calcs['feeder_amps'] = feeder_amps
    
    # NEC 2023 Art. 240.6(A): Tamaños estándar de interruptores automáticos (Breakers)
    standard_breakers =
    calcs['main_breaker'] = next((x for x in standard_breakers if x >= feeder_amps), 400)
    
    # NEC 2023 Tabla 310.16: Ampacidad de conductores de Cobre (THHN a 75°C)
    if calcs['main_breaker'] <= 15: calcs['feeder_wire'] = "2x #14 AWG CU THHN"
    elif calcs['main_breaker'] <= 20: calcs['feeder_wire'] = "2x #12 AWG CU THHN"
    elif calcs['main_breaker'] <= 30: calcs['feeder_wire'] = "2x #10 AWG CU THHN"
    elif calcs['main_breaker'] <= 50: calcs['feeder_wire'] = "2x #8 AWG CU THHN"
    elif calcs['main_breaker'] <= 65: calcs['feeder_wire'] = "2x #6 AWG CU THHN"
    elif calcs['main_breaker'] <= 85: calcs['feeder_wire'] = "2x #4 AWG CU THHN"
    elif calcs['main_breaker'] <= 115: calcs['feeder_wire'] = "2x #2 AWG CU THHN"
    elif calcs['main_breaker'] <= 130: calcs['feeder_wire'] = "2x #1 AWG CU THHN"
    elif calcs['main_breaker'] <= 150: calcs['feeder_wire'] = "2x #1/0 AWG CU THHN"
    elif calcs['main_breaker'] <= 200: calcs['feeder_wire'] = "2x #3/0 AWG CU THHN"
    elif calcs['main_breaker'] <= 225: calcs['feeder_wire'] = "2x #4/0 AWG CU THHN"
    else: calcs['feeder_wire'] = "Paralelo: 2x(3x #250 kcmil CU THHN)"
    
    return calcs

# --- GENERADOR DEL REPORTE FÍSICO EN PDF ---
def build_puc_pdf_package(facility_type, raw_data, calcs):
    pdf_path = "puc_belize_submission_package.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#002855'), alignment=1, spaceAfter=20)
    h2_style = ParagraphStyle('SecTitle', parent=styles['Heading2'], fontSize=11, leading=15, textColor=colors.HexColor('#0056B3'), spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['BodyText'], fontSize=9, leading=13)
    
    story = []
    
    # PÁGINA 1: HOJA DE CÁLCULO DE ACOMETIDA
    story.append(Paragraph("PUBLIC UTILITIES COMMISSION (PUC) OF BELIZE", title_style))
    story.append(Paragraph(f"<b>FEEDER SERVICE LOAD CALCULATION SHEET - {facility_type.upper()}</b>", h2_style))
    story.append(Spacer(1, 10))
    
    table_data = [
        [Paragraph("<b>Concepto Eléctrico</b>", body_style), Paragraph("<b>Valor Extraído / Calculado</b>", body_style), Paragraph("<b>Referencia NEC 2023</b>", body_style)],
        [Paragraph("Área Total de la Infraestructura", body_style), Paragraph(f"{raw_data.get('area_sqft', 0)} sq ft", body_style), Paragraph("Art. 220.11", body_style)],
        [Paragraph("Conteo de Tomacorrientes Generales", body_style), Paragraph(f"{raw_data.get('outlet_count', 0)} salidas", body_style), Paragraph("Art. 220.14", body_style)],
        [Paragraph("Carga de Unidades A/C", body_style), Paragraph(f"{raw_data.get('ac_total_va', 0)} VA", body_style), Paragraph("Art. 440.32", body_style)],
        [Paragraph("<b>Carga Total de Demanda Neta</b>", body_style), Paragraph(f"<b>{calcs['total_va']:.2f} VA</b>", body_style), Paragraph("Art. 220 Sub III", body_style)],
        [Paragraph("<b>Corriente de Línea del Alimentador</b>", body_style), Paragraph(f"<b>{calcs['feeder_amps']:.2f} A</b>", body_style), Paragraph("Sección de Alimentadores", body_style)]
    ]
    t = Table(table_data, colWidths=)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EDF2F7')), ('GRID',(0,0),(-1,-1),0.5,colors.grey), ('PADDING',(0,0),(-1,-1),5)]))
    story.append(t)
    
    story.append(PageBreak())
    
    # PÁGINA 2: CUADRO DE CARGAS (PANEL SCHEDULE)
    story.append(Paragraph("<b>CUADRO DE DISTRIBUCIÓN DE CIRCUITOS (PANEL SCHEDULE)</b>", h2_style))
    story.append(Spacer(1, 10))
    
    panel_data = [
        [Paragraph("<b>Circuito</b>", body_style), Paragraph("<b>Descripción del Circuito</b>", body_style), Paragraph("<b>Carga Constante</b>", body_style), Paragraph("<b>Protección</b>", body_style), Paragraph("<b>Conductor</b>", body_style)],
        [Paragraph("1", body_style), Paragraph("Circuitos de Alumbrado General", body_style), Paragraph("1500 VA", body_style), Paragraph("1x 20A", body_style), Paragraph("#12 AWG CU", body_style)],
        [Paragraph("2", body_style), Paragraph("Circuitos de Tomacorrientes", body_style), Paragraph(f"{int(raw_data.get('outlet_count', 0))*180} VA", body_style), Paragraph("1x 20A", body_style), Paragraph("#12 AWG CU", body_style)],
        [Paragraph("3", body_style), Paragraph("Sistema de Climatización A/C Dedicated", body_style), Paragraph(f"{raw_data.get('ac_total_va', 0)} VA", body_style), Paragraph(f"1x {calcs['main_breaker']}A", body_style), Paragraph(f"{calcs['feeder_wire']}", body_style)],
        [Paragraph("MAIN", body_style), Paragraph("<b>INTERRUPTOR PRINCIPAL DEL TABLERO</b>", body_style), Paragraph(f"{calcs['total_va']:.0f} VA", body_style), Paragraph(f"<b>{calcs['main_breaker']}A</b>", body_style), Paragraph(f"<b>{calcs['feeder_wire']}</b>", body_style)]
    ]
    t2 = Table(panel_data, colWidths=)
    t2.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EDF2F7')), ('GRID',(0,0),(-1,-1),0.5,colors.grey), ('PADDING',(0,0),(-1,-1),5)]))
    story.append(t2)
    
    doc.build(story)
    return pdf_path

# --- INTERFAZ WEB ---
if api_key:
    genai.configure(api_key=api_key)
    facility_type = st.sidebar.selectbox("Selecciona Tipo de Proyecto:", ["Dwelling (Residencial)", "Non-Dwelling (Comercial / Oficinas)"])
    uploaded_file = st.file_uploader("Sube el plano arquitectónico o eléctrico (PNG, JPG):", type=["png", "jpg", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Plano cargado correctamente", use_container_width=True)
        
        if st.button("🚀 Procesar Todo el Documento Símbolo por Símbolo"):
            with st.spinner("Ejecutando escaneo geométrico y reglas fijas NEC 2023..."):
                try:
                    # Instrucciones de bloqueo de comportamiento (JSON Estricto)
                    system_instruction = (
                        "Eres un parser visual de planos arquitectónicos eléctricos. Tu única tarea es extraer conteos físicos "
                        "y dimensiones del plano. Tienes estrictamente prohibido redactar explicaciones o calcular fórmulas. "
                        "Tu salida debe ser exclusivamente un objeto JSON válido, sin bloques markdown de tipo ```json."
                    )
                    
                    prompt = (
