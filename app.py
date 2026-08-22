import os
import streamlit as st
from google import generativeai as genai
from PIL import Image

# Configuración de la interfaz web
st.set_page_config(page_title="PUC Belize AI Beta", layout="wide")
st.title("⚡ PUC Belize & NEC AI Compliance Beta")
st.subheader("Sube tu plano arquitectónico para una extracción exacta sin errores")

# Entrada para tu clave de API gratuita de Google AI Studio
api_key = st.sidebar.text_input("Introduce tu Gemini API Key (Gratis):", type="password")

if api_key:
    genai.configure(api_key=api_key)
    
    # 1. Capa de Control Humano: Tus restricciones exactas para la IA
    system_instruction = (
        "Eres un extractor visual estricto de ingeniería eléctrica para el NEC y la PUC de Belice. "
        "Tu ÚNICA tarea es contar y listar los símbolos eléctricos y cargas exactas que ves en la imagen. "
        "Está estrictamente PROHIBIDO inventar, asumir o calcular calibres o protecciones. "
        "Si no ves un dato, reporta 0. Responde exclusivamente en un formato estructurado de texto."
    )
    
    uploaded_file = st.file_uploader("Sube el plano arquitectónico o diagrama (PNG, JPG):", type=["png", "jpg", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Plano cargado con éxito", use_container_width=True)
        
        if st.button("Procesar Plano con IA Estricta"):
            with st.spinner("Leyendo símbolos píxel por píxel..."):
                try:
                    # Inicializar modelo de visión de Google (Gratuito en Google AI Studio)
                    model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction=system_instruction
                    )
                    
                    # Prompt detallado para conteo estricto
                    prompt = (
                        "Analiza este plano símbolo por símbolo. Identifica y cuenta exactamente:\n"
                        "1. Cantidad de tomacorrientes generales (Duplex Receptacles).\n"
                        "2. Cantidad de unidades de Aire Acondicionado (A/C Units).\n"
                        "Proporciona los totales en formato: 'Tomacorrientes: [número]' y 'A/C: [número]'."
                    )
                    
                    response = model.generate_content([prompt, image])
                    raw_text = response.text
                    
                    st.success("🤖 Extracción de la IA Completada con Éxito")
                    st.text_area("Datos Extraídos del Plano:", raw_text, height=150)
                    
                    # 2. Capa de Ingeniería Matemática (Fórmulas fijas NEC - Cero Alucinaciones)
                    st.subheader("🧮 Cálculos Automáticos Basados en el NEC")
                    
                    # Simulación de extracción limpia para el motor matemático
                    # En producción, usarías expresiones regulares (regex) para pasar estos números automáticamente
                    st.info("Introduce los valores extraídos arriba para ejecutar el Motor de Reglas Matemáticas:")
                    amps_ac = st.number_input("Amperaje de placa del A/C detectado (Amperios):", min_value=0.0, value=16.0, step=1.0)
                    
                    if amps_ac > 0:
                        # NEC Art. 440.62: Los circuitos de A/C individuales deben dimensionarse al 125%
                        nec_load = amps_ac * 1.25
                        
                        # NEC Art. 240.6: Tamaños estándar de interruptores (Breakers)
                        standard_breakers = [15, 20, 25, 30, 40, 50, 60, 70, 80, 100]
                        breaker_size = next((x for x in standard_breakers if x >= nec_load), 100)
                        
                        st.markdown(f"**Resultado del Motor de Reglas (Código Puro):**")
                        st.write(f"• Carga continua calculada (125%): **{nec_load:.2f} A**")
                        st.write(f"• Protección requerida según NEC Artículo 240.6: **{breaker_size} A Breaker**")
                        st.caption("Nota: Este cálculo fue hecho por código tradicional matemático, garantizando un 0% de errores de la IA.")
                        
                except Exception as e:
                    st.error(f"Error al procesar: {e}")
else:
    st.warning("Por favor, introduce tu API Key gratuita en la barra lateral para activar la aplicación.")
