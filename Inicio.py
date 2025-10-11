import streamlit as st
import pandas as pd
import os
from pyzbar.pyzbar import decode
from PIL import Image
from db import get_qry

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


consulta = """
                SELECT S.Status_RID, StatusName, L.Location_RID, L.LocationName AREA, CurrentLocation_RID_FK, LO.LocationName LINEA, Gage_SN, GageDescriptionName, RecurrenceOptionType, Period, RecurrenceType,
                    LastDone, NextDue, G.Notes  
                FROM ActionSchedules LEFT JOIN GageCalibrations ON ActionSchedule_RID = ActionSchedule_RID_FK
                                    LEFT JOIN Gages G ON Gage_RID_FK = Gage_RID
                                    LEFT JOIN GageDescriptions ON GageDescription_RID = GageDescription_RID_FK
                                    LEFT JOIN Locations L ON L.Location_RID = StorageLocation_RID_FK
                                    LEFT JOIN Locations LO ON LO.Location_RID = CurrentLocation_RID_FK
                                    LEFT JOIN Custodians ON Custodian_RID = L.Custodian_RID_FK
                                    LEFT JOIN GageTypes ON GageType_RID = GageType_RID_FK
                                    LEFT JOIN Status S ON S.Status_RID = Status_RID_FK
                WHERE Gage_ID = ?;
           """


def ExecuteQry(): 
    try:
        rows, description  = get_qry(consulta, [param])
        if rows:
            df = pd.DataFrame.from_records(rows, columns=[desc[0] for desc in description])
            st.dataframe(df, use_container_width=True)

            #df_transposed = df.T
            #df_transposed.columns = ['Valor']  # Opcional, para renombrar la columna
            #st.dataframe(df_transposed, use_container_width=True)
            #st.table(df_transposed)

            df_transposed = df.T
            df_transposed.columns = ['Valor']
            # Convertir todo a string
            df_transposed['Valor'] = df_transposed['Valor'].astype(str)
            # Mostrar tabla centrada
            st.markdown("<div style='width: 60%; margin: auto;'>", unsafe_allow_html=True)
            st.table(df_transposed)
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")

    return None  # En caso de error, retornar None


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
            ExecuteQry()
        else:
            st.warning("El QR no tiene suficientes líneas")
    else:
        st.error("No se detectó ningún QR")




              




