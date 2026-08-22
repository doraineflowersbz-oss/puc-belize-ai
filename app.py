import os
import streamlit as st
from google import generativeai as genai
from PIL import Image
import json
import re
import ezdxf

# ReportLab layout modules for clean document compilation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="PUC Belize AI Engine Pro", layout="wide")
st.title("🛡️ Universal Power Infrastructure Intelligence - PUC Belize")
st.subheader("Enterprise System: Direct AI Blueprint Vision & Native CAD (.DWG) Data Parsing Engine")

# --- SIDEBAR INTERFACE ---
st.sidebar.header("🔑 API Connection Configuration")
api_key = st.sidebar.text_input("Enter your Gemini API Key:", type="password")

st.sidebar.header("🔌 Voltage & Phase Grid Setup")
system_phase = st.sidebar.selectbox(
    "Select System Configuration:",
    ["Single-Phase (1-Phase / 2-Wire)", "Split-Phase (2-Phase / 3-Wire)", "Three-Phase (3-Phase / 4-Wire)"]
)

if system_phase == "Single-Phase (1-Phase / 2-Wire)":
    selected_voltage = st.sidebar.selectbox("Operating Line Voltage:", ["110V", "220V"])
elif system_phase == "Split-Phase (2-Phase / 3-Wire)":
    selected_voltage = st.sidebar.selectbox("Line-to-Line Supply Voltage:", ["110/220V", "120/240V"])
else:
    selected_voltage = st.sidebar.selectbox("Operating System Voltages (L-L / L-N):", ["115/230V", "220/440V", "120/208V", "277/480V"])

st.sidebar.header("📝 Official Submission Metadata")
engineer_name = st.sidebar.text_input("Authorizing Licensed Engineer:", "Ing. Doraine Flowers")
client_name = st.sidebar.text_input("Project Developer / Client Name:", "Belize Infrastructure Partners")
project_location = st.sidebar.text_input("Project Site Location:", "Belize City, Belize")

# --- MULTI-VOLTAGE MATHEMATICS BACKEND ---
def run_universal_voltage_engine(raw_data, phase_config, volt_config):
    calcs = {}
    area = float(raw_data.get('area_sqft', 0))
    outlets = int(raw_data.get('outlet_count', 0))
    ac_va = float(raw_data.get('ac_total_va', 0))
    motors_va = float(raw_data.get('motors_total_va', 0))
    
    st_breakers = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 600, 700, 800, 1000, 1200, 1600, 2000, 2500, 3000, 4000, 5000, 6000]
    
    lighting_va = area * 3.5 if "Three-Phase" in phase_config else area * 3.0
    appliance_va = 4500.0 if "Single" in phase_config or "Split" in phase_config else 0.0
    total_gen_load = lighting_va + appliance_va
    
    if total_gen_load <= 3000:
        demand_general = total_gen_load
    elif total_gen_load <= 120000:
        demand_general = 3000 + ((total_gen_load - 3000) * 0.35)
    else:
        demand_general = 3000 + (117000 * 0.35) + ((total_gen_load - 120000) * 0.25)
        
    total_net_va = demand_general + ac_va + (motors_va * 1.25)
    calcs['total_va'] = total_net_va
    
    calcs['lighting_circuits'] = max(1, int(re.sub(r'\.0$', '', str(round(lighting_va / 1800.0 + 0.49)))))
    calcs['receptacle_circuits'] = max(1, int(re.sub(r'\.0$', '', str(round((outlets * 180.0) / 2400.0 + 0.49)))))
    
    if "Single-Phase" in phase_config:
        v_line = float(re.sub(r'[^\d.]', '', volt_config))
        feeder_amps = total_net_va / v_line
        calcs['p_A'], calcs['p_B'], calcs['p_C'] = total_net_va, 0.0, 0.0
    elif "Split-Phase" in phase_config:
        v_ll = float(volt_config.split('/')[-1].replace('V',''))
        feeder_amps = total_net_va / v_ll
        calcs['p_A'], calcs['p_B'], calcs['p_C'] = total_net_va * 0.51, total_net_va * 0.49, 0.0
    else:
        v_numerical = float(volt_config.split('/')[0].replace('V',''))
        v_ll = v_numerical * 1.732 if v_numerical in [115, 120, 277] else v_numerical
        feeder_amps = total_net_va / (v_ll * 1.732)
        base_share = total_net_va / 3
        calcs['p_A'], calcs['p_B'], calcs['p_C'] = base_share * 1.01, base_share * 0.99, base_share * 1.00

    calcs['feeder_amps'] = feeder_amps
    calcs['main_breaker'] = next((x for x in st_breakers if x >= feeder_amps), 6000)
    
    if calcs['main_breaker'] <= 30: calcs['feeder_wire'] = "2x #10 AWG CU THHN"
    elif calcs['main_breaker'] <= 50: calcs['feeder_wire'] = "2x #8 AWG CU THHN"
    elif calcs['main_breaker'] <= 65: calcs['feeder_wire'] = "2x #6 AWG CU THHN"
    elif calcs['main_breaker'] <= 115: calcs['feeder_wire'] = "2x #2 AWG CU THHN"
    elif calcs['main_breaker'] <= 150: calcs['feeder_wire'] = "2x #1/0 AWG CU THHN"
    elif calcs['main_breaker'] <= 200: calcs['feeder_wire'] = "2x #3/0 AWG CU THHN"
    elif calcs['main_breaker'] <= 225: calcs['feeder_wire'] = "2x #4/0 AWG CU THHN"
    elif calcs['main_breaker'] <= 400: calcs['feeder_wire'] = "2x #600 kcmil CU THHN"
    elif calcs['main_breaker'] <= 600: calcs['feeder_wire'] = "Parallel: 2 Runs of (3x #350 kcmil CU)"
    elif calcs['main_breaker'] <= 800: calcs['feeder_wire'] = "Parallel: 2 Runs of (3x #600 kcmil CU)"
    elif calcs['main_breaker'] <= 1200: calcs['feeder_wire'] = "Parallel: 3 Runs of (3x #600 kcmil CU)"
    elif calcs['main_breaker'] <= 2000: calcs['feeder_wire'] = "Parallel: 5 Runs of (3x #600 kcmil CU)"
    else: calcs['feeder_wire'] = "Parallel Conductor Array Run Pack: 11 Runs of (3x #600 kcmil CU)"
        
    return calcs

