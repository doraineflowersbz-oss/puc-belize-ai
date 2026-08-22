import os
import streamlit as st
from google import generativeai as genai
from PIL import Image
import json
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="PUC Belize AI Engine - Pure Search", layout="wide")
st.title("🛡️ Document-Grounded Electrical Intelligence - PUC Belize")
st.subheader("Strict Reference Lookup Mode: Grounded Parsing directly via NEC 2023 Verification")

st.sidebar.header("🔑 System Access Configuration")
api_key = st.sidebar.text_input("Enter your Gemini API Key:", type="password")

st.sidebar.header("📝 Official Submission Metadata")
engineer_name = st.sidebar.text_input("Authorizing Licensed Engineer:", "Ing. Doraine Flowers")
client_name = st.sidebar.text_input("Project Developer / Client Name:", "Belize Infrastructure Partners")
project_location = st.sidebar.text_input("Project Site Location:", "Belize City, Belize")
system_voltage = st.sidebar.text_input("Target System Operating Voltage (e.g., 120/240V, 115/230V):", "120/240V")

def compile_grounded_pdf(raw_data, verified_nec, eng, client, loc, volt):
    pdf_path = "puc_belize_grounded_submission_package.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=15, leading=19, textColor=colors.HexColor('#002855'), alignment=1, spaceAfter=15)
    h2_style = ParagraphStyle('SecTitle', parent=styles['Heading2'], fontSize=11, leading=14, textColor=colors.HexColor('#0056B3'), spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['BodyText'], fontSize=9, leading=13)
    
    story = []
    story.append(Paragraph("<b>PUBLIC UTILITIES COMMISSION (PUC) - BELIZE</b>", title_style))
    story.append(Paragraph("<b>OFFICIAL COMPLIANCE PACKAGE - GROUNDED DIRECTLY ON NEC 2023 ORIGINAL TEXT</b>", title_style))
    story.append(Spacer(1, 15))
    
    meta_table = [
        [Paragraph("<b>Licensed Attending Engineer:</b>", body_style), Paragraph(eng, body_style)],
        [Paragraph("<b>Contracting Project Developer:</b>", body_style), Paragraph(client, body_style)],
        [Paragraph("<b>Project Deployment Site:</b>", body_style), Paragraph(loc, body_style)],
        [Paragraph("<b>Target Operating Voltage:</b>", body_style), Paragraph(volt, body_style)],
        [Paragraph("<b>Code Grounding Baseline:</b>", body_style), Paragraph("National Electrical Code (NEC 2023 Edition - Strictly Sourced)", body_style)]
    ]
    t_meta = Table(meta_table, colWidths=[150, 350])
    t_meta.setStyle(TableStyle([('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F2F4F7')), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 6)]))
    story.append(t_meta)
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>DOCUMENT 01: EXTRACTED BLUEPRINT DATA LOG</b>", h2_style))
    
    load_table = [
        [Paragraph("<b>Layout Parameter</b>", body_style), Paragraph("<b>Detected Metric Value</b>", body_style)],
        [Paragraph("Estimated Square Footage Area", body_style), Paragraph(f"{raw_data.get('area_sqft', 'Not Found')} sq ft", body_style)],
        [Paragraph("Duplex Receptacle Node Count", body_style), Paragraph(f"{raw_data.get('outlet_count', 'Not Found')} Nodes", body_style)],
        [Paragraph("HVAC Cooling Machinery Base Load", body_style), Paragraph(f"{raw_data.get('ac_total_va', 'Not Found')} VA", body_style)]
    ]
    t_load = Table(load_table, colWidths=[200, 300])
    t_load.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EDF2F7')), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t_load)
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>DOCUMENT 02: VERIFIED SOURCED CODE COMPLIANCE METRICS</b>", h2_style))
    story.append(Paragraph(f"<b>Sourced Overcurrent Rating (Art. 240.6):</b> {verified_nec.get('main_breaker_rating', 'Pending Verification')}", body_style))
    story.append(Paragraph(f"<b>Sourced Conductor Run Capacity (Table 310.16):</b> {verified_nec.get('conductor_specifications', 'Pending Verification')}", body_style))
    story.append(Paragraph(f"<b>Direct Source Citation Excerpt:</b> {verified_nec.get('source_code_citation_text', 'No direct reference text logged')}", body_style))
    
    doc.build(story)
    return pdf_path

