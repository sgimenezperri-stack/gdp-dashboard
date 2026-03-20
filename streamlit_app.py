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
    # Limpiamos espacios en blanco al inicio/final de los nombres de las columnas
    df.columns = df.columns.str.strip()
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

# --- CONEXIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = get_data_from_sheet(SHEET_URL, "DESEMPEÑO")
        
        # --- MAPEO INTELIGENTE POR NOMBRE O POSICIÓN ---
        def get_col(name, index):
            if name in df.columns: return name
            return df.columns[index] if len(df.columns) > index else None

        # Asignamos según tus indicaciones y el orden estándar de las letras
        m = {
            'nombre': get_col('APELLIDO Y NOMBRE', 0),    # Columna A
            'empresa': get_col('EMPRESA', 2),             # Asumimos C
            'localidad': get_col('LOCALIDAD', 3),         # Asumimos D
            'area': get_col('AREA', 4),                  # COLUMNA E (Índice 4)
            'puesto': get_col('PUESTO', 5),               # Asumimos F
            'antiguedad': get_col('ANTIGUEDAD', 10),      # COLUMNA K (Índice 10)
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS',
            'tablero': '% ACUMULADO TABLERO',
            'final': 'DESEMPEÑO'
        }
        return df, m
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

df_raw, m = load_data()

if df_raw is not None:
    # --- LIMPIEZA NUMÉRICA ---
    for col_key in ['comp', 'tablero', 'final']:
        col_name = m[col_key]
        if col_name in df_raw.columns:
            df_raw[col_name] = pd.to_numeric(df_raw[col_name].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce')

    # --- SIDEBAR ---
    st.sidebar.header("Filtros de Selección")
    
    def safe_filter(label, col_name):
        if col_name and col_name in df_raw.columns:
            return st.sidebar.multiselect(label, options=sorted(df_raw[col_name].dropna().unique()))
        return []

    f_empresa = safe_filter("Empresa", m['empresa'])
    f_localidad = safe_filter("Localidad", m['localidad'])
    f_area = safe_filter("Área (Col E)", m['area'])
    f_puesto = safe_filter("Puesto", m['puesto'])

    # Aplicar Filtros
    df = df_raw.copy()
    if f_empresa: df = df[df[m['empresa']].isin(f_empresa)]
    if f_localidad: df = df[df[m['localidad']].isin(f_localidad)]
    if f_area: df = df[df[m['area']].isin(f_area)]
    if f_puesto: df = df[df[m['puesto']].isin(f_puesto)]

    # --- DASHBOARD ---
    st.title("📈 Gestión de Talento - Grupo Cenoa")
    
    if not df.empty:
        # Métricas
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Colaboradores", len(df))
        with c2: st.metric("Prom. Competencias", f"{df[m['comp']].mean():.1f}%") if m['comp'] in df.columns else None
        with c3: st.metric("Prom. Tablero", f"{df[m['tablero']].mean():.1f}%") if m['tablero'] in df.columns else None

        st.divider()

        # Gráfico Scatter (Potencial vs Resultados)
        st.subheader("Matriz de Desempeño (Potencial vs Resultados)")
        
        # Validamos que las columnas necesarias existan para el gráfico
        if m['comp'] in df.columns and m['tablero'] in df.columns:
            fig = px.scatter(
                df, x=m['comp'], y=m['tablero'], 
                color=m['area'] if m['area'] in df.columns else None,
                hover_name=m['nombre'] if m['nombre'] in df.columns else None,
                size=m['final'] if m['final'] in df.columns else None,
                labels={m['comp']: "Competencias %", m['tablero']: "Tablero Acumulado %"},
                template="plotly_white"
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Meta")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Faltan columnas de score para generar el gráfico.")

        # Tabla de Detalles
        st.subheader("Listado Detallado")
        cols_mostrar = [c for c in [m['nombre'], m['area'], m['puesto'], m['final']] if c is not None]
        st.dataframe(df[cols_mostrar].sort_values(m['final'], ascending=False), use_container_width=True)
    else:
        st.info("Usa los filtros de la izquierda para analizar los datos.")
