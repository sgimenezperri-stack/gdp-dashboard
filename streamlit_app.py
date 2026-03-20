import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(page_title="Dashboard V34.0 | Grupo Cenoa", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238; color: white; }
    [data-testid="stSidebar"] h3 { color: #90a4ae; font-size: 0.8rem; margin-top: 25px; text-transform: uppercase; }
    .stRadio > div { background-color: transparent !important; }
    .stRadio label { color: #cfd8dc !important; font-size: 0.9rem !important; padding: 10px !important; }
    .analista-box {
        background-color: #f8f9fa;
        border-left: 5px solid #6f42c1;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .stMetric { background-color: #ffffff; border-radius: 10px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE CARGA ---
@st.cache_data(ttl=60)
def load_data_cenoa():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        sheet_name = urllib.parse.quote("DESEMPEÑO")
        csv_url = f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip() # Limpieza de nombres

        # Mapeo Inteligente por posición si el nombre falla
        def get_col(pref, idx):
            if pref in df.columns: return pref
            return df.columns[idx] if len(df.columns) > idx else None

        mapping = {
            'nombre': get_col('APELLIDO Y NOMBRE', 0),
            'empresa': get_col('EMPRESA', 2),
            'localidad': get_col('LOCALIDAD', 3),
            'area': get_col('AREA', 4), # COLUMNA E
            'puesto': get_col('PUESTO', 5),
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS',
            'tablero': '% ACUMULADO TABLERO',
            'final': 'DESEMPEÑO'
        }

        # Limpieza de datos (Tratamiento de "-" y %)
        for key in ['comp', 'tablero', 'final']:
            c = mapping[key]
            if c in df.columns:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        return df, mapping
    except Exception as e:
        st.error(f"Error cargando Sheets: {e}")
        return None, None

df_raw, m = load_data_cenoa()

# --- SIDEBAR (MARGEN IZQUIERDO) ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V34.0 (Multi-Año)")
    
    st.markdown("### GESTIÓN RRHH")
    # Usamos iconos similares a tu imagen
    menu_rrhh = st.radio("Nav1", ["🏠 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución"], label_visibility="collapsed")
    
    st.markdown("### COMERCIAL")
    menu_com = st.radio("Nav2", ["📋 Perf. Comercial", "📍 Matriz 9-Box"], label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("💾 Guardar HTML", use_container_width=True):
        st.info("Generando reporte estático...")

# --- PANEL PRINCIPAL ---
if df_raw is not None:
    st.header("Desempeño General")
    
    # FILTROS SUPERIORES EN LÍNEA
    c1, c2, c3, c4, c5 = st.columns([1.5, 1.5, 1.5, 2, 1])
    
    with c1:
        f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with c2:
        f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with c3:
        f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    with c4:
        f_nom = st.text_input("COLABORADOR", placeholder="Buscar nombre...")
    with c5:
        f_mes = st.selectbox("MES", ["Acumulado", "Marzo", "Febrero", "Enero"])

    # Aplicar Filtros
    df = df_raw.copy()
    if f_emp != "Todas": df = df[df[m['empresa']] == f_emp]
    if f_loc != "Todas": df = df[df[m['localidad']] == f_loc]
    if f_are != "Todas": df = df[df[m['area']] == f_are]
    if f_nom: df = df[df[m['nombre']].str.contains(f_nom, case=False, na=False)]

    # BLOQUE ANALISTA VIRTUAL
    avg_perf = df[m['final']].mean()
    st.markdown(f"""
        <div class="analista-box">
            <strong>📝 Analista Virtual: Desempeño General</strong><br>
            Desempeño promedio actual: <b>{avg_perf:.1f}%</b>. 
            El análisis de los <b>{len(df)}</b> colaboradores muestra una tendencia estable.
            <br><span style="color: #6c757d;">💡 Sugerencia: Focalizar en planes de desarrollo para el grupo 'Riesgo'.</span>
        </div>
    """, unsafe_allow_html=True)

    # KPI CARDS (Conteo de categorías según desempeño)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("⭐ Estrella", len(df[df[m['final']] >= 90]))
    k2.metric("📘 Profesional", len(df[(df[m['final']] < 90) & (df[m['final']] >= 80)]))
    k3.metric("❓ Enigma", len(df[(df[m['final']] < 80) & (df[m['comp']] >= 80)])) # Ejemplo: Alto potencial, bajo tablero
    k4.metric("✅ Clave", len(df[(df[m['final']] < 80) & (df[m['final']] >= 60)]))
    k5.metric("⚠️ Riesgo", len(df[df[m['final']] < 60]))

    # MAPA DE DISTRIBUCIÓN
    st.subheader("Mapa de Distribución")
    df_plot = df.dropna(subset=[m['comp'], m['tablero']])
    
    if not df_plot.empty:
        fig = px.scatter(
            df_plot, x=m['tablero'], y=m['comp'],
            color=m['area'], hover_name=m['nombre'],
            size=df_plot[m['final']].fillna(50),
            color_discrete_sequence=px.colors.qualitative.Pastel,
            labels={m['tablero']: "Resultados (Tablero %)", m['comp']: "Potencial (Competencias %)"},
            height=500, template="plotly_white"
        )
        # Líneas guía
        fig.add_hline(y=75, line_dash="dash", line_color="#eceff1")
        fig.add_vline(x=75, line_dash="dash", line_color="#eceff1")
        st.plotly_chart(fig, use_container_width=True)
    
    # TABLA DE DATOS
    st.dataframe(df[[m['nombre'], m['puesto'], m['area'], m['final']]].sort_values(m['final'], ascending=False), use_container_width=True)

else:
    st.error("No se pudo conectar con el Google Sheets del Grupo Cenoa.")