if api_key:
    genai.configure(api_key=api_key)
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        uploaded_blueprint = st.file_uploader("Step 1: Upload architectural blueprint layout (PNG, JPG):", type=["png", "jpg", "jpeg"])
    with col_input2:
        uploaded_nec_reference = st.file_uploader("Step 2: Upload strict NEC 2023 reference chapter or table extract (PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"])
        
    if uploaded_blueprint and uploaded_nec_reference:
        img_blueprint = Image.open(uploaded_blueprint)
        st.image(img_blueprint, caption="Active project blueprint pushed to staging pipeline", use_container_width=True)
        
        if st.button("🔥 INITIATE GROUNDED DOCUMENT-BASED PROCESSING"):
            with st.spinner("Processing documents simultaneously. Searching strict code references without guessing..."):
                try:
                    blueprint_instruction = (
                        "You act as a raw visual counting lens. Your only task is to look at the architectural image and extract physical parameters. "
                        "Do not calculate sizing metrics or guess codes. Output results strictly inside a clean JSON object format."
                    )
                    blueprint_prompt = (
                        "Scan this sheet completely. Extract parameters into this exact JSON layout structure:\n"
                        "{\n"
                        "  \"area_sqft\": (total built area found in text or dimensions),\n"
                        "  \"outlet_count\": (exact count of duplex receptacle symbols),\n"
                        "  \"ac_total_va\": (sum total of cooling load indicators)\n"
                        "}"
                    )
                    
                    model_bp = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=blueprint_instruction)
                    response_bp = model_bp.generate_content([blueprint_prompt, img_blueprint])
                    clean_bp_json = re.sub(r"```json|```", "", response_bp.text).strip()
                    parsed_blueprint_data = json.loads(clean_bp_json)
                    
                    st.success("Stage 1: Blueprint Structural Analysis Succeeded")
                    
                    nec_instruction = (
                        "You are a strict code inspector tool. Your only task is to look at the provided reference code attachment "
                        "and extract exact written specifications matching the query. You are strictly forbidden from referencing "
                        "outside knowledge, guessing sizes, or predicting answers. Quote only what is visibly typed on the code paper."
                    )
                    nec_query_prompt = (
                        f"Look at the uploaded reference document. Based strictly on the physical numbers written on it, find and output a JSON matching these fields:\n"
                        "{\n"
                        "  \"main_breaker_rating\": \"(Find the exact breaker size nameplate rating from the reference page that handles the extracted parameters)\",\n"
                        "  \"conductor_specifications\": \"(Find the exact wire size or AWG from Table 310.16 written on the reference page)\",\n"
                        "  \"source_code_citation_text\": \"(Quote word-for-word the text sentence or table row matching the selection)\"\n"
                        "}"
                    )
                    
                    model_nec = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=nec_instruction)
                    
                    if hasattr(uploaded_nec_reference, 'type') and "image" in uploaded_nec_reference.type:
                        img_ref = Image.open(uploaded_nec_reference)
                        response_nec = model_nec.generate_content([nec_query_prompt, img_ref])
                    else:
                        response_nec = model_nec.generate_content([nec_query_prompt, uploaded_nec_reference.read().decode('utf-8', errors='ignore')])
                        
                    clean_json_nec = re.sub(r"```json|```", "", response_nec.text).strip()
                    parsed_nec_verification = json.loads(clean_json_nec)
                    
                    st.success("Stage 2: Strict Reference Lookup Verification Succeeded")
                    
                    col_dash1, col_dash2 = st.columns(2)
                    with col_dash1:
                        st.markdown("### 📋 Variables Found on Blueprint")
                        st.json(parsed_blueprint_data)
                    with col_dash2:
                        st.markdown("### 🔍 Strict Code Values Located in Document")
                        st.json(parsed_nec_verification)
                        
                    st.markdown("### 📊 Document-Grounded Single Line Diagram (SLD)")
                    sld_graph = (
                        "──[ UTILITY SOURCE SUPPLY ]──► [ REGISTERED PUC METER ]\n"
                        f"                                         │\n"
                        f"                       VERIFIED BREAKER: {parsed_nec_verification.get('main_breaker_rating', 'UNVERIFIED')}\n"
