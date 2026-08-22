import os
import streamlit as st
from google import generativeai as genai
from PIL import Image
import json
import re

st.set_page_config(page_title="PUC Belize AI Engine", layout="wide")
st.title("🛡️ Universal Power Infrastructure Intelligence - PUC Belize")
st.subheader("Unrestricted Multi-Format Upload: PDF, DWG, PNG, JPG Parsing Engine")

# --- SIDEBAR INTERFACE ---
st.sidebar.header("🔑 API Connection Configuration")
api_key = st.sidebar.text_input("Enter your Gemini API Key:", type="password")

st.sidebar.header("🔌 Voltage & Phase Grid Setup")
system_phase = st.sidebar.selectbox(
    "Select System Configuration:",
    ["Single-Phase (1-Phase / 2-Wire)", "Split-Phase (2-Phase / 3-Wire)", "Three-Phase (3-Phase / 4-Wire)"]
)

selected_voltage = st.sidebar.text_input("Operating System Voltage (e.g. 120/240V, 115/230V, 277/480V):", "120/240V")

st.sidebar.header("📝 Official Submission Metadata")
engineer_name = st.sidebar.text_input("Authorizing Licensed Engineer:", "Ing. Doraine Flowers")
client_name = st.sidebar.text_input("Project Developer / Client Name:", "Belize Infrastructure Partners")
project_location = st.sidebar.text_input("Project Site Location:", "Belize City, Belize")

if api_key:
    genai.configure(api_key=api_key)
    
    uploaded_file = st.file_uploader("Upload blueprint layout or CAD drawing file (PDF, DWG, PNG, JPG):", type=["pdf", "dwg", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        st.info("⚡ Engineering document loaded into the analysis pipeline container.")
        
        if st.button("🔥 INITIATE AUTONOMOUS ELECTRICAL COMPILATION"):
            with st.spinner("Executing structural data layout analysis..."):
                try:
                    system_instruction = (
                        "You act exclusively as a high-precision industrial electrical parser for structural text and sheets. "
                        "Your sole purpose is to scan the uploaded document data, count physical layout nodes, and extract textual dimensions. "
                        "You are strictly forbidden from performing mathematical calculations, wiring ampacity logic, or explaining code blocks. "
                        "Your response output MUST be exclusively a single valid JSON block without any surrounding text or markdown formatting tags."
                    )
                    prompt = (
                        "Analyze this document thoroughly. Parse structural configurations and dimensions into this exact JSON schema format:\n"
                        "{\n"
                        "  \"area_sqft\": 2500,\n"
                        "  \"outlet_count\": 12,\n"
                        "  \"ac_total_va\": 3500,\n"
                        "  \"motors_total_va\": 1500\n"
                        "}"
                    )
                    
                    model = genai.GenerativeModel(model_name="gemini-3.5-flash", system_instruction=system_instruction)
                    
                    if "pdf" in uploaded_file.type:
                        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": uploaded_file.read()}])
                    elif "dwg" in uploaded_file.name.lower():
                        response = model.generate_content([prompt, {"mime_type": "application/octet-stream", "data": uploaded_file.read()}])
                    else:
                        image = Image.open(uploaded_file)
                        response = model.generate_content([prompt, image])
                    
                    clean_json = re.sub(r"```json|```", "", response.text).strip()
                    parsed_data = json.loads(clean_json)
                    
                    st.success("🛸 Layout Scanning Complete")
                    
                    # --- MATH BACKEND ---
                    area = float(parsed_data.get('area_sqft', 2500))
                    outlets = int(parsed_data.get('outlet_count', 12))
                    ac_va = float(parsed_data.get('ac_total_va', 3500))
                    motors_va = float(parsed_data.get('motors_total_va', 1500))
                    
                    lighting_va = area * 3.0
                    total_net_va = lighting_va + 4500.0 + ac_va + (motors_va * 1.25)
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
                        st.markdown("### 📋 Automated Data Extractions")
                        st.json(parsed_data)
                    with c2:
                        st.markdown("### ⚙️ Deterministic NEC Engineering Metrics")
                        st.write(f"• Total Demand Load: **{total_net_va:.2f} VA**")
                        st.write(f"• Service Line Current: **{feeder_amps:.2f} Amps**")
                        st.write(f"• Main Overcurrent Protector (Breaker): **{main_breaker} A**")
                        st.write(f"• Main Intake Wire Specification: **{wire_sz}**")
                    
                    st.markdown("### 📊 Automated Single Line Diagram Layout (SLD)")
                    sld_graph = (
                        "──[ BELIZE ELECTRICITY LIMITED (BEL) UTILITY INPUT ]──► [ MAIN TRANSFORMER BANK ]\n"
                        "                                                                     │\n"
                        "                                                     [ PUC RECORDING REVENUE METER ]\n"
                        "                                                                     │\n"
                        f"                                                     [ SWITCHBOARD SERVICE PANEL MAIN OCPD: {main_breaker}A ]\n"
                        "                                                                     │\n"
                        f"                                                          FEEDER LINE: {wire_sz}\n"
                        "                                                                     │\n"
                        "                                                                     ▼\n"
                        "                                                     INTERNAL MAIN DISTRIBUTION PANELBOARD\n"
                        "                                                      ├─► Branched Path 1: General Lighting ── Breaker: 1x20A ── Wire: #12 AWG\n"
                        "                                                      ├─► Branched Path 2: Receptacle Loads ── Breaker: 1x20A ── Wire: #12 AWG\n"
                        f"                                                      └─► Branched Path 3: HVAC Compressor Dedicated Node ── Breaker: 1x{main_breaker}A\n"
                    )
                    st.code(sld_graph, language="text")
                    
                    # --- SAFE COMPILATION OF PACKAGED TEXT REPORT PACK ---
                    report_title = "PUBLIC UTILITIES COMMISSION (PUC) - BELIZE\nOFFICIAL ELECTRICAL SUBMISSION INSPECTION PACKAGE\n\n"
                    report_meta = f"Engineer: {engineer_name}\nClient: {client_name}\nLocation: {project_location}\nTopology: {system_phase} @ {selected_voltage}\n\n"
                    report_metrics = f"--- ENGINEERING CALCULATIONS ---\nArea: {area} sq ft\nOutlets: {outlets} Nodes\nHVAC Load: {ac_va} VA\nMotor Load: {motors_va} VA\nTotal Net Demand: {total_net_va:.2f} VA\nLine Current: {feeder_amps:.2f} A\nMain Breaker: {main_breaker}A\nMain Wire Size: {wire_sz}\n\n"
                    report_diagram = f"--- SINGLE LINE DIAGRAM SCHEMA ---\n{sld_graph}"
                    
                    final_package_data = report_title + report_meta + report_metrics + report_diagram
                    
                    st.download_button(
                        label="📥 DOWNLOAD COMPLETED PUC BELIZE OFFICIAL SUBMISSION PACKAGE (.TXT)",
                        data=final_package_data,
                        file_name=f"PUC_Belize_Submission_{engineer_name.replace(' ', '_')}.txt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Execution handling failure: {e}")
else:
    st.sidebar.warning("Please input your active Gemini API Key inside the sidebar menu interface to initialize processing systems.")

