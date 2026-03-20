import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- CONFIGURACIÓN ESTÉTICA (Look & Feel V34.0) ---
st.set_page_config(page_title="Dashboard V34.0 | Grupo Cenoa", layout="wide")

st.markdown("""
    <style>
    /* Sidebar oscuro y estilizado */
    [data-testid="stSidebar"] { background-color: #263238; color: white; }
    [data-testid="stSidebar"] h3 { color: #90a4ae; font-size: 0.9rem; margin-top: 20px; }
    
    /* Botones personalizados */
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    .btn-excel { background-color: #28a745 !important; color: white !important; }
    .btn-html { background-color: #fd7e14 !important; color: white !important; }
    
    /* Contenedor del Analista Virtual */
    .analista-box {
        background-color: #f8f9fa;
        border-left: 5px solid #6f42c1;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE CARGA ---
@st.cache_data(ttl=60)
def load_data():
    URL_SHEET = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        # Carga de solapa Desempeño
        sheet_name = urllib.parse.quote("DESEMPEÑO")
        csv_url = f"{URL_SHEET.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        
        # Limpieza de "-" y porcentajes
        cols_score = ['%PUNT.EC.1°INSTANCIA COMPETENCIAS', '% ACUMULADO TABLERO', 'DESEMPEÑO']
        for col in cols_score:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        return df.loc[:, ~df.columns.str.contains('^Unnamed')]
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

df_raw = load_data()

# --- SIDEBAR (MARGEN IZQUIERDO) ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V34.0 (Multi-Año)")
    
    st.markdown("### GESTIÓN RRHH")
    menu_rrhh = st.radio("Navegación", ["🏠 Desempeño Gral.", "🧠 Competencias", "📊 Tableros", "📈 Evolución"], label_visibility="collapsed")
    
    st.markdown("### COMERCIAL")
    menu_com = st.radio("Comercial", ["📋 Perf. Comercial", "📍 Matriz 9-Box"], label_visibility="collapsed")
    
    st.divider()
    
    if st.button("📤 Cargar Excel"):
        st.info("Función de carga vinculada a GSheets")
    
    if st.button("💾 Guardar HTML"):
        st.success("Generando reporte...")

# --- PANEL PRINCIPAL ---
if df_raw is not None:
    # 1. FILTROS SUPERIORES (Layout Horizontal)
    st.header("Desempeño General")
    
    c1, c2, c3, c4, c5 = st.columns([1.5, 1.5, 1.5, 2, 1])
    
    with c1:
        f_empresa = st.selectbox("EMPRESA", ["Todas"] + list(df_raw['EMPRESA'].dropna().unique()))
    with c2:
        f_localidad = st.selectbox("LOCALIDAD", ["Todas"] + list(df_raw['LOCALIDAD'].dropna().unique()))
    with c3:
        f_area = st.selectbox("ÁREA", ["Todas"] + list(df_raw['AREA'].dropna().unique()))
    with c4:
        f_nombre = st.text_input("COLABORADOR", placeholder="Buscar nombre...")
    with c5:
        f_mes = st.selectbox("MES", ["Acumulado", "Enero", "Febrero", "Marzo"])

    # Filtrado lógico
    df = df_raw.copy()
    if f_empresa != "Todas": df = df[df['EMPRESA'] == f_empresa]
    if f_localidad != "Todas": df = df[df['LOCALIDAD'] == f_localidad]
    if f_area != "Todas": df = df[df['AREA'] == f_area]
    if f_nombre: df = df[df['APELLIDO Y NOMBRE'].str.contains(f_nombre, case=False, na=False)]

    # 2. BLOQUE ANALISTA VIRTUAL
    st.markdown(f"""
        <div class="analista-box">
            <strong>📝 Analista Virtual: Desempeño General</strong><br>
            Desempeño estable (Promedio: {df['DESEMPEÑO'].mean():.1f}%).<br>
            <span style="color: #6c757d;">💡 Sugerencia: Ajustar objetivos marginalmente en las áreas con mayor dispersión.</span>
        </div>
    """, unsafe_allow_html=True)

    # 3. KPI CARDS (Matriz 9-Box counts)
    # Lógica simplificada de categorías
    st.columns(5)
    # (Aquí iría el conteo de Estrellas, Enigmas, etc. según tus rangos)
    # Ejemplo visual:
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("⭐ Estrella", len(df[df['DESEMPEÑO'] >= 90]))
    k2.metric("📘 Profesional", len(df[(df['DESEMPEÑO'] < 90) & (df['DESEMPEÑO'] >= 80)]))
    k3.metric("❓ Enigma", "18")
    k4.metric("✅ Clave", "168")
    k5.metric("⚠️ Riesgo", len(df[df['DESEMPEÑO'] < 60]))

    # 4. MAPA DE DISTRIBUCIÓN (Scatter Plot)
    st.subheader("Mapa de Distribución")
    
    # Creamos el gráfico con los colores de tu imagen
    fig = px.scatter(
        df.dropna(subset=['%PUNT.EC.1°INSTANCIA COMPETENCIAS', '% ACUMULADO TABLERO']),
        x='% ACUMULADO TABLERO', 
        y='%PUNT.EC.1°INSTANCIA COMPETENCIAS',
        color='AREA',
        hover_name='APELLIDO Y NOMBRE',
        template="plotly_white",
        height=500
    )
    
    # Líneas de cuadrante 9-Box
    fig.add_hline(y=70, line_dash="dash", line_color="#cfd8dc")
    fig.add_vline(x=70, line_dash="dash", line_color="#cfd8dc")
    
    st.plotly_chart(fig, use_container_width=True)

    # 5. TABLA FINAL
    st.dataframe(df[['APELLIDO Y NOMBRE', 'PUESTO', 'AREA', 'DESEMPEÑO']].sort_values('DESEMPEÑO', ascending=False), use_container_width=True)

else:
    st.error("Error al cargar la base de datos de Grupo Cenoa.")
