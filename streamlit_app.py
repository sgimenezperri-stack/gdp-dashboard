import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- Configuración de la página ---
st.set_page_config(page_title="Tablero Integral de Desempeño Comercial", layout="wide")

# --- HEADER Y DESCRIPCIÓN ---
st.title("📊 Tablero Integral de Desempeño y People Analytics")
st.markdown("""
Esta herramienta unifica los datos comerciales de 2025/2026 y realiza un análisis profundo del **Desempeño** para el mapeo de talento y la toma de decisiones estratégicas.
""")

# --- CONEXIÓN Y CARGA DE DATOS ---
url_principal = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit?gid=1693153873#gid=1693153873"

# Crear la conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para cargar y limpiar datos de forma segura
@st.cache_data(ttl=600)  # Caché de 10 minutos
def load_all_data(url):
    try:
        # Importar solapas solicitadas
        # Importante: los nombres de las solapas deben coincidir exactamente
        df_2025 = conn.read(spreadsheet=url, worksheet="PERFO COMERCIAL 2025")
        df_2026 = conn.read(spreadsheet=url, worksheet="PERFO COMERCIAL 2026")
        df_desempeño = conn.read(spreadsheet=url, worksheet="DESEMPEÑO")
        
        # Una limpieza básica de nulos
        df_desempeño = df_desempeño.dropna(how='all')
        
        return df_2025, df_2026, df_desempeño
    
    except Exception as e:
        st.error(f"Error cargando los datos. Verifica que la URL es correcta y que las solapas existen con esos nombres. Error: {e}")
        return None, None, None

# Cargar los datos
df_25, df_26, df_des_raw = load_all_data(url_principal)

