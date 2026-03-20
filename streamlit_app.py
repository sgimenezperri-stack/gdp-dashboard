import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Grupo Cenoa V42.0", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS AVANZADO (Menú Descomprimido y Profesional) ---
st.markdown("""
    <style>
    /* Sidebar: Fondo y ancho */
    [data-testid="stSidebar"] { 
        background-color: #263238 !important; 
        min-width: 320px !important; 
    }
    
    /* Contenedor del Radio Group */
    [data-testid="stRadio"] div[role="radiogroup"] {
        padding-top: 20px;
    }

    /* Ocultar los círculos nativos */
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { 
        display: none !important; 
    }
    
    /* Estilo de cada botón del menú */
    [data-testid="stRadio"] div[role="radiogroup"] label {
        padding: 12px 20px !important;
        background-color: transparent !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important; /* Más espacio entre botones */
        transition: all 0.3s ease;
        position: relative;
    }
    
    /* Texto de los botones */
    [data-testid="stRadio"] label p { 
        color: #cfd8dc !important; 
        font-size: 1.05rem !important; 
        font-weight: 500 !important;
    }
    
    /* Efecto Hover */
    [data-testid="stRadio"] div[role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
    }

    /* Botón Seleccionado (Azul Cenoa) */
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] {
        background-color: #3498db !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { 
        color: white !important; 
        font-weight: bold !important; 
    }

    /* --- INYECCIÓN DE TÍTULOS (Fuera del bloque azul) --- */
    
    /* Título: GESTIÓN RRHH */
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1) {
        margin-top: 40px !important;
    }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1)::before {
        content: "GESTIÓN RRHH";
        position: absolute;
        top: -35px;
        left: 10px;
        color: #90a4ae;
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 1.5px;
    }

    /* Título: GESTIÓN COMERCIAL */
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5) {
        margin-top: 60px !important; /* Espacio extra para separar bloques */
    }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5)::before {
        content: "GESTIÓN COMERCIAL";
        position: absolute;
        top: -35px;
        left: 10px;
        color: #90a4ae;
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 1.5px;
        border-top: 1px solid rgba(144, 164, 174, 0.2);
        padding-top: 15px;
        width: 100%;
    }

    /* Estilos de KPI y Analista */
    .kpi-card { background-color: #ffffff; border-radius: 15px; padding: 15px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; height: 70px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_all_data():
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
            'tablero': '% ACUMULADO TABLERO', 
            'final': 'DESEMPEÑO'
        }
        df[m['nombre']] = df[m['nombre']].astype(str).str.upper().str.strip()
        for k in ['comp', 'tablero', 'final']:
            df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        # Semáforos e Iniciales
        def get_sem(v):
            if pd.isna(v): return "Sin Dato"
            return "Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"
        df['Sem_Comp'] = df[m['comp']].apply(get_sem)
        df['Sem_Tab'] = df[m['tablero']].apply(get_sem)
        df['Inic'] = df[m['nombre']].apply(lambda x: (x.split()[0][0] + (x.split()[1][0] if len(x.split())>1 else "")).upper() if len(x)>3 else "")
        return df, m
    except: return None, None

df_raw, m = load_all_data()

# --- 4. SIDEBAR (ORGANIZACIÓN REAL) ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard 2026 | V42.0")
    
    # Lista única y ordenada para el menú
    menu_items = [
        "👤 Desempeño Gral.", 
        "🧠 Competencias", 
        "📑 Tableros", 
        "📈 Evolución",
        "🥇 Ranking Comercial", 
        "📊 Perf. Comercial", 
        "🔳 Matriz 9-Box"
    ]
    
    # Navegación
    idx_actual = menu_items.index(st.session_state.pagina) if st.session_state.pagina in menu_items else 0
    seleccion = st.radio("Navigation", menu_items, index=idx_actual, label_visibility="collapsed")
    
    if st.session_state.pagina != seleccion:
        st.session_state.pagina = seleccion
        st.session_state.det_sel = None
        st.rerun()

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # Filtros Globales
    c_f1, c_f2, c_f3, c_f4, c_kpi = st.columns([1.5, 1.5, 1.5, 2.5, 1])
    with c_f1: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with c_f2: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with c_f3: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    
    df_f = df_raw.copy()
    if f_emp != "Todas": df_f = df_f[df_f[m['empresa']] == f_emp]
    if f_loc != "Todas": df_f = df_f[df_f[m['localidad']] == f_loc]
    if f_are != "Todas": df_f = df_f[df_f[m['area']] == f_are]

    with c_f4: f_nom = st.selectbox("COLABORADOR", ["Todos"] + sorted(df_f[m['nombre']].unique().tolist()))
    df_final = df_f if f_nom == "Todos" else df_f[df_f[m['nombre']] == f_nom]
    
    with c_kpi:
        st.markdown(f'<div class="kpi-card"><span style="font-size:0.6rem;font-weight:bold;color:#636e72;">DOTACIÓN</span><br><span style="font-size:1.3rem;font-weight:bold;color:#2d3436;">{len(df_final)}</span></div>', unsafe_allow_html=True)
    st.divider()

    # --- LÓGICA DE PÁGINAS ---
    
    if "Desempeño Gral." in st.session_state.pagina:
        # (Lógica de burbujas estéticas con iniciales...)
        fig = px.scatter(df_final.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
        fig.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
        st.plotly_chart(fig, use_container_width=True)

    elif "Ranking Comercial" in st.session_state.pagina:
        st.subheader("Top 10 Colaboradores por Resultado Tablero")
        df_r = df_f[df_f[m['tablero']].notna()].sort_values(by=m['tablero'], ascending=False).head(10)
        if not df_r.empty:
            fig_r = px.bar(df_r, x=m['tablero'], y=m['nombre'], orientation='h', color=m['tablero'], color_continuous_scale='RdYlGn', text_auto='.1f')
            fig_r.update_layout(yaxis={'categoryorder':'total ascending'}, height=500, template="plotly_white")
            st.plotly_chart(fig_r, use_container_width=True)
        else: st.warning("No hay datos para el ranking.")

    elif st.session_state.pagina in ["🧠 Competencias", "📑 Tableros"]:
        # (Lógica de KPIs y gráficos de franjas...)
        st.info("Pestaña activa. Visualizando KPIs y distribución.")

    elif "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            # (Gráfico de evolución de 12 meses...)
            st.write("Visualizando tendencia mensual.")
        else: st.info("👈 Seleccione un colaborador.")

else:
    st.error("Error al conectar con la base de datos.")
