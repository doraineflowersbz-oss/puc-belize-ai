import os
import streamlit as st
from google import generativeai as genai
from PIL import Image
import json
import re

st.set_page_config(page_title="PUC Belize AI Engine Pro", layout="wide")
st.title("🛡️ Industrial Electrical Engineering Platform - PUC Belize")
st.subheader("Autonomous Multi-Voltage, Parallel Feeder Conduit Fill & Voltage Drop Calculations")

# --- SIDEBAR INTERFACE ---
st.sidebar.header("🔑 API Connection Configuration")
api_key = st.sidebar.text_input("Enter your Gemini API Key:", type="password")

st.sidebar.header("🔌 Voltage & Phase Grid Setup")
system_phase = st.sidebar.selectbox(
    "Select System Configuration:",
    ["Single-Phase (1-Phase / 2-Wire)", "Split-Phase (2-Phase / 3-Wire)", "Three-Phase (3-Phase / 4-Wire)"]
)

if system_phase == "Single-Phase (1-Phase / 2-Wire)":
    selected_voltage = st.sidebar.selectbox("Operating Line Voltage:", ["110V", "120V", "220V", "240V"])
elif system_phase == "Split-Phase (2-Phase / 3-Wire)":
    selected_voltage = st.sidebar.selectbox("Line-to-Line Supply Voltage:", ["110/220V", "120/240V"])
else:
    selected_voltage = st.sidebar.selectbox("Operating System Voltages (L-L / L-N):", ["115/230V", "220/440V", "120/208V", "277/480V"])

st.sidebar.header("📐 Physical Field Variables")
run_distance = st.sidebar.number_input("One-Way Feeder Distance Runway (Feet):", min_value=1.0, value=150.0, step=5.0)
conduit_type = st.sidebar.selectbox("Rigid Raceway Enclosure Material:", ["Schedule 40 PVC Conduit", "Schedule 80 PVC Conduit", "Rigid PVC Conduit (RMC)"])

st.sidebar.header("📝 Official Submission Metadata")
engineer_name = st.sidebar.text_input("Authorizing Licensed Engineer:", "Ing. Doraine Flowers")
client_name = st.sidebar.text_input("Project Developer / Client Name:", "Belize Infrastructure Partners")
project_location = st.sidebar.text_input("Project Site Location:", "Belize City, Belize")

