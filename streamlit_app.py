import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard V37.1 | Grupo Cenoa", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_gen' not in st.session_state: st.session_state.det_gen = None
if 'det_comp' not in st.session_state: st.session_state.det_comp = None
if 'det_tab' not in st.session_state: st.session_state.det_tab = None

# --- 2. CSS AVANZADO ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238 !important; }
    .sidebar-title { color: #90a4ae !important; font-size: 0.8rem !important; font-weight: bold !important; margin: 20px 0 5px 20px !important; text-transform: uppercase; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 10px 20px !important; background-color: transparent !important; border-radius: 8px !important; margin-bottom: 5px !important; width: 100% !important; }
    [data-testid="stRadio"] label p { color: #eceff1 !important; font-size: 1.05rem !important; font-weight: 500 !important; margin: 0 !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }
    .dotacion-card { background-color: #f0f2f6; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #dfe3e8; }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; height: 70px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data_v37_1():
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
        
        def calc_init(name):
            parts = name.split()
            return (parts[0][0] + (parts[1][0] if len(parts)>1 else "")).upper()
        df['Inic'] = df[m['nombre']].apply(calc_init)
        
        # Función para semáforo
        def get_color_sem(val):
            if pd.isna(val): return "Sin Dato"
            if val >= 90: return "Verde (>90%)"
            if val >= 80: return "Amarillo (80-90%)"
            return "Rojo (<80%)"
        df['Sem_Comp'] = df[m['comp']].apply(get_color_sem)
        df['Sem_Tab'] = df[m['tablero']].apply(get_color_sem)
        
        return df, m
    except: return None, None

df_raw, m = load_data_v37_1()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V37.1")
    st.markdown('<p class="sidebar-title">GESTIÓN RRHH</p>', unsafe_allow_html=True)
    menu = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    st.session_state.pagina = st.radio("Menu", menu, label_visibility="collapsed")

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

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

    # Mapa de Colores Común
    color_map = {"Verde (>90%)": "#27ae60", "Amarillo (80-90%)": "#f1c40f", "Rojo (<80%)": "#c0392b", "Sin Dato": "#bdc3c7"}

    # --- PÁGINA 1: DESEMPEÑO GRAL (MATRIZ INTERACTIVA) ---
    if "Desempeño Gral." in st.session_state.pagina:
        dic_gen = {"ESTRELLA": df[df[m['final']] >= 90], "PROFESIONAL": df[(df[m['final']] >= 80) & (df[m['final']] < 90)], "CLAVE": df[(df[m['final']] >= 70) & (df[m['final']] < 80)], "ENIGMA": df[(df[m['final']] >= 60) & (df[m['final']] < 70)], "RIESGO": df[df[m['final']] < 60]}
        cb = st.columns(5)
        for i, (nom, d_cat) in enumerate(dic_gen.items()):
            if cb[i].button(f"{nom}\n({len(d_cat)})"): st.session_state.det_gen = nom
        if st.session_state.det_gen:
            df_d = dic_gen[st.session_state.det_gen]
            df_d['Valor'] = df_d.apply(lambda r: f"R:{r[m['tablero']]:.0f}% / P:{r[m['comp']]:.0f}%", axis=1)
            st.dataframe(df_d[[m['nombre'], m['puesto'], m['area'], 'Valor']], use_container_width=True)
            if st.button("Cerrar Detalle"): st.session_state.det_gen = None; st.rerun()
        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio: <b>{df[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        df_p = df.dropna(subset=[m['comp'], m['tablero']])
        if not df_p.empty:
            fig = px.scatter(df_p, x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
            fig.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
            st.plotly_chart(fig, use_container_width=True)

    # --- PÁGINA 2: COMPETENCIAS (DISPERSIÓN POR EMPRESA + SEMÁFORO) ---
    elif "Competencias" in st.session_state.pagina:
        dic_comp = {"CRÍTICO": df[df[m['comp']] < 70], "ESPERADO": df[(df[m['comp']] >= 70) & (df[m['comp']] < 85)], "ALTO": df[(df[m['comp']] >= 85) & (df[m['comp']] < 95)], "SOBRESALIENTE": df[df[m['comp']] >= 95]}
        cc = st.columns(4)
        for i, (nom, d_cat) in enumerate(dic_comp.items()):
            if cc[i].button(f"{nom}\n({len(d_cat)})"): st.session_state.det_comp = nom
        if st.session_state.det_comp:
            st.dataframe(dic_comp[st.session_state.det_comp][[m['nombre'], m['empresa'], m['comp']]], use_container_width=True)
            if st.button("Cerrar Detalle Comp."): st.session_state.det_comp = None; st.rerun()
        
        st.subheader("Dispersión de Competencias por Empresa")
        df_c_plot = df.dropna(subset=[m['comp']])
        fig_s = px.strip(df_c_plot, x=m['empresa'], y=m['comp'], color='Sem_Comp', 
                         color_discrete_map=color_map, hover_name=m['nombre'], height=550, template="plotly_white")
        fig_s.update_traces(marker=dict(size=10, opacity=0.7))
        fig_s.update_layout(xaxis_title="Empresa", yaxis_title="Competencias %", showlegend=True)
        st.plotly_chart(fig_s, use_container_width=True)

    # --- PÁGINA 3: TABLEROS (DISPERSIÓN POR EMPRESA + SEMÁFORO) ---
    elif "Tableros" in st.session_state.pagina:
        dic_tab = {"CRÍTICO": df[df[m['tablero']] < 70], "ESPERADO": df[(df[m['tablero']] >= 70) & (df[m['tablero']] < 85)], "ALTO": df[(df[m['tablero']] >= 85) & (df[m['tablero']] < 95)], "SOBRESALIENTE": df[df[m['tablero']] >= 95]}
        ct = st.columns(4)
        for i, (nom, d_cat) in enumerate(dic_tab.items()):
            if ct[i].button(f"{nom}\n({len(d_cat)})"): st.session_state.det_tab = nom
        if st.session_state.det_tab:
            st.dataframe(dic_tab[st.session_state.det_tab][[m['nombre'], m['empresa'], m['tablero']]], use_container_width=True)
            if st.button("Cerrar Detalle Tablero"): st.session_state.det_tab = None; st.rerun()

        st.subheader("Dispersión de Resultados (Tablero) por Empresa")
        df_t_plot = df.dropna(subset=[m['tablero']])
        fig_t = px.strip(df_t_plot, x=m['empresa'], y=m['tablero'], color='Sem_Tab', 
                         color_discrete_map=color_map, hover_name=m['nombre'], height=550, template="plotly_white")
        fig_t.update_traces(marker=dict(size=10, opacity=0.7))
        fig_t.update_layout(xaxis_title="Empresa", yaxis_title="Resultado Tablero %", showlegend=True)
        st.plotly_chart(fig_t, use_container_width=True)

else:
    st.error("Conexión fallida.")
