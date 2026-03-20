import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

st.set_page_config(page_title="People Analytics | Grupo Cenoa", layout="wide")

# --- FUNCIÓN DE CARGA ---
def get_data_from_sheet(url, sheet_name):
    base_url = url.split('/edit')[0]
    sheet_name_parsed = urllib.parse.quote(sheet_name)
    csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name_parsed}"
    df = pd.read_csv(csv_url)
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

# --- CONEXIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"

@st.cache_data(ttl=60)
def load_and_debug():
    try:
        df = get_data_from_sheet(SHEET_URL, "DESEMPEÑO")
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

df_raw = load_and_debug()

if df_raw is not None:
    # --- MODO DIAGNÓSTICO (Solo tú lo verás) ---
    with st.expander("🛠️ CONFIGURACIÓN DE COLUMNAS (Haz clic aquí si ves errores)"):
        st.write("Copia los nombres exactos de aquí abajo y pégalos en el código si es necesario:")
        st.write(df_raw.columns.tolist())

    # --- MAPEO MANUAL (Ajusta los nombres según lo que veas en el diagnóstico) ---
    # He ajustado estos nombres basándome en lo que vi en tus fotos
    m = {
        'empresa': 'EMPRESA',           # Si sale error, prueba con 'AREA' (por lo que vi en tu foto)
        'localidad': 'LOCALIDAD',
        'area': 'AREA',                 # Si sale error, revisa si es 'UNIDAD' o 'SECTOR'
        'sub_area': 'SUB AREA',
        'puesto': 'PUESTO',
        'antiguedad': 'ANTIGUEDAD',     # Columna K
        'nombre': 'APELLIDO Y NOMBRE',
        'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS',
        'tablero': '% ACUMULADO TABLERO',
        'final': 'DESEMPEÑO'
    }

    # --- LIMPIEZA AUTOMÁTICA DE DATOS ---
    # Convertir a número y quitar el símbolo %
    for col_key in ['comp', 'tablero', 'final']:
        col_name = m[col_key]
        if col_name in df_raw.columns:
            df_raw[col_name] = pd.to_numeric(df_raw[col_name].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce')

    # --- SIDEBAR CON VALIDACIÓN ---
    st.sidebar.header("Filtros de Selección")
    
    def safe_multiselect(label, col_name):
        if col_name in df_raw.columns:
            return st.sidebar.multiselect(label, options=sorted(df_raw[col_name].dropna().unique()))
        else:
            st.sidebar.warning(f"No encontré la columna: {col_name}")
            return []

    f_empresa = safe_multiselect("Empresa", m['empresa'])
    f_localidad = safe_multiselect("Localidad", m['localidad'])
    f_area = safe_multiselect("Área", m['area'])
    f_puesto = safe_multiselect("Puesto", m['puesto'])

    # Aplicar Filtros
    df = df_raw.copy()
    if f_empresa: df = df[df[m['empresa']].isin(f_empresa)]
    if f_localidad: df = df[df[m['localidad']].isin(f_localidad)]
    if f_area: df = df[df[m['area']].isin(f_area)]
    if f_puesto: df = df[df[m['puesto']].isin(f_puesto)]

    # --- DASHBOARD ---
    st.title("🚀 Desempeño Grupo Cenoa")
    
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Colaboradores", len(df))
        with c2: st.metric("Prom. Competencias", f"{df[m['comp']].mean():.1f}%")
        with c3: st.metric("Prom. Tablero", f"{df[m['tablero']].mean():.1f}%")

        st.divider()

        # Gráfico de Competencias vs Resultados
        fig = px.scatter(df, x=m['comp'], y=m['tablero'], 
                         color=m['area'] if m['area'] in df.columns else None,
                         hover_name=m['nombre'], size=m['final'],
                         title="Matriz de Desempeño (Potencial vs Resultados)")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Listado Detallado")
        st.dataframe(df[[m['nombre'], m['puesto'], m['final']]].sort_values(m['final'], ascending=False))
    else:
        st.info("Selecciona filtros para ver los datos.")

else:
    st.error("No se pudo cargar la base de datos.")