# --- INDUSTRIAL METRIC CALCULATION ENGINE ---
def run_god_mode_industrial_engine(raw_data, phase_config, volt_config, distance, raceway):
    calcs = {}
    area = float(raw_data.get('area_sqft', 2500))
    outlets = int(raw_data.get('outlet_count', 12))
    ac_va = float(raw_data.get('ac_total_va', 3500))
    motors_va = float(raw_data.get('motors_total_va', 1500))
    
    st_breakers = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 600, 700, 800, 1000, 1200, 1600, 2000, 2500, 3000, 4000, 5000, 6000]
    
    lighting_va = area * 3.5 if "Three-Phase" in phase_config else area * 3.0
    appliance_va = 4500.0 if "Single" in phase_config or "Split" in phase_config else 0.0
    total_net_va = lighting_va + appliance_va + ac_va + (motors_va * 1.25)
    calcs['total_va'] = total_net_va
    
    if "Single-Phase" in phase_config:
        v_line = float(re.sub(r'[^\d.]', '', volt_config))
        feeder_amps = total_net_va / v_line
        factor_vd = 2.0
    elif "Split-Phase" in phase_config:
        v_line = float(volt_config.split('/')[-1].replace('V',''))
        feeder_amps = total_net_va / v_line
        factor_vd = 2.0
    else:
        v_numerical = float(volt_config.split('/')[0].replace('V',''))
        v_line = v_numerical * 1.732 if v_numerical in [115, 120, 277] else v_numerical
        feeder_amps = total_net_va / (v_line * 1.732)
        factor_vd = 1.732

    breaker_load_profile = feeder_amps * 1.00
    main_breaker = next((x for x in st_breakers if x >= breaker_load_profile), 6000)
    calcs['main_breaker'] = main_breaker
    calcs['feeder_amps'] = feeder_amps

    wire_properties_matrix = [
        ["#14 AWG CU", 15, 3.07, 0.0097],
        ["#12 AWG CU", 20, 1.93, 0.0133],
        ["#10 AWG CU", 30, 1.24, 0.0211],
        ["#8 AWG CU", 50, 0.778, 0.0366],
        ["#6 AWG CU", 65, 0.491, 0.0507],
        ["#4 AWG CU", 85, 0.308, 0.0824],
        ["#2 AWG CU", 115, 0.194, 0.1158],
        ["#1/0 AWG CU", 150, 0.122, 0.1855],
        ["#2/0 AWG CU", 175, 0.0967, 0.2223],
        ["#3/0 AWG CU", 200, 0.0766, 0.2679],
        ["#4/0 AWG CU", 225, 0.0608, 0.3237],
        ["#250 kcmil CU", 255, 0.0515, 0.3970],
        ["#350 kcmil CU", 310, 0.0367, 0.5242],
        ["#500 kcmil CU", 380, 0.0258, 0.7073],
        ["#600 kcmil CU", 420, 0.0214, 0.8676]
    ]

    selected_wire_profile = next((w for w in wire_properties_matrix if w[1] >= main_breaker), wire_properties_matrix[-1])
    wire_label = selected_wire_profile[0]
    r_val = selected_wire_profile[2]
    area_wire = selected_wire_profile[3]
    
    num_runs = 1
    if main_breaker > 400:
        num_runs = (main_breaker // 380) + 1
        selected_wire_profile = wire_properties_matrix[-2]
        wire_label = f"Parallel Run Array: {num_runs} Runs of (3x {selected_wire_profile[0]})"
        r_val = selected_wire_profile[2] / num_runs
        area_wire = selected_wire_profile[3]
    
    calcs['feeder_wire'] = wire_label

    voltage_drop_total = (factor_vd * distance * r_val * feeder_amps) / 1000.0
    vd_percentage = (voltage_drop_total / v_line) * 100.0
    
    calcs['vd_volts'] = voltage_drop_total
    calcs['vd_percent'] = vd_percentage
    calcs['vd_status'] = "PASSED (Within 3% Limit)" if vd_percentage <= 3.0 else "WARNING: EXCEEDS LIMITS"

    total_conductors_run = 4 if "Three-Phase" in phase_config else 3
    combined_wires_area = area_wire * total_conductors_run * num_runs
    
    conduit_allowable_limits = [
        ["1/2\" Conduit Pipe", 0.122],
        ["3/4\" Conduit Pipe", 0.213],
        ["1\" Conduit Pipe", 0.346],
        ["1-1/4\" Conduit Pipe", 0.598],
        ["1-1/2\" Conduit Pipe", 0.814],
        ["2\" Conduit Pipe", 1.343],
        ["2-1/2\" Conduit Pipe", 1.921],
        ["3\" Conduit Pipe", 2.950],
        ["3-1/2\" Conduit Pipe", 3.961],
        ["4\" Conduit Pipe", 5.090]
    ]
    
    optimized_conduit_selection = next((c for c in conduit_allowable_limits if c[1] >= combined_wires_area), conduit_allowable_limits[-1])
    calcs['conduit_diameter'] = optimized_conduit_selection[0]
    calcs['total_wire_area_sqin'] = combined_wires_area
    calcs['allowable_conduit_area_sqin'] = optimized_conduit_selection[1]
    calcs['conduit_fill_percentage'] = (combined_wires_area / optimized_conduit_selection[1]) * 40.0

    calcs['lighting_circuits'] = max(1, int(round(lighting_va / 1800.0 + 0.49)))
    calcs['receptacle_circuits'] = max(1, int(round((outlets * 180.0) / 2400.0 + 0.49)))

    return calcs

if api_key:
    genai.configure(api_key=api_key)
    uploaded_file = st.file_uploader("Upload blueprint layout or document (PDF, DWG, PNG, JPG):", type=["pdf", "dwg", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        st.info("⚡ Engineering document loaded into the analysis pipeline container.")
        
        if st.button("🔥 INITIATE AUTONOMOUS ELECTRICAL COMPILATION"):
            with st.spinner("Executing structural data layout analysis..."):
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
                
                st.success("🛸 Data Node Matrix Extraction Succeeded")
                
                metrics = run_god_mode_industrial_engine(parsed_data, system_phase, selected_voltage, run_distance, conduit_type)
                
                st.markdown("### 📋 Automated Data Extractions")
                st.json(parsed_data)
                
                st.markdown("### ⚙️ Hardcoded Sizing Specifications (100% Breaker Rating Multiplier)")
                st.write(f"• Demand Current Draw on Service: **{metrics['feeder_amps']:.2f} Amps**")
                st.write(f"• Overcurrent Breaker Trip Rating (100% Load Match): **{metrics['main_breaker']} A**")
                st.write(f"• Service Intake Wire Configuration Run: **{metrics['feeder_wire']}**")
                
                st.markdown("### 📉 Feeder Voltage Drop Sub-Sheet")
                st.write(f"• Calculated Feeder Voltage Loss: **{metrics['vd_volts']:.2f} Volts**")
                st.write(f"• True Vector Ratio Percentage Loss: **{metrics['vd_percent']:.2f}%**")
                st.write(f"• Evaluation Compliance Status Profile: **{metrics['vd_status']}**")
                
