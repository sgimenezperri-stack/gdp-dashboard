import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard V36.3 | Grupo Cenoa", layout="wide")

if 'pagina' not in st.session_state:
    st.session_state.pagina = "👤 Desempeño Gral."

# --- 2. CSS AVANZADO PARA SIDEBAR (NOMBRES VISIBLES) ---
st.markdown("""
    <style>
    /* Fondo del Sidebar */
    [data-testid="stSidebar"] {
        background-color: #263238 !important;
    }

    /* Títulos de secciones */
    .sidebar-section-title {
        color: #90a4ae !important;
        font-size: 0.8rem !important;
        font-weight: bold !important;
        margin: 20px 0 10px 20px !important;
        text-transform: uppercase;
    }

    /* OCULTAR CÍRCULOS DEL RADIO */
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* ESTILO DE LAS ETIQUETAS (NOMBRES) */
    [data-testid="stRadio"] div[role="radiogroup"] label {
        padding: 10px 20px !important;
        background-color: transparent !important;
        border-radius: 8px !important;
        margin-bottom: 5px !important;
        width: 100% !important;
    }

    /* FORZAR COLOR DE TEXTO BLANCO */
    [data-testid="stRadio"] label p {
        color: #eceff1 !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }

    /* COLOR AZUL CUANDO ESTÁ SELECCIONADO */
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] {
        background-color: #3498db !important;
        color: white !important;
    }
    
    [data-testid="stRadio"] label[data-baseweb="radio"] p {
        color: white !important;
        font-weight: bold !important;
    }

    /* Analista y Dotación */
    .dotacion-card { background-color: #f0f2f6; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #dfe3e8; }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data_v36_3():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        sheet_name = urllib.parse.quote("DESEMPEÑO")
        csv_url = f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        m = {
            'nombre': df.columns[1], 'empresa': df.columns[2], 'localidad': df.columns[3],
            'area': df.columns[4], 'puesto': df.columns[5],
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS',
            'tablero': '% ACUMULADO TABLERO', 'final': 'DESEMPEÑO'
        }
        df[m['nombre']] = df[m['nombre']].astype(str).str.upper()
        for k in ['comp', 'tablero', 'final']:
            if m[k] in df.columns:
                df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        return df, m
    except: return None, None

df_raw, m = load_data_v36_3()

# --- 4. SIDEBAR CON ETIQUETAS VISIBLES ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V36.3")
    
    st.markdown('<p class="sidebar-section-title">GESTIÓN RRHH</p>', unsafe_allow_html=True)
    menu_opciones = [
        "👤 Desempeño Gral.", 
        "🧠 Competencias", 
        "📑 Tableros", 
        "📈 Evolución",
        "📊 Perf. Comercial",
        "🔳 Matriz 9-Box"
    ]
    
    seleccion = st.radio("Menu", menu_opciones, label_visibility="collapsed")
    st.session_state.pagina = seleccion

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # FILTROS
    c1, c2, c3, c4, c_dot = st.columns([1.5, 1.5, 1.5, 2.5, 1])
    with c1: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with c2: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with c3: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    with c4: f_nom = st.selectbox("COLABORADOR", ["Todos"] + sorted(df_raw[m['nombre']].unique().tolist()))

    df = df_raw.copy()
    if f_emp != "Todas": df = df[df[m['empresa']] == f_emp]
    if f_loc != "Todas": df = df[df[m['localidad']] == f_loc]
    if f_are != "Todas": df = df[df[m['area']] == f_are]
    if f_nom != "Todos": df = df[df[m['nombre']] == f_nom]

    with c_dot:
        st.markdown(f'<div class="dotacion-card"><span style="font-size:0.7rem;font-weight:bold;">DOTACIÓN</span><br><span style="font-size:1.5rem;font-weight:bold;">{len(df)}</span></div>', unsafe_allow_html=True)
    st.divider()

    # --- LÓGICA DE DIMENSIONES ---
    
    # 1. DESEMPEÑO GENERAL
    if "Desempeño Gral." in st.session_state.pagina:
        # Aquí van los 5 botones de Estrella, Profesional, etc. (como en V35.5)
        # Analista Virtual
        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio: <b>{df[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        # Mapa
        fig = px.scatter(df.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], hover_name=m['nombre'], height=500, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    # 2. COMPETENCIAS
    elif "Competencias" in st.session_state.pagina:
        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Análisis de Competencias (Columna M). Promedio: <b>{df[m["comp"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        fig_strip = px.strip(df.dropna(subset=[m['comp']]), x=m['area'], y=m['comp'], color=m['area'], hover_name=m['nombre'], height=500, template="plotly_white")
        st.plotly_chart(fig_strip, use_container_width=True)

else:
    st.error("Conexión fallida.")
