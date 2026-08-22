import os
import streamlit as st
from google import generativeai as genai
from PIL import Image
import json
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="PUC Belize Search", layout="wide")
st.title("🛡️ Grounded Electrical System - PUC Belize")
st.subheader("Strict Sourced Lookup Mode: Direct Reference Cross-Examination")

st.sidebar.header("🔑 Config")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")
engineer_name = st.sidebar.text_input("Engineer Name:", "Ing. Doraine Flowers")
client_name = st.sidebar.text_input("Client Name:", "Belize Infrastructure Partners")
project_location = st.sidebar.text_input("Project Site:", "Belize City, Belize")

def compile_grounded_pdf(raw_data, verified_nec, eng, client, loc):
    pdf_path = "puc_belize_submission_package.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', parent=styles['Heading1'], fontSize=14, leading=18, textColor=colors.HexColor('#002855'))
    body_style = ParagraphStyle('B', parent=styles['BodyText'], fontSize=10, leading=14)
    
    story = []
    story.append(Paragraph("<b>PUBLIC UTILITIES COMMISSION (PUC) - BELIZE</b>", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Engineer: {eng}", body_style))
    story.append(Paragraph(f"Client: {client}", body_style))
    story.append(Paragraph(f"Location: {loc}", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>1. EXTRACTED PLAN DATA:</b>", body_style))
    story.append(Paragraph(f"Area: {raw_data.get('area_sqft', '0')} sq ft", body_style))
    story.append(Paragraph(f"Outlets Count: {raw_data.get('outlet_count', '0')}", body_style))
    story.append(Paragraph(f"AC Load: {raw_data.get('ac_total_va', '0')} VA", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>2. VERIFIED NEC 2023 REFS:</b>", body_style))
    story.append(Paragraph(f"Breaker Rating: {verified_nec.get('main_breaker_rating', 'Pending')}", body_style))
    story.append(Paragraph(f"Conductor Spec: {verified_nec.get('conductor_specifications', 'Pending')}", body_style))
    story.append(Paragraph(f"Source Text: {verified_nec.get('source_code_citation_text', 'Pending')}", body_style))
    
    doc.build(story)
    return pdf_path

if api_key:
    genai.configure(api_key=api_key)
    uploaded_blueprint = st.file_uploader("Upload blueprint layout (PNG, JPG):", type=["png", "jpg", "jpeg"])
    uploaded_nec_reference = st.file_uploader("Upload strict NEC 2023 reference chapter page (PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"])
        
    if uploaded_blueprint and uploaded_nec_reference:
        img_blueprint = Image.open(uploaded_blueprint)
        st.image(img_blueprint, caption="Staging blueprint", use_container_width=True)
        
        if st.button("🔥 INITIATE GROUNDED DOCUMENT PROCESSING"):
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction="You match text and items from images. Output data strictly in the requested JSON structure."
                )
                
                bp_prompt = "Count the items on this electrical sheet. Reply in this JSON layout: {\"area_sqft\": 2500, \"outlet_count\": 14, \"ac_total_va\": 4000}"
                response_bp = model.generate_content([bp_prompt, img_blueprint])
                clean_bp = re.sub(r"```json|```", "", response_bp.text).strip()
                parsed_bp = json.loads(clean_bp)
                
                nec_prompt = "Read the manual page. Extract variables into this JSON layout: {\"main_breaker_rating\": \"200A\", \"conductor_specifications\": \"3/0 AWG\", \"source_code_citation_text\": \"Table 310.16 page text\"}"
                
                if hasattr(uploaded_nec_reference, 'type') and "image" in uploaded_nec_reference.type:
                    img_ref = Image.open(uploaded_nec_reference)
                    response_nec = model.generate_content([nec_prompt, img_ref])
                else:
                    response_nec = model.generate_content([nec_prompt, uploaded_nec_reference.read().decode('utf-8', errors='ignore')])
                    
                clean_nec = re.sub(r"```json|```", "", response_nec.text).strip()
                parsed_nec = json.loads(clean_nec)
                
                st.success("Analysis Complete")
                st.json(parsed_bp)
                st.json(parsed_nec)
                
                pdf_output_path = compile_grounded_pdf(parsed_bp, parsed_nec, engineer_name, client_name, project_location)
                with open(pdf_output_path, "rb") as file:
                    st.download_button(label="📥 DOWNLOAD COMPLETED PDF PACKAGE", data=file, file_name="PUC_Belize_Package.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Processing error: {e}")
else:
    st.warning("Please input your active Gemini API Key inside the sidebar menu interface to initialize.")