# --- REPORTLAB PACKAGER ENGINE ---
def compile_universal_pdf(phase_config, volt_config, raw_data, calcs, eng, client, loc):
    pdf_path = "puc_belize_submission_package.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=15, leading=19, textColor=colors.HexColor('#002855'), alignment=1, spaceAfter=15)
    h2_style = ParagraphStyle('SecTitle', parent=styles['Heading2'], fontSize=11, leading=14, textColor=colors.HexColor('#0056B3'), spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['BodyText'], fontSize=9, leading=13)
    
    story = []
    story.append(Paragraph("<b>PUBLIC UTILITIES COMMISSION (PUC) - BELIZE</b>", title_style))
    story.append(Paragraph("<b>OFFICIAL GRID COMPLIANCE PACKAGE SUBMISSION</b>", title_style))
    story.append(Spacer(1, 15))
    
    meta_table = [
        [Paragraph("<b>Licensed Attending Engineer:</b>", body_style), Paragraph(eng, body_style)],
        [Paragraph("<b>Contracting Project Developer:</b>", body_style), Paragraph(client, body_style)],
        [Paragraph("<b>Project Deployment Site:</b>", body_style), Paragraph(loc, body_style)],
        [Paragraph("<b>Grid Configuration Topology:</b>", body_style), Paragraph(f"{phase_config} @ {volt_config}", body_style)],
        [Paragraph("<b>Regulatory Code Baseline:</b>", body_style), Paragraph("National Electrical Code (NEC 2023 Framework)", body_style)]
    ]
    t_meta = Table(meta_table, colWidths=[200, 300])
    t_meta.setStyle(TableStyle([('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F2F4F7')), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 6)]))
    story.append(t_meta)
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>DOCUMENT 01: SYSTEM FEEDER METRIC CALCULATIONS</b>", h2_style))
    
    load_table = [
        [Paragraph("<b>Grid Parameter Node</b>", body_style), Paragraph("<b>Calculated Metric</b>", body_style), Paragraph("<b>NEC 2023 Reference</b>", body_style)],
        [Paragraph("Total Physical Area Evaluated", body_style), Paragraph(f"{raw_data.get('area_sqft', 0)} sq ft", body_style), Paragraph("Art. 220.11", body_style)],
        [Paragraph("Duplex Receptacle Outlets Found", body_style), Paragraph(f"{raw_data.get('outlet_count', 0)} Nodes", body_style), Paragraph("Art. 220.14(I)", body_style)],
        [Paragraph("HVAC Cooling Machinery Base Load", body_style), Paragraph(f"{raw_data.get('ac_total_va', 0)} VA", body_style), Paragraph("Art. 440.32", body_style)],
        [Paragraph("<b>Total System Calculated Demand Load</b>", body_style), Paragraph(f"<b>{calcs['total_va']:.2f} VA</b>", body_style), Paragraph("Art. 220 Sub III", body_style)],
        [Paragraph("<b>Resulting Computed Phase Current</b>", body_style), Paragraph(f"<b>{calcs['feeder_amps']:.2f} A</b>", body_style), Paragraph("Phase Vector Formula", body_style)]
    ]
    t_load = Table(load_table, colWidths=[180, 160, 160])
    t_load.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EDF2F7')), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t_load)
    
    story.append(PageBreak())
    
    story.append(Paragraph("<b>DOCUMENT 02: BALANCED ELECTRICAL PANEL SCHEDULE SHEET</b>", h2_style))
    story.append(Spacer(1, 10))
    
    panel_table = [
        [Paragraph("<b>Ckt</b>", body_style), Paragraph("<b>Load Description</b>", body_style), Paragraph("<b>Phase A (VA)</b>", body_style), Paragraph("<b>Phase B (VA)</b>", body_style), Paragraph("<b>Phase C (VA)</b>", body_style), Paragraph("<b>OCPD Rating</b>", body_style)],
        [Paragraph("1", body_style), Paragraph("General Lighting Run Blocks", body_style), Paragraph(f"{calcs['p_A']*0.4:.0f}", body_style), Paragraph(f"{calcs['p_B']*0.2:.0f}", body_style), Paragraph(f"{calcs['p_C']*0.2:.0f}", body_style), Paragraph("1x 20A", body_style)],
        [Paragraph("2", body_style), Paragraph("Duplex Utility Receptacles", body_style), Paragraph("0", body_style), Paragraph(f"{calcs['p_B']*0.8:.0f}", body_style), Paragraph(f"{calcs['p_C']*0.3:.0f}", body_style), Paragraph("1x 20A", body_style)],
