import streamlit as st

import pandas as pd

import plotly.express as px

import plotly.graph_objects as go

import urllib.parse

import numpy as np



# --- 1. CONFIGURACIÓN ---

st.set_page_config(page_title="Dashboard Grupo Cenoa V43.1", layout="wide")



if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."

if 'det_sel' not in st.session_state: st.session_state.det_sel = None



# --- 2. CSS PREMIUM ---

st.markdown("""

    <style>

    [data-testid="stSidebar"] { background-color: #263238 !important; min-width: 320px !important; }

    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }

    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 12px 20px !important; background-color: transparent !important; border-radius: 10px !important; margin-bottom: 8px !important; transition: all 0.3s ease; position: relative; }

    [data-testid="stRadio"] label p { color: #cfd8dc !important; font-size: 1.05rem !important; font-weight: 500 !important; }

    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }

    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }



    /* Inyección de Títulos de Bloque */

    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1) { margin-top: 40px !important; }

    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1)::before {

        content: "GESTIÓN RRHH"; position: absolute; top: -35px; left: 10px;

        color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px;

    }

    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5) { margin-top: 60px !important; }

    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5)::before {

        content: "GESTIÓN COMERCIAL"; position: absolute; top: -35px; left: 10px;

        color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px;

        border-top: 1px solid rgba(144, 164, 174, 0.2); padding-top: 15px; width: 100%;

    }



    /* Estilos de KPI y Botones */

    .kpi-card { background-color: #ffffff; border-radius: 15px; padding: 15px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }

    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }

    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; height: 75px; transition: 0.3s; }

    

    /* Resaltado especial para botones de "Sin Dato" */

    .btn-audit button { border: 1px dashed #e74c3c !important; color: #e74c3c !important; }

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

        # Backup de datos crudos para auditoría

        df['raw_comp'] = df[m['comp']].astype(str).str.strip()

        df['raw_tab'] = df[m['tablero']].astype(str).str.strip()

        

        for k in ['comp', 'tablero', 'final']:

            df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')

        

        df['Sem_Comp'] = df[m['comp']].apply(lambda v: "Sin Dato" if pd.isna(v) else ("Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"))

        df['Sem_Tab'] = df[m['tablero']].apply(lambda v: "Sin Dato" if pd.isna(v) else ("Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"))

        df['Inic'] = df[m['nombre']].apply(lambda x: (x.split()[0][0] + (x.split()[1][0] if len(x.split())>1 else "")).upper() if len(x)>3 else "")

        return df, m

    except: return None, None



df_raw, m = load_all_data()



# --- 4. SIDEBAR ---

with st.sidebar:

    st.title("Grupo Cenoa")

    st.caption("Dashboard 2026 | V43.1")

    menu_items = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "🥇 Ranking Comercial", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]

    seleccion = st.radio("Nav", menu_items, index=menu_items.index(st.session_state.pagina) if st.session_state.pagina in menu_items else 0, label_visibility="collapsed")

    if st.session_state.pagina != seleccion:

        st.session_state.pagina = seleccion

        st.session_state.det_sel = None

        st.rerun()



# --- 5. PANEL PRINCIPAL ---

if df_raw is not None:

    st.header(st.session_state.pagina.split(" ", 1)[1])



    # FILTROS

    cf1, cf2, cf3, cf4, ckpi = st.columns([1.5, 1.5, 1.5, 2.5, 1])

    with cf1: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))

    with cf2: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))

    with cf3: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))

    

    df_f = df_raw.copy()

    if f_emp != "Todas": df_f = df_f[df_f[m['empresa']] == f_emp]

    if f_loc != "Todas": df_f = df_f[df_f[m['localidad']] == f_loc]

    if f_are != "Todas": df_f = df_f[df_f[m['area']] == f_are]



    nombres_disp = sorted(df_f[m['nombre']].unique().tolist())

    with cf4: f_nom = st.selectbox("COLABORADOR", ["Todos"] + nombres_disp)

    df_final = df_f if f_nom == "Todos" else df_f[df_f[m['nombre']] == f_nom]

    

    with ckpi:

        st.markdown(f'<div class="kpi-card"><span style="font-size:0.6rem;font-weight:bold;">DOTACIÓN</span><br><span style="font-size:1.3rem;font-weight:bold;">{len(df_final)}</span></div>', unsafe_allow_html=True)

    st.divider()



    # --- PÁGINA: DESEMPEÑO GRAL ---

    if "Desempeño Gral." in st.session_state.pagina:

        cats_g = {"ESTRELLA": df_final[df_final[m['final']] >= 90], "PROFESIONAL": df_final[(df_final[m['final']] >= 80) & (df_final[m['final']] < 90)], "CLAVE": df_final[(df_final[m['final']] >= 70) & (df_final[m['final']] < 80)], "ENIGMA": df_final[(df_final[m['final']] >= 60) & (df_final[m['final']] < 70)], "RIESGO": df_final[df_final[m['final']] < 60]}

        cb = st.columns(5)

        for i, (k, v) in enumerate(cats_g.items()):

            if cb[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k

        if st.session_state.det_sel in cats_g:

            st.write(f"### Detalle: {st.session_state.det_sel}"); st.dataframe(cats_g[st.session_state.det_sel][[m['nombre'], m['puesto'], m['final']]], use_container_width=True)

            if st.button("✖️ Cerrar Detalle"): st.session_state.det_sel = None; st.rerun()

        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio: <b>{df_final[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)

        fig = px.scatter(df_final.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'],error("No se pudo cargar la solapa PERFO COMERCIAL 2025. Por favor, verifica que el nombre sea exacto en el Google Sheets.")
