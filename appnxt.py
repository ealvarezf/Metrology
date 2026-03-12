import streamlit as st
import pandas as pd
import os
from pyzbar.pyzbar import decode
from PIL import Image
from db import get_qry
from gage import ExecuteQry, Gage

# Obtener parámetros del URL
query_params = st.query_params

# Leer un parámetro específico
prm_gage = query_params.get("gage")

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
        <h1 style='color: #666; margin-bottom: 0;'>METROLOGÍA</h1>
        <hr style='border: 2px solid #003366; width: 60%; margin: auto;'>
    </div>
    """,
    unsafe_allow_html=True
)

# --- LISTA INTERACTIVA ---
opciones = ["Planta 66", "Planta 65", "Planta 63"]
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    seleccion = st.selectbox("Selecciona la planta:", opciones, index=0, key="planta_select")
    
seleccion = seleccion.replace("Planta ", "")
if seleccion == "66": seleccion = ""
db = seleccion

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
            body {
                font-family: 'Segoe UI', sans-serif;
                background: #eef2f7;
                padding: 40px;
            }

            .spec-container {
                max-width: 900px;
                margin: auto;
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.1);
            }

            .title {
                font-size: 28px;
                font-weight: bold;
                color: #1f2d3d;
                margin-bottom: 20px;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }

            .section {
                margin-top: 20px;
            }

            .section-title {
                font-weight: bold;
                color: #3498db;
                margin-bottom: 10px;
            }

            table {
                width: 100%;
                border-collapse: collapse;
            }

            td {
                padding: 8px;
                border-bottom: 1px solid #ddd;
            }

            td:first-child {
                font-weight: bold;
                width: 30%;
                background: #f9fafc;
            }
            .ok { color: #15803d; font-weight: 600; }
            .alerta { color: #e11d48; font-weight: 600; }
        </style>
""", unsafe_allow_html=True)

# =====================================================
# FUNCIÓN PARA RENDERIZAR TARJETA
# =====================================================

def render_gage_card(g: Gage, p):
        # Si p es un conjunto, extrae el primer elemento
    if isinstance(p, set):
        p = next(iter(p))

    dias_cal = g.calibration.dias_para_proximo() if g.calibration else None
    dias_msa = g.msa.dias_para_proximo() if g.msa else None
    estado_cal = "alerta" if dias_cal and dias_cal < 1 else "ok"
    estado_msa = "alerta" if dias_msa and dias_msa < 1 else "ok"

    html = f"""
    <div class="spec-container">
        <div class="title">{p} | {g.descripcion}</div>
        <div class="section-title">INFORMACION GENERAL</div>
        <table>
            <tr><td>Estatus:</td><td>{g.estatus}</td></tr>
            <tr><td>Área:</td><td>{g.area}</td></tr>
            <tr><td>Línea:</td><td>{g.linea}</td></tr>
            <tr><td>Operación:</td><td>{g.operacion}</td></tr>
            <tr><td>Nota:</td><td>{g.nota}</td></tr>
        </table>
        <div class="section-title">CALIBRACION</div>
        <table>
            <tr><td>Tipo:</td><td>{g.calibration.action_type}</td></tr>
            <tr><td>Recurrencia:</td><td>{g.calibration.frecuencia}</td></tr>
            <tr><td>Última:</td><td>{g.calibration.last_done}</td></tr>
            <tr><td>Próxima:</td><td><span class="{estado_cal}">{g.calibration.next_due}</span></td></tr>
        </table>
        <div class="section-title">MSA</div>
        <table>
            <tr><td>Tipo:</td><td>{g.msa.action_type}</td></tr>
            <tr><td>Recurrencia:</td><td>{g.msa.frecuencia}</td></tr>
            <tr><td>Última:</td><td>{g.msa.last_done}</td></tr>
            <tr><td>Próxima:</td><td><span class="{estado_msa}">{g.msa.next_due}</span></td></tr>
        </table>                
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

# Interfaz Streamlit
param = None  # Inicializamos la variable para evitar el NameError
# Inicializamos valores en session_state si no existen