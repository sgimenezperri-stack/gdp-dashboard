import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- Configuración de página ---
st.set_page_config(page_title="People Analytics - Grupo Cenoa", layout="wide", page_icon="📈")

# --- Estilo personalizado ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE CONEXIÓN ROBUSTA ---
def get_data_from_sheet(url, sheet_name):
    # Esta es la forma más estable de leer Google Sheets con espacios en los nombres
    base_url = url.split('/edit')[0]
    sheet_name_parsed = urllib.parse.quote(sheet_name)
    csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name_parsed}"
    return pd.read_csv(csv_url)

# URL de tu Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"

# --- CARGA DE DATOS ---
@st.cache_data(ttl=600)
def load_all_data():
    try:
        df_25 = get_data_from_sheet(SHEET_URL, "PERFO COMERCIAL 2025")
        df_26 = get_data_from_sheet(SHEET_URL, "PERFO COMERCIAL 2026")
        df_des = get_data_from_sheet(SHEET_URL, "DESEMPEÑO")
        return df_25, df_26, df_des
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return None, None, None

df_25, df_26, df_des = load_all_data()

if df_des is not None:
    # --- LIMPIEZA DE DATOS ---
    # Eliminamos columnas vacías que a veces trae Google Sheets
    df_des = df_des.loc[:, ~df_des.columns.str.contains('^Unnamed')]
    
    # --- SIDEBAR (FILTROS) ---
    st.sidebar.image("https://www.grupocenoa.com.ar/wp-content/uploads/2021/05/logo-cenoa.png", width=150) # Logo genérico o el tuyo
    st.sidebar.title("Filtros Globales")
    
    # Intentamos detectar columnas dinámicamente
    cols = df_des.columns.tolist()
    
    # Mapeo de columnas (Asegúrate que coincidan con tu Excel)
    col_emp = "Empresa" if "Empresa" in cols else cols[0]
    col_loc = "Localidad" if "Localidad" in cols else cols[1]
    col_area = "Area" if "Area" in cols else cols[2]
    col_puesto = "Puesto" if "Puesto" in cols else cols[3]
    col_score = "Desempeño" if "Desempeño" in cols else (cols[-1] if len(cols)>4 else cols[0])

    f_empresa = st.sidebar.multiselect("Empresa", options=df_des[col_emp].unique(), default=df_des[col_emp].unique())
    f_localidad = st.sidebar.multiselect("Localidad", options=df_des[col_loc].unique(), default=df_des[col_loc].unique())
    f_area = st.sidebar.multiselect("Área", options=df_des[col_area].unique(), default=df_des[col_area].unique())

    # Aplicar Filtros
    mask = (df_des[col_emp].isin(f_empresa)) & (df_des[col_loc].isin(f_localidad)) & (df_des[col_area].isin(f_area))
    df_filtered = df_des[mask]

    # --- DASHBOARD PRINCIPAL ---
    st.title("🚀 Dashboard de Mapeo de Talento")
    
    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Colaboradores", len(df_filtered))
    with k2:
        avg_score = df_filtered[col_score].mean() if pd.api.types.is_numeric_dtype(df_filtered[col_score]) else 0
        st.metric("Promedio Desempeño", f"{avg_score:.2f}")
    with k3:
        st.metric("Localidades", df_filtered[col_loc].nunique())
    with k4:
        st.metric("Áreas", df_filtered[col_area].nunique())

    st.divider()

    # --- ANÁLISIS GRÁFICO ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Distribución por Desempeño")
        fig_bar = px.histogram(df_filtered, x=col_score, color=col_emp, 
                               marginal="box", title="Frecuencia de Scores",
                               color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("Desempeño Promedio por Puesto")
        df_puesto = df_filtered.groupby(col_puesto)[col_score].mean().reset_index().sort_values(col_score)
        fig_puesto = px.bar(df_puesto, y=col_puesto, x=col_score, orientation='h',
                            color=col_score, color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_puesto, use_container_width=True)

    # --- MATRIZ DE TALENTO (9-BOX) ---
    st.subheader("📍 Matriz de Decisión Estratégica")
    # Nota: Para una 9-box real necesitarías una columna de "Potencial". 
    # Aquí graficamos Desempeño vs Localidad/Empresa como ejemplo de dispersión.
    fig_scatter = px.scatter(df_filtered, x=col_loc, y=col_score, color=col_area,
                             size=[10]*len(df_filtered), hover_name=cols[0],
                             title="Dispersión de Talento por Localidad")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # --- TABLA DE DATOS ---
    with st.expander("Ver base de datos completa"):
        st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("Esperando conexión con Google Sheets... Asegúrate de que el archivo sea público.")
