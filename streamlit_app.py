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
    df.columns = df.columns.str.strip() # Limpiar espacios en nombres de columnas
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

# --- CONEXIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = get_data_from_sheet(SHEET_URL, "DESEMPEÑO")
        
        # Mapeo por posición (blindado por si cambian los nombres)
        def get_col_name(preferred_name, index):
            if preferred_name in df.columns: return preferred_name
            return df.columns[index] if len(df.columns) > index else None

        m = {
            'nombre': get_col_name('APELLIDO Y NOMBRE', 0),
            'empresa': get_col_name('EMPRESA', 2),
            'localidad': get_col_name('LOCALIDAD', 3),
            'area': get_col_name('AREA', 4),  # Columna E
            'puesto': get_col_name('PUESTO', 5),
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS',
            'tablero': '% ACUMULADO TABLERO',
            'final': 'DESEMPEÑO'
        }
        
        # --- LIMPIEZA NUMÉRICA CRÍTICA ---
        for col_key in ['comp', 'tablero', 'final']:
            col_name = m[col_key]
            if col_name in df.columns:
                # Convertimos a string, quitamos %, reemplazamos coma por punto y pasamos a número
                df[col_name] = pd.to_numeric(
                    df[col_name].astype(str).str.replace('%', '').str.replace(',', '.').str.strip(), 
                    errors='coerce'
                )
        
        return df, m
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

df_raw, m = load_data()

if df_raw is not None:
    # --- SIDEBAR ---
    st.sidebar.header("Filtros de Selección")
    
    def safe_filter(label, col_name):
        if col_name and col_name in df_raw.columns:
            return st.sidebar.multiselect(label, options=sorted(df_raw[col_name].dropna().unique()))
        return []

    f_empresa = safe_filter("Empresa", m['empresa'])
    f_localidad = safe_filter("Localidad", m['localidad'])
    f_area = safe_filter("Área", m['area'])
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
        # MÉTRICAS (Escritas de forma más segura)
        c1, c2, c3 = st.columns(3)
        
        c1.metric("Colaboradores", len(df))
        
        # Promedio Competencias
        val_comp = df[m['comp']].mean() if m['comp'] in df.columns else 0
        c2.metric("Prom. Competencias", f"{val_comp:.1f}%")
        
        # Promedio Tablero
        val_tab = df[m['tablero']].mean() if m['tablero'] in df.columns else 0
        c3.metric("Prom. Tablero", f"{val_tab:.1f}%")

        st.divider()

        # --- GRÁFICO SCATTER ---
        if m['comp'] in df.columns and m['tablero'] in df.columns:
            st.subheader("Matriz de Desempeño (Potencial vs Resultados)")
            
            # Solo graficamos si hay datos numéricos válidos
            df_plot = df.dropna(subset=[m['comp'], m['tablero']])
            
            if not df_plot.empty:
                fig = px.scatter(
                    df_plot, x=m['comp'], y=m['tablero'],
                    color=m['area'] if m['area'] in df.columns else None,
                    hover_name=m['nombre'] if m['nombre'] in df.columns else None,
                    size=m['final'].fillna(0) if m['final'] in df.columns else None,
                    labels={m['comp']: "Competencias %", m['tablero']: "Tablero %"},
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Meta 70%")
                fig.add_vline(x=70, line_dash="dash", line_color="red")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay suficientes datos numéricos para mostrar el gráfico.")

        # --- TABLA DETALLADA ---
        st.subheader("Listado Detallado")
        cols_finales = [c for c in [m['nombre'], m['area'], m['puesto'], m['final']] if c is not None]
        st.dataframe(df[cols_finales].sort_values(by=m['final'], ascending=False).dropna(subset=[m['final']]), use_container_width=True)
    else:
        st.info("Ajusta los filtros para ver los resultados de los 539 colaboradores.")