if df_des_raw is not None:
    # --- SIDEBAR: Filtros Globales (Basados en DESEMPEÑO) ---
    st.sidebar.header("Filtros de Análisis (Desempeño)")
    
    # !!! IMPORTANTE: CAMBIA LOS NOMBRES ENTRE COMILLAS POR TUS COLUMNAS REALES !!!
    col_empresa = "Empresa"   # <-- CAMBIAR AQUI si tu columna se llama "Razón Social" etc.
    col_localidad = "Localidad" # <-- CAMBIAR AQUI
    col_area = "Area"       # <-- CAMBIAR AQUI
    col_puesto = "Puesto"     # <-- CAMBIAR AQUI
    
    # Verificar si las columnas de filtro existen antes de usarlas
    available_cols = df_des_raw.columns.tolist()
    
    empresa_filter = st.sidebar.multiselect("Filtrar por Empresa", options=df_des_raw[col_empresa].unique(), default=df_des_raw[col_empresa].unique()) if col_empresa in available_cols else []
    loc_filter = st.sidebar.multiselect("Localidad", options=df_des_raw[col_localidad].unique(), default=df_des_raw[col_localidad].unique()) if col_localidad in available_cols else []
    area_filter = st.sidebar.multiselect("Área", options=df_des_raw[col_area].unique(), default=df_des_raw[col_area].unique()) if col_area in available_cols else []
    puesto_filter = st.sidebar.multiselect("Puesto", options=df_des_raw[col_puesto].unique(), default=df_des_raw[col_puesto].unique()) if col_puesto in available_cols else []

    # Aplicar filtros
    df_des_filtered = df_des_raw[
        (df_des_raw[col_empresa].isin(empresa_filter) if col_empresa in available_cols else True) &
        (df_des_raw[col_localidad].isin(loc_filter) if col_localidad in available_cols else True) &
        (df_des_raw[col_area].isin(area_filter) if col_area in available_cols else True) &
        (df_des_raw[col_puesto].isin(puesto_filter) if col_puesto in available_cols else True)
    ]

    # --- SECCIÓN 1: VISTA COMERCIAL RÁPIDA (2025-2026) ---
    st.header("🛒 Resumen Comercial Rápido (2025/2026)")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Datos de 2025")
        st.dataframe(df_25.head(5), use_container_width=True) # Solo mostramos los primeros para no saturar
        # Aquí podrías añadir un gráfico de tendencias de 2025 si lo deseas
        
    with c2:
        st.subheader("Datos de 2026")
        st.dataframe(df_26.head(5), use_container_width=True)
        # Aquí podrías añadir un gráfico de tendencias de 2026 si lo deseas

    st.divider()

    # --- SECCIÓN 2: EL GRAN ANÁLISIS DE DESEMPEÑO ---
    st.header("🧠 Análisis Profundo de Desempeño (Mapeo de Talento)")
    
    # !!! IMPORTANTE: CAMBIA LAS COLUMNAS DE SCORE !!!
    col_colaborador = "Colaborador" # <-- CAMBIAR AQUI
    col_score = "Score_Desempeño" # <-- CAMBIAR AQUI (Columna numérica de 1-10 o 1-5)

    if col_score not in df_des_filtered.columns:
        st.error(f"La columna '{col_score}' no se encuentra en la solapa DESEMPEÑO. Revisa el código.")
    else:
        # --- KPIs Strategicos ---
        kpi1, kpi2, kpi3 = st.columns(3)
        promedio = df_des_filtered[col_score].mean()
        high_performers = df_des_filtered[df_des_filtered[col_score] >= 8] # Asumimos escala 1-10, High >= 8
        low_performers = df_des_filtered[df_des_filtered[col_score] <= 4] # Asumimos escala 1-10, Low <= 4

        kpi1.metric("Dotación Analizada", len(df_des_filtered))
        kpi2.metric("Promedio Score General", f"{promedio:.1f}")
        kpi3.metric("Talentos de Alto Desempeño (>=8)", f"{len(high_performers)} ({len(high_performers)/len(df_des_filtered)*100:.0f}%)" if len(df_des_filtered)>0 else "0")

        st.divider()

        # --- Gráficos de Análisis ---
        ga1, ga2 = st.columns(2)

        with ga1:
            # Gráfico 1: Distribución del Score
            st.subheader("Distribución de Scores de Desempeño")
            fig_hist = px.histogram(
                df_des_filtered, 
                x=col_score, 
                nbins=10, 
                title="Frecuencia de Evaluaciones",
                color_discrete_sequence=['#43a047'], # Color verde
                labels={col_score: "Score Final"}
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with ga2:
            # Gráfico 2: Desempeño por Área (Promedio)
            if col_area in available_cols:
                st.subheader("Promedio de Desempeño por Área")
                df_area_avg = df_des_filtered.groupby(col_area)[col_score].mean().reset_index()
                fig_area = px.bar(
                    df_area_avg, 
                    x=col_area, 
                    y=col_score, 
                    text=col_score,
                    title="Score Promedio",
                    labels={col_area: "Área operativa", col_score: "Score Promedio"}
                )
                fig_area.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                st.plotly_chart(fig_area, use_container_width=True)

        # --- Gráfico 3 (Ancho Completo): Variabilidad del desempeño por Localidad/Puesto ---
        st.divider()
        st.subheader("Variabilidad del Desempeño por Localidad y Puesto")
        # Usamos Boxplot para ver no solo el promedio sino la dispersión (riesgo operativo)
        if col_localidad in available_cols and col_puesto in available_cols:
            fig_box = px.box(
                df_des_filtered, 
                x=col_puesto, 
                y=col_score, 
                color=col_localidad, 
                points="all", 
                title="Distribución de Scores por Puesto (Segmentado por Localidad)",
                labels={col_score: "Score de Desempeño"}
            )
            st.plotly_chart(fig_box, use_container_width=True)

        # --- Detalle de Colaboradores (La Tabla de Decisión) ---
        st.divider()
        st.subheader("🔍 Tabla Detallada para Toma de Decisiones")
        # Mostramos las columnas más relevantes
        cols_finales = [col_colaborador, col_puesto, col_area, col_localidad, col_empresa, col_score]
        
        # Verificar si todas existen
        cols_to_show = [c for c in cols_finales if c in df_des_filtered.columns]
        
        # Permitir ordenar por score automáticamente (más útil para decisiones rápidas)
        st.dataframe(df_des_filtered[cols_to_show].sort_values(by=col_score, ascending=False), use_container_width=True)
else:
    st.warning("No se pudieron cargar los datos de desempeño. Por favor revisa la consola de errores.")
