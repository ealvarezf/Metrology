import streamlit as st
import pandas as pd
import os
from pyzbar.pyzbar import decode
from PIL import Image
from db import get_qry
from gage import ExecuteQry, Gage
import cv2
import numpy as np

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
        <h1 style='color: #003366; margin-bottom: 0;'>METROLOGÍA</h1>
        <h3 style='color: #666;'>Nexteer Automotive</h3>
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
#st.write(f"Has seleccionado: **{db}**")

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
    h3 { color: #475569; } 
    h4 { color: #475569; margin-top: 20px; }
    p { color: #475569; margin: 4px 0; }
    .ok { color: #15803d; font-weight: 600; }
    .alerta { color: #e11d48; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

#    h3 { color: #1e293b; } 
#    h4 { color: #334155; margin-top: 20px; }

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
    <div class="card">
        <h2>{p}</h2>
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
# Inicializamos valores en session_state si no existen

if "manual_param" not in st.session_state:
    st.session_state.manual_param = ""
if "img_file" not in st.session_state:
    st.session_state.img_file = None

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    # Capturar imagen desde la webcam
    img_file = st.camera_input("Escanear código QR")

    # Detectar cuando se limpia la foto (img_file vuelve a None)
    if img_file is None and st.session_state.img_file is not None:
        # Se limpió la foto, también limpiamos el input manual
        st.session_state.manual_param = ""

    # Guardar el estado actual
    st.session_state.img_file = img_file

    # Alternativa manual
    st.markdown("<hr>", unsafe_allow_html=True)
    st.text_input(
        "O ingresa el código manualmente:",
        placeholder="Ejemplo: GAGE12345",
        label_visibility="visible",
        key="manual_param"  # <-- clave que mantiene sincronización
    )

if img_file is not None:
    # Abrir la imagen con PIL
    img = Image.open(img_file)

    #Lineas para preprocesamiento de imagen
    img1 = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # 1. Gris
    gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)

    # 2. Aumentar contraste con CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)

    # 3. Filtrar ruido sin perder bordes
    filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)

    # 4. Binarización Otsu
    _, thresh = cv2.threshold(filtered, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)

    img = Image.fromarray(thresh)
    # Fin de preprocesamiento

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

        else:
            st.warning("El QR no tiene suficientes líneas")
            param = None
    else:
        st.error("No se detectó ningún QR")
        param = None
else:
    param = None

# Si el usuario escribió el código manualmente, usarlo
if not param and st.session_state.manual_param:
    param = st.session_state.manual_param.strip()

    st.info(f"Usando el parámetro ingresado manualmente: {param}")

# Ejecutar la consulta si tenemos un parámetro
if param:
    gage = ExecuteQry(db, param)
    if gage:
        render_gage_card(gage, {param})
    else:
        st.error("No se encontraron resultados para el parámetro ingresado.")    





              




