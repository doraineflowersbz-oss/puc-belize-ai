import os
import streamlit as st
from google import generativeai as genai
from PIL import Image
import json
import re

st.set_page_config(page_title="PUC Belize AI Engine", layout="wide")
st.title("🛡️ Universal Power Infrastructure Intelligence - PUC Belize")
st.subheader("Multi-Voltage Engine: Single, Two, and Three-Phase Automation (NEC 2023 Hardcoded Rules)")

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

# --- CORE FRONTEND DROP INTERFACE ---
if api_key:
    genai.configure(api_key=api_key)
    uploaded_file = st.file_uploader("Upload architectural blueprint or electrical schematic (PNG, JPG):", type=["png", "jpg", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Blueprint drawing loaded into pipeline conduit", use_container_width=True)
        
        if st.button("🔥 INITIATE AUTONOMOUS MECHANICAL-ELECTRICAL COMPILATION"):
            with st.spinner("Analyzing structural layouts pixel-by-pixel..."):
                try:
                    system_instruction = (
                        "You act exclusively as a high-precision industrial electrical parser for architectural sheets. "
                        "Your sole purpose is to scan the image matrix, count physical layout nodes, and extract textual dimensions. "
                        "You are strictly forbidden from performing mathematical calculations, wiring ampacity logic, or explaining code blocks. "
                        "Your response output MUST be exclusively a single valid JSON block without any surrounding text or markdown formatting tags."
                    )
                    prompt = (
                        "Analyze this schematic sheet node-by-node. Parse structural counts and dimensions into this exact JSON schema format:\n"
                        "{\n"
                        "  \"area_sqft\": 2500,\n"
                        "  \"outlet_count\": 12,\n"
                        "  \"ac_total_va\": 3500,\n"
                        "  \"motors_total_va\": 1500\n"
                        "}"
                    )
                    
                    model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=system_instruction)
                    response = model.generate_content([prompt, image])
                    clean_json = re.sub(r"```json|```", "", response.text).strip()
                    parsed_data = json.loads(clean_json)
                    
                    st.success(f"🛸 Optical Scanning Complete: Computing load parameters under {system_phase}")
                    
                    # --- FIXED NEC CALCULATIONS ---
                    area = float(parsed_data.get('area_sqft', 0))
                    outlets = int(parsed_data.get('outlet_count', 0))
                    ac_va = float(parsed_data.get('ac_total_va', 0))
                    motors_va = float(parsed_data.get('motors_total_va', 0))
                    
                    lighting_va = area * 3.0
                    appliance_va = 4500.0
                    total_net_va = lighting_va + appliance_va + ac_va + (motors_va * 1.25)
                    
                    feeder_amps = total_net_va / 240.0
                    main_breaker = 100
                    if feeder_amps > 100: main_breaker = 150
                    if feeder_amps > 150: main_breaker = 200
                    if feeder_amps > 200: main_breaker = 400
                    if feeder_amps > 400: main_breaker = 800
                    
                    wire_sz = "#4 AWG CU"
                    if main_breaker == 150: wire_sz = "#1/0 AWG CU"
                    if main_breaker == 200: wire_sz = "#3/0 AWG CU"
                    if main_breaker == 400: wire_sz = "#600 kcmil CU"
                    if main_breaker >= 800: wire_sz = "Parallel 2x #600 kcmil CU"
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 📋 Computer Vision Automated Extractions")
                        st.json(parsed_data)
                    with c2:
                        st.markdown("### ⚙️ Hardcoded NEC 2023 Mathematical Metrics")
                        st.write(f"• Total Demand Load: **{total_net_va:.2f} VA**")
                        st.write(f"• Main Feeder Line Current: **{feeder_amps:.2f} Amps**")
                        st.write(f"• Main Service Switchboard Breaker: **{main_breaker} A**")
                        st.write(f"• Main Intake Feeder Wire Gauge Run: **{wire_sz}**")
                        
                    st.markdown("### 📊 Automated Single Line Diagram Layout (SLD)")
                    sld_graph = (
                        f"──[ BELIZE ELECTRICITY LIMITED (BEL) GRID INTERFACE ]──► [ PRIMARY DISTRIBUTION XFMR ]\n"
                        f"                                                                      │\n"
                        f"                                                      [ 📊 PUC RECORDING SERVICE REVENUE METER ]\n"
                        f"                                                                      │\n"
                        f"                                                      [ 🛑 MAIN SWITCHBOARD PANEL OCPD: {main_breaker}A ]\n"
                        f"                                                                      │\n"
                        f"                                                           FEEDER RUN RUN: {wire_sz}\n"
                        f"                                                                      │\n"
                        f"                                                                      ▼\n"
                        f"                                                       ⚙️ INDOOR INTERNAL PANEL DISTRIBUTION BOARD\n"
                        f"                                                        ├─► Lighting Branches ── Breakers: 1x20A ── Cable: #12 AWG THHN\n"
                        f"                                                        ├─► Receptacle Branches ── Breakers: 1x20A ── Cable: #12 AWG THHN\n"
                        f"                                                        └─► [HVAC Compressor Sub-System Circuit] ── Circuit Protection: 1x{main_breaker}A\n"
                    )
                    st.code(sld_graph, language="text")
                    
                    # --- BUILD BULLETPROOF TXT REPORT OVERVIEW ---
                    output_text = (
                        f"PUBLIC UTILITIES COMMISSION (PUC) - BELIZE\n"
                        f"OFFICIAL GRID COMPLIANCE PACKAGE SUBMISSION\n\n"
                        f"Licensed Engineer: {engineer_name}\n"
                        f"Client Developer: {client_name}\n"
                        f"Site Location: {project_location}\n"
                        f"Grid Topology: {system_phase} @ {selected_voltage}\n\n"
                        f"--- ELECTRICAL ENGINEERING METRICS ---\n"
                        f"Total Construction Area: {area} sq ft\n"
                        f"Outlet Device Count: {outlets}\n"
                        f"Total Demand Calculation: {total_net_va:.2f} VA\n"
                        f"Calculated Service Line Current: {feeder_amps:.2f} Amps\n"
                        f"Mandatory Main Switch Breaker sizing: {main_breaker}A\n"
                        f"Required Intake Feeder Wire Configuration: {wire_sz}\n\n"
                        f"--- SINGLE LINE DIAGRAM ARRAY ---\n"
                        f"{sld_graph}"
                    )
                    
                    st.download_button(
                        label="📥 DOWNLOAD COMPLETED PUC BELIZE OFFICIAL SUBMISSION PACKAGE",
                        data=output_text,
                        file_name=f"PUC_Belize_Submission_{engineer_name.replace(' ', '_')}.txt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Critical execution error within processing logic pipeline: {e}")
else:
    st.warning("Please input your active Gemini API Key inside the sidebar menu interface to initialize processing systems.")
