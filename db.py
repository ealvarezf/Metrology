import os
import streamlit as st  # Importar Streamlit para usar sus funciones de UI
import sqlite3
import json
import pyodbc
from cryptography.fernet import Fernet

def get_connection():
    try:
        # Leer el archivo JSON de configuración
        if not os.path.exists('config.json'):
            raise FileNotFoundError("El archivo 'config.json' no fue encontrado.")

        with open('config.json', 'r') as file:
            config = json.load(file)

        key = config["NETKEY"].encode("utf-8")
        f = Fernet(key)

        SERVER = config["SERVER"]
        DATABASE = config["DATABASE"]
        USERNAME = config["USERNAME"]
        PASSWORD = f.decrypt(config["PASSWORD"].encode("utf-8")).decode("utf-8")
        DRIVER = "ODBC Driver 17 for SQL Server"

        # Crear la conexión a SQL Server
        connection_string = f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
        return pyodbc.connect(connection_string)

    except FileNotFoundError as e:
        st.error(f"Error: {e}")
    except json.JSONDecodeError:
        st.error("Error: El archivo 'config.json' no tiene un formato JSON válido.")
    except KeyError as e:
        st.error(f"Error: Falta la clave '{e}' en el archivo de configuración.")
    except pyodbc.Error as e:
        st.error(f"Error de conexión a la base de datos: {e}")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")

    return None  # En caso de error, retornar None

def get_connectionSQLite():
    try:
        DB_PATH = "GtData874 1.db3"
        # Leer el archivo JSON de configuración
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError("El archivo de base de datos no fue encontrado.")

        return sqlite3.connect(DB_PATH)

    except FileNotFoundError as e:
        st.error(f"Error: {e}")
    except sqlite3.Error as e:
        st.error(f"Error de conexión a la base de datos: {e}")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")

    return None  # En caso de error, retornar None

def get_qry(qry: str, params: list = []):
    try:     

        conn = get_connection()
        if conn is None:
            st.error("No se pudo establecer conexión con la base de datos.")
            return None, None

        cursor = conn.cursor()
        
        cursor.execute(qry, params)
        
        rows = cursor.fetchall()
        description = cursor.description
        return rows, description

    except sqlite3.Error as e:
        st.error(f"Error de base de datos: {e}")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
    finally:
        try:
            if conn:
                conn.close()
        except:
            pass  # Evita error adicional si no se pudo cerrar

    return None, None