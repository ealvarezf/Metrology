import streamlit as st
import pandas as pd
import os
from pyzbar.pyzbar import decode
from PIL import Image
from db import get_qry
from gage import ExecuteQry, Gage 

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Control de Gages - Nexteer",
    page_icon="",
    layout="wide",
)

# --- HEADER CON IMAGEN Y TÍTULO ---
# Puedes usar una imagen local (en la misma carpeta) o una URL
BASE_DIR = os.path.dirname(__file__)
img_path = os.path.join(BASE_DIR, "", "image", "header_nexteer.png")

# Cargar imagen si existe
try:
    st.image(img_path, use_container_width=True)
    
except Exception:
    st.warning("No se pudo cargar la imagen del encabezado.")

# --- TÍTULO PRINCIPAL ---
st.markdown(
    """
    <div style='text-align: center; padding: 10px 0;'>
        <h1 style='color: #003366; margin-bottom: 0;'>CONTROL DE EQUIPOS - METROLOGÍA</h1>
        <h3 style='color: #666;'>Planta 66 - Nexteer Automotive</h3>
        <hr style='border: 2px solid #003366; width: 60%; margin: auto;'>
    </div>
    """,
    unsafe_allow_html=True
)

# --- CSS para centrar y hacer cuadrado el recuadro de cámara ---
st.markdown("""
    <style>
        /* Contenedor principal del input de cámara */
        div[data-testid="stCameraInput"] {
            width: 100% !important;        /* Ocupa un tercio del ancho */
            margin: auto;                 /* Centrado horizontal */
        }

        /* Video y canvas cuadrado */
        div[data-testid="stCameraInput"] video,
        div[data-testid="stCameraInput"] canvas {
            aspect-ratio: 1 / 1 !important;  /* Mantiene proporción cuadrada */
            object-fit: cover !important;    /* Rellena el cuadro */
            border-radius: 15px !important;  /* Bordes redondeados */
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            width: 80% !important;
            height: auto !important;
        }

        /* Centrar el botón de captura */
        button[kind="secondary"] {
            margin: 10px auto !important;
            display: flex !important;
            justify-content: center !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- CSS para centrar el texto del label del camera_input ---
st.markdown("""
    <style>
    /* Centrar el texto del label del camera_input */
    div[data-testid="stCameraInput"] > label {
        display: block;
        text-align: center;
        font-weight: 600;
        font-size: 60px;  /* tamaño más grande */
        color: #003366;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================
# ESTILO
# =====================================================
st.markdown("""
    <style>
    .card {
        background: linear-gradient(145deg, #ffffff, #f9fafb);
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
        margin: 20px 0;
        border: 1px solid #e2e8f0;
    }
    .card:hover {
        transform: translateY(-4px);
        transition: all 0.3s ease;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
    }
    h3 { color: #1e293b; }
    h4 { color: #334155; margin-top: 20px; }
    p { color: #475569; margin: 4px 0; }
    .ok { color: #15803d; font-weight: 600; }
    .alerta { color: #e11d48; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# =====================================================
# FUNCIÓN PARA RENDERIZAR TARJETA
# =====================================================

def render_gage_card(g: Gage):
    dias_cal = g.calibration.dias_para_proximo() if g.calibration else None
    dias_msa = g.msa.dias_para_proximo() if g.msa else None
    estado_cal = "alerta" if dias_cal and dias_cal < 30 else "ok"
    estado_msa = "alerta" if dias_msa and dias_msa < 30 else "ok"

    html = f"""
    <div class="card">
        <h3>{g.descripcion}</h3>
        <p><b>Estatus:</b> {g.estatus}</p>
        <p><b>Área:</b> {g.area}</p>
        <p><b>Línea:</b> {g.linea}</p>
        <p><b>Operación:</b> {g.operacion}</p>
        <p><b>Nota:</b> {g.nota}</p>
        <h4>Calibración</h4>
        <p><b>Tipo:</b> {g.calibration.action_type}</p>
        <p><b>Recurrencia:</b> {g.calibration.frecuencia}</p>
        <p><b>Última:</b> {g.calibration.last_done}</p>
        <p><b>Próxima:</b> <span class="{estado_cal}">{g.calibration.next_due}</span></p>
        <h4>MSA</h4>
        <p><b>Tipo:</b> {g.msa.action_type}</p>
        <p><b>Recurrencia:</b> {g.msa.frecuencia}</p>
        <p><b>Último:</b> {g.msa.last_done}</p>
        <p><b>Próximo:</b> <span class="{estado_msa}">{g.msa.next_due}</span></p>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)



# Interfaz Streamlit
param = None  # Inicializamos la variable para evitar el NameError

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    # Capturar imagen desde la webcam
    img_file = st.camera_input("Escanear código QR")

if img_file is not None:
    # Abrir la imagen con PIL
    img = Image.open(img_file)
    
    # Mostrar la imagen capturada
    #st.image(img, caption="Imagen capturada", use_container_width=True)
    
   # Decodificar QR
    decoded_objects = decode(img)
    
    if decoded_objects:
        qr_data = decoded_objects[0].data.decode("utf-8")
        st.write("Contenido del QR:")
        st.text(qr_data)
        
        # Separar por líneas
        lines = qr_data.strip().split("\n")
        if len(lines) >= 1:
            param = lines[-1]
            st.success(f"Parámetro para la consulta: {param}")
            gage = ExecuteQry(param)
            if gage:
                #gage.render()

                # =====================================================
                # MOSTRAR TARJETA
                # =====================================================
                render_gage_card(gage)

        else:
            st.warning("El QR no tiene suficientes líneas")
    else:
        st.error("No se detectó ningún QR")




              




