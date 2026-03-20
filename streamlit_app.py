import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard V36.4 | Grupo Cenoa", layout="wide")

# Inicialización de estados
if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_gen' not in st.session_state: st.session_state.det_gen = None
if 'det_comp' not in st.session_state: st.session_state.det_comp = None

# --- 2. CSS AVANZADO (Look V36.3 + Componentes Interactivos) ---
st.markdown("""
    <style>
    /* 2.1 Sidebar Look & Feel */
    [data-testid="stSidebar"] { background-color: #263238 !important; }
    .sidebar-section-title { color: #90a4ae !important; font-size: 0.8rem !important; font-weight: bold !important; margin: 20px 0 10px 20px !important; text-transform: uppercase; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 10px 20px !important; background-color: transparent !important; border-radius: 8px !important; margin-bottom: 5px !important; width: 100% !important; }
    [data-testid="stRadio"] label p { color: #eceff1 !important; font-size: 1.05rem !important; font-weight: 500 !important; margin: 0 !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; color: white !important; }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }

    /* 2.2 Componentes del Panel */
    .dotacion-card { background-color: #f0f2f6; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #dfe3e8; height: 100%; }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    
    /* Botones Categorías (Interactivas) */
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; height: 75px; transition: 0.3s; }
    div.stButton > button:hover { border-color: #6f42c1; background-color: #f8f9fa; }
    
    /* Colores Competencias */
    .btn-critico { border-left: 8px solid #c0392b !important; }
    .btn-esperado { border-left: 8px solid #f1c40f !important; }
    .btn-alto { border-left: 8px solid #27ae60 !important; }
    .btn-sobre { border-left: 8px solid #2980b9 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data_cenoa_v36_4():
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
        
        # Limpieza Numérica
        for k in ['comp', 'tablero', 'final']:
            if m[k] in df.columns:
                df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        # --- GENERAR INICIALES ---
        def get_initials(name):
            try:
                words = name.split()
                if len(words) >= 2: return (words[0][0] + words[1][0]).upper()
                return words[0][0].upper() if words else ""
            except: return ""
        df['Iniciales'] = df[m['nombre']].apply(get_initials)
        
        return df, m
    except: return None, None

df_raw, m = load_data_cenoa_v36_4()

# --- 4. SIDEBAR RESTAURADO ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V36.4")
    
    st.markdown('<p class="sidebar-section-title">GESTIÓN RRHH</p>', unsafe_allow_html=True)
    opciones_menu = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    seleccion = st.radio("Menu", opciones_menu, label_visibility="collapsed")
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

    # --- LÓGICA DE PÁGINAS ---

    # DIMENSIÓN: DESEMPEÑO GENERAL (Botones e Gráfico Mapeo Talentos)
    if "Desempeño Gral." in st.session_state.pagina:
        # Lógica Categorías Universal (Mamani con 84.7% es Profesional)
        dic_gen = {
            "ESTRELLA (>=90)": df[df[m['final']] >= 90],
            "PROFESIONAL (80-89)": df[(df[m['final']] >= 80) & (df[m['final']] < 90)],
            "CLAVE (70-79)": df[(df[m['final']] >= 70) & (df[m['final']] < 80)],
            "ENIGMA (60-69)": df[(df[m['final']] >= 60) & (df[m['final']] < 70)],
            "RIESGO (<60)": df[df[m['final']] < 60]
        }
        iconos_gen = ["⭐", "📘", "✅", "❓", "⚠️"]

        # Botones Interactivos
        cb = st.columns(5)
        for i, (nom, d_cat) in enumerate(dic_gen.items()):
            nom_btn = nom.split(" ")[0] # Toma el nombre sin el rango
            with cb[i]:
                if st.button(f"{iconos_gen[i]} {nom_btn}\n({len(d_cat)})"): st.session_state.det_gen = nom

        # Apertura de Detalle
        if st.session_state.det_gen:
            st.subheader(f"Listado: {st.session_state.det_gen}")
            df_d = dic_gen[st.session_state.det_gen]
            if not df_d.empty:
                df_d['Valor'] = df_d.apply(lambda r: f"R:{r[m['tablero']]:.0f}% / P:{r[m['comp']]:.0f}%", axis=1)
                st.dataframe(df_d[[m['nombre'], m['puesto'], m['area'], 'Valor']].sort_values(by=m['nombre']), use_container_width=True)
                if st.button("✖️ Cerrar Detalle"): st.session_state.det_gen = None; st.rerun()
            else: st.info("No hay colaboradores."); if st.button("Cerrar"): st.session_state.det_gen = None; st.rerun()
            st.divider()

        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio: <b>{df[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        
        st.subheader("Mapeo Talentos (Burbujas Estéticas con Iniciales)")
        # Preparación de datos para gráfico
        df_gen_plot = df.dropna(subset=[m['comp'], m['tablero']])
        
        if not df_gen_plot.empty:
            # Gráfico Burbujas Estéticas (Mode markers+text)
            fig_gen = px.scatter(
                df_gen_plot, x=m['tablero'], y=m['comp'], 
                color=m['area'], hover_name=m['nombre'], 
                text='Iniciales',
                labels={m['tablero']: "Resultados (Tablero %)", m['comp']: "Potencial (Competencias %)"},
                height=600, template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            # Personalización de Burbujas (Más grandes y estéticas)
            fig_gen.update_traces(
                mode='markers+text',
                marker=dict(size=df_gen_plot[m['final']].fillna(50), 
                            sizemode='area', sizeref=2
