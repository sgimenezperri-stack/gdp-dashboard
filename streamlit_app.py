import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- Configuración de página ---
st.set_page_config(page_title="People Analytics | Grupo Cenoa", layout="wide", page_icon="📈")

# --- FUNCIÓN DE CARGA ---
def get_data_from_sheet(url, sheet_name):
    base_url = url.split('/edit')[0]
    sheet_name_parsed = urllib.parse.quote(sheet_name)
    csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name_parsed}"
    df = pd.read_csv(csv_url)
    # Limpieza de columnas vacías
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

def clean_percent(column):
    """Convierte strings de porcentaje o valores con ',' a flotantes numéricos"""
    if column.dtype == 'object':
        return pd.to_numeric(column.str.replace('%', '').str.replace(',', '.'), errors='coerce')
    return column

# --- CONEXIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"

@st.cache_data(ttl=300)
def load_and_process():
    try:
        # Cargamos solo Desempeño para este análisis profundo
        df = get_data_from_sheet(SHEET_URL, "DESEMPEÑO")
        
        # Mapeo de columnas específicas según tu estructura
        # Si los nombres en el Excel varían un poco, asegúrate de que coincidan aquí:
        cols_map = {
            'empresa': 'EMPRESA', 
            'localidad': 'LOCALIDAD',
            'area': 'AREA',
            'sub_area': 'SUB AREA',
            'puesto': 'PUESTO',
            'antiguedad': 'ANTIGUEDAD', # Columna K
            'competencias': '%PUNT.EC.1°INSTANCIA COMPETENCIAS',
            'acumulado_tablero': '% ACUMULADO TABLERO',
            'desempeño_final': 'DESEMPEÑO',
            'nombre': 'APELLIDO Y NOMBRE' # Asumiendo que esta es la A o B
        }

        # Limpieza numérica de las columnas de score
        for col in ['competencias', 'acumulado_tablero', 'desempeño_final']:
            if cols_map[col] in df.columns:
                df[cols_map[col]] = clean_percent(df[cols_map[col]])
        
        return df, cols_map
    except Exception as e:
        st.error(f"Error procesando datos: {e}")
        return None, None

df_raw, m = load_and_process()

if df_raw is not None:
    # --- SIDEBAR: FILTROS REQUERIDOS ---
    st.sidebar.header("Filtros de Selección")
    
    # Filtros con lista desplegable (Multiselect para mayor flexibilidad)
    f_empresa = st.sidebar.multiselect("Empresa", options=sorted(df_raw[m['empresa']].dropna().unique()))
    f_localidad = st.sidebar.multiselect("Localidad", options=sorted(df_raw[m['localidad']].dropna().unique()))
    f_area = st.sidebar.multiselect("Área", options=sorted(df_raw[m['area']].dropna().unique()))
    f_subarea = st.sidebar.multiselect("Sub Área", options=sorted(df_raw[m['sub_area']].dropna().unique()))
    f_puesto = st.sidebar.multiselect("Puesto", options=sorted(df_raw[m['puesto']].dropna().unique()))
    
    # Filtro de Antigüedad (Slider o Multiselect)
    antiguedades = sorted(df_raw[m['antiguedad']].dropna().unique())
    f_antiguedad = st.sidebar.multiselect("Antigüedad (Años/Meses)", options=antiguedades)

    # Aplicación de filtros
    df = df_raw.copy()
    if f_empresa: df = df[df[m['empresa']].isin(f_empresa)]
    if f_localidad: df = df[df[m['localidad']].isin(f_localidad)]
    if f_area: df = df[df[m['area']].isin(f_area)]
    if f_subarea: df = df[df[m['sub_area']].isin(f_subarea)]
    if f_puesto: df = df[df[m['puesto']].isin(f_puesto)]
    if f_antiguedad: df = df[df[m['antiguedad']].isin(f_antiguedad)]

    # --- DASHBOARD ---
    st.title("📈 Análisis de Desempeño Global")
    
    # KPIs Principales
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Colaboradores", len(df))
    with c2:
        val = df[m['desempeño_final']].mean()
        st.metric("Promedio Desempeño", f"{val:.1f}%")
    with c3:
        val_comp = df[m['competencias']].mean()
        st.metric("Prom. Competencias", f"{val_comp:.1f}%")
    with c4:
        val_tab = df[m['acumulado_tablero']].mean()
        st.metric("Prom. Tablero", f"{val_tab:.1f}%")

    st.divider()

    # --- GRÁFICOS DE TOMA DE DECISIONES ---
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("Competencias vs Tablero (Mapeo)")
        fig_scatter = px.scatter(
            df, x=m['competencias'], y=m['acumulado_tablero'],
            color=m['area'], hover_name=m['nombre'],
            size=m['desempeño_final'],
            labels={m['competencias']: "Competencias %", m['acumulado_tablero']: "Tablero %"},
            title="Relación Potencial (Competencias) vs Resultados (Tablero)"
        )
        # Líneas de cuadrante (asumiendo 70% como corte)
        fig_scatter.add_hline(y=70, line_dash="dash", line_color="red")
        fig_scatter.add_vline(x=70, line_dash="dash", line_color="red")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with g2:
        st.subheader("Desempeño por Antigüedad")
        df_ant = df.groupby(m['antiguedad'])[m['desempeño_final']].mean().reset_index()
        fig_ant = px.line(df_ant, x=m['antiguedad'], y=m['desempeño_final'], markers=True,
                         title="Curva de Desempeño según Tiempo en la Empresa")
        st.plotly_chart(fig_ant, use_container_width=True)

    # --- ANÁLISIS POR PUESTO ---
    st.subheader("Ranking de Desempeño por Puesto")
    fig_puesto = px.box(df, x=m['puesto'], y=m['desempeño_final'], color=m['empresa'],
                       title="Distribución de Notas por Puesto y Empresa")
    st.plotly_chart(fig_puesto, use_container_width=True)

    # --- TABLA FINAL ---
    st.subheader("🔍 Detalle Nominal de Colaboradores")
    columnas_tabla = [m['nombre'], m['empresa'], m['puesto'], m['antiguedad'], 
                      m['competencias'], m['acumulado_tablero'], m['desempeño_final']]
    
    # Ordenar por el mejor desempeño
    st.dataframe(
        df[columnas_tabla].sort_values(by=m['desempeño_final'], ascending=False).style.background_gradient(cmap='RdYlGn', subset=[m['desempeño_final']]),
        use_container_width=True
    )

else:
    st.warning("No se pudo cargar la solapa 'DESEMPEÑO'. Revisa que el nombre sea exacto.")
