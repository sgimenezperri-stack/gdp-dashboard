import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard V36.1 | Grupo Cenoa", layout="wide")

# Inicialización de estados para navegación y clics
if 'pagina' not in st.session_state: st.session_state.pagina = "🏠 Desempeño General"
if 'det_gen' not in st.session_state: st.session_state.det_gen = None
if 'det_comp' not in st.session_state: st.session_state.det_comp = None

# --- 2. ESTILOS CSS ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238; color: white; min-width: 260px !important; }
    [data-testid="stSidebar"] .stRadio label { color: #cfd8dc !important; font-size: 1rem !important; font-weight: 500; }
    .dotacion-card { background-color: #f0f2f6; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #dfe3e8; }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    
    /* Botones de Categorías */
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; }
    
    /* Colores laterales para Competencias */
    .line-critico { border-left: 8px solid #c0392b !important; }
    .line-esperado { border-left: 8px solid #f1c40f !important; }
    .line-alto { border-left: 8px solid #27ae60 !important; }
    .line-sobre { border-left: 8px solid #2980b9 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data_cenoa():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        sheet_name = urllib.parse.quote("DESEMPEÑO")
        csv_url = f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        
        m = {
            'nombre': df.columns[1], # Col B
            'empresa': df.columns[2],
            'localidad': df.columns[3],
            'area': df.columns[4],
            'puesto': df.columns[5],
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS',
            'tablero': '% ACUMULADO TABLERO',
            'final': 'DESEMPEÑO'
        }

        # Limpieza
        df[m['nombre']] = df[m['nombre']].astype(str).str.upper()
        for k in ['comp', 'tablero', 'final']:
            df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        return df, m
    except: return None, None

df_raw, m = load_data_cenoa()

# --- 4. MARGEN IZQUIERDO (SIDEBAR RESTAURADO CON TÍTULOS) ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V36.1")
    
    st.markdown("### GESTIÓN RRHH")
    # Eliminamos label_visibility="collapsed" para que se vean los títulos
    opciones_rrhh = ["🏠 Desempeño General", "🧠 Competencias", "📑 Tablero", "📈 Evolución"]
    sel_rrhh = st.radio("Secciones RRHH", opciones_rrhh, label_visibility="visible")
    
    st.markdown("### COMERCIAL")
    opciones_com = ["🥇 Ranking", "📋 Performance Comercial", "📍 Matriz 9BOX Comercial"]
    sel_com = st.radio("Secciones Comercial", opciones_com, label_visibility="visible")
    
    # Lógica para sincronizar la página actual
    if st.session_state.pagina != sel_rrhh and sel_rrhh in opciones_rrhh:
        st.session_state.pagina = sel_rrhh
    # Nota: para manejar múltiples radios se requiere lógica de sincronización de estado, 
    # por ahora el dashboard responderá al último radio tocado.

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    # Título y Filtros Comunes
    st.header(st.session_state.pagina)
    
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

    # --- DIMENSIÓN 1: DESEMPEÑO GENERAL (RESTAURADO) ---
    if "Desempeño General" in st.session_state.pagina:
        # Categorías
        dic_gen = {
            "ESTRELLA": df[df[m['final']] >= 90],
            "PROFESIONAL": df[(df[m['final']] >= 80) & (df[m['final']] < 90)],
            "ENIGMA": df[(df[m['final']] >= 60) & (df[m['final']] < 70)],
            "CLAVE": df[(df[m['final']] >= 70) & (df[m['final']] < 80)],
            "RIESGO": df[df[m['final']] < 60]
        }

        # Botones Interactivos
        cb = st.columns(5)
        for i, (nom, d_cat) in enumerate(dic_gen.items()):
            with cb[i]:
                if st.button(f"{nom}\n({len(d_cat)})"): st.session_state.det_gen = nom

        # Detalle
        if st.session_state.det_gen:
            st.subheader(f"Listado: {st.session_state.det_gen}")
            df_d = dic_gen[st.session_state.det_gen]
            df_d['Valor'] = df_d.apply(lambda r: f"R:{r[m['tablero']]:.0f}% / P:{r[m['comp']]:.0f}%", axis=1)
            st.dataframe(df_d[[m['nombre'], m['puesto'], m['area'], 'Valor']], use_container_width=True)
            if st.button("✖️ Cerrar Detalle"): st.session_state.det_gen = None; st.rerun()

        # Analista y Mapa
        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio General: <b>{df[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        fig_gen = px.scatter(df.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], hover_name=m['nombre'], height=500, template="plotly_white")
        st.plotly_chart(fig_gen, use_container_width=True)

    # --- DIMENSIÓN 2: COMPETENCIAS (CON DETALLE ACTIVADO) ---
    elif "Competencias" in st.session_state.pagina:
        # Categorías Competencias
        dic_comp = {
            "CRÍTICO": df[df[m['comp']] < 70],
            "ESPERADO": df[(df[m['comp']] >= 70) & (df[m['comp']] < 85)],
            "ALTO": df[(df[m['comp']] >= 85) & (df[m['comp']] < 95)],
            "SOBRESALIENTE": df[df[m['comp']] >= 95]
        }

        # Botones tipo Tarjeta (Clickables)
        cc = st.columns(4)
        estilos = ["line-critico", "line-esperado", "line-alto", "line-sobre"]
        for i, (nom, d_cat) in enumerate(dic_comp.items()):
            with cc[i]:
                if st.button(f"{nom}\n{len(d_cat)}"): st.session_state.det_comp = nom

        # Detalle Competencias
        if st.session_state.det_comp:
            st.subheader(f"Listado Competencias: {st.session_state.det_comp}")
            df_c = dic_comp[st.session_state.det_comp]
            st.dataframe(df_c[[m['nombre'], m['area'], m['puesto'], m['comp']]], use_container_width=True)
            if st.button("✖️ Cerrar Listado"): st.session_state.det_comp = None; st.rerun()

        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio Competencias: <b>{df[m["comp"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        
        # Mapa Strip Plot
        fig_strip = px.strip(df.dropna(subset=[m['comp']]), x=m['area'], y=m['comp'], color=m['area'], hover_name=m['nombre'], height=500, template="plotly_white")
        st.plotly_chart(fig_strip, use_container_width=True)

else:
    st.error("Error de conexión.")
