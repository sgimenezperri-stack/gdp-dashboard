import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Dashboard V36.2 | Grupo Cenoa", layout="wide")

# Estado de navegación
if 'pagina' not in st.session_state:
    st.session_state.pagina = "👤 Desempeño Gral."

# --- 2. ESTILOS CSS (CLONACIÓN DE INTERFAZ) ---
st.markdown("""
    <style>
    /* Estilo del contenedor del Sidebar */
    [data-testid="stSidebar"] {
        background-color: #263238 !important;
        color: white !important;
        min-width: 300px !important;
    }
    
    /* Títulos de secciones (GESTIÓN RRHH / COMERCIAL) */
    .sidebar-header {
        color: #90a4ae;
        font-size: 0.85rem;
        font-weight: bold;
        margin: 25px 0 10px 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Estilo para que el radio button parezca un menú de botones */
    .stRadio > div {
        background-color: transparent !important;
        padding: 0 10px;
    }
    
    /* Estilo de cada opción del menú */
    .stRadio [data-testid="stWidgetLabel"] { display: none; } /* Oculta el label del radio */
    
    .stRadio label {
        background-color: transparent !important;
        color: #cfd8dc !important;
        font-size: 1.1rem !important;
        padding: 12px 20px !important;
        border-radius: 8px !important;
        margin-bottom: 5px !important;
        border: none !important;
        transition: 0.2s;
    }

    /* Color azul cuando está seleccionado (como en tu imagen) */
    .stRadio label[data-selected="true"] {
        background-color: #3498db !important;
        color: white !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }

    /* Estilos de componentes del panel principal */
    .dotacion-card { background-color: #f0f2f6; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #dfe3e8; }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data_v36():
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
            df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        return df, m
    except: return None, None

df_raw, m = load_data_v36()

# --- 4. MARGEN IZQUIERDO (SIDEBAR CALCADO) ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V36.2")
    
    st.markdown('<p class="sidebar-header">GESTIÓN RRHH</p>', unsafe_allow_html=True)
    opciones_menu = [
        "👤 Desempeño Gral.", 
        "🧠 Competencias", 
        "📑 Tableros", 
        "📈 Evolución",
        "📊 Perf. Comercial",
        "🔳 Matriz 9-Box"
    ]
    
    # El radio button ahora actúa como nuestro menú principal
    seleccion = st.radio("Navegación", opciones_menu, label_visibility="collapsed")
    st.session_state.pagina = seleccion

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1]) # Quita el icono del título

    # FILTROS COMUNES
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

    # --- LÓGICA DE PÁGINAS ---
    
    # PÁGINA: DESEMPEÑO GENERAL
    if "Desempeño Gral." in st.session_state.pagina:
        dic_gen = {
            "ESTRELLA": df[df[m['final']] >= 90],
            "PROFESIONAL": df[(df[m['final']] >= 80) & (df[m['final']] < 90)],
            "ENIGMA": df[(df[m['final']] >= 60) & (df[m['final']] < 70)],
            "CLAVE": df[(df[m['final']] >= 70) & (df[m['final']] < 80)],
            "RIESGO": df[df[m['final']] < 60]
        }
        cb = st.columns(5)
        for i, (nom, d_cat) in enumerate(dic_gen.items()):
            with cb[i]:
                if st.button(f"{nom}\n({len(d_cat)})"): st.session_state.det_gen = nom
        
        # Analista y Gráfico
        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio: <b>{df[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        fig_gen = px.scatter(df.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], hover_name=m['nombre'], height=500, template="plotly_white")
        st.plotly_chart(fig_gen, use_container_width=True)

    # PÁGINA: COMPETENCIAS
    elif "Competencias" in st.session_state.pagina:
        # Categorías Competencias (Columna M)
        dic_comp = {
            "CRÍTICO": df[df[m['comp']] < 70],
            "ESPERADO": df[(df[m['comp']] >= 70) & (df[m['comp']] < 85)],
            "ALTO": df[(df[m['comp']] >= 85) & (df[m['comp']] < 95)],
            "SOBRESALIENTE": df[df[m['comp']] >= 95]
        }
        cc = st.columns(4)
        for i, (nom, d_cat) in enumerate(dic_comp.items()):
            with cc[i]:
                st.button(f"{nom}\n{len(d_cat)}")
        
        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio Competencias: <b>{df[m["comp"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        fig_strip = px.strip(df.dropna(subset=[m['comp']]), x=m['area'], y=m['comp'], color=m['area'], hover_name=m['nombre'], height=500, template="plotly_white")
        st.plotly_chart(fig_strip, use_container_width=True)

else:
    st.error("No se pudo conectar con la base de datos.")
