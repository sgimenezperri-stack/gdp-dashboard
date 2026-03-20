import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- Configuración ---
st.set_page_config(page_title="Tablero de Desempeño - Grupo Cenoa", layout="wide")

# URL limpia (usamos .strip() para eliminar espacios invisibles)
URL_SHEET = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit?usp=sharing".strip()

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def load_data_safe():
    try:
        # Leemos las solapas asegurando que los nombres no tengan espacios accidentales
        # Si el error persiste, verifica que en Google Sheets las pestañas se llamen EXACTAMENTE así
        df_2025 = conn.read(spreadsheet=URL_SHEET, worksheet="PERFO COMERCIAL 2025")
        df_2026 = conn.read(spreadsheet=URL_SHEET, worksheet="PERFO COMERCIAL 2026")
        df_des = conn.read(spreadsheet=URL_SHEET, worksheet="DESEMPEÑO")
        
        return df_2025, df_2026, df_des
    except Exception as e:
        st.error(f"Error crítico de conexión: {e}")
        st.info("💡 Consejo: Revisa que la solapa 'PERFO COMERCIAL 2025' no tenga un espacio extra al final de su nombre en Google Sheets.")
        return None, None, None

df_25, df_26, df_des_raw = load_data_safe()

# --- VALIDACIÓN DE DATOS ---
if df_des_raw is not None:
    st.success("✅ Datos conectados correctamente")
    
    # Aquí iría el resto de tu lógica de filtros y gráficos que armamos antes...
    # Ejemplo rápido de métricas:
    st.header("Análisis de Desempeño")
    st.write(df_des_raw.head())
