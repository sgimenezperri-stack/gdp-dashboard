import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Talento V35.3", layout="wide")

# Inicializar el estado para el detalle
if 'detalle_categoria' not in st.session_state:
    st.session_state.detalle_categoria = None

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238; }
    .dotacion-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        border: 2px solid #dfe3e8;
    }
    .analista-box {
        background-color: #f8f9fa;
        border-left: 5px solid #6f42c1;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    /* Estilo botones categoría */
    div.stButton > button {
        width: 100%;
        height: 70px;
        border-radius: 10px;
        border: 1px solid #eee;
        background-color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data_v35_3():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        sheet_name = urllib.parse.quote("DESEMPEÑO")
        csv_url = f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        
        m = {
            'nombre': df.columns[1], # Apellido y Nombre
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

df_raw, m = load_data_v35_3()

# --- PANEL PRINCIPAL ---
if df_raw is not None:
    st.header("Desempeño General")

    # 1. FILTROS SUPERIORES
    c1, c2, c3, c4, c_dot = st.columns([1.5, 1.5, 1.5, 2.5, 1])
    with c1: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with c2: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with c3: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    with c4: f_nom = st.selectbox("COLABORADOR", ["Todos"] + sorted(df_raw[m['nombre']].unique().tolist()))

    # Filtrado
    df = df_raw.copy()
    if f_emp != "Todas": df = df[df[m['empresa']] == f_emp]
    if f_loc != "Todas": df = df[df[m['localidad']] == f_loc]
    if f_are != "Todas": df = df[df[m['area']] == f_are]
    if f_nom != "Todos": df = df[df[m['nombre']] == f_nom]

    with c_dot:
        st.markdown(f'<div class="dotacion-card"><span style="font-size:0.7rem;">DOTACIÓN</span><br><span style="font-size:1.5rem;font-weight:bold;">{len(df)}</span></div>', unsafe_allow_html=True)

    st.divider()

    # 2. LÓGICA DE CATEGORÍAS (Sin eval())
    dic_cats = {
        "ESTRELLA": df[ (df[m['tablero']] >= 85) & (df[m['comp']] >= 85) ],
        "PROFESIONAL": df[ (df[m['tablero']] >= 80) & (df[m['comp']] < 70) ],
        "ENIGMA": df[ (df[m['comp']] >= 80) & (df[m['tablero']] < 70) ],
        "CLAVE": df[ (df[m['final']] >= 70) & (df[m['final']] < 85) ],
        "RIESGO": df[ (df[m['final']] < 60) ]
    }

    # 3. BOTONES
    cols_btn = st.columns(5)
    for i, (nombre, df_cat) in enumerate(dic_cats.items()):
        with cols_btn[i]:
            if st.button(f"{nombre}\n({len(df_cat)})"):
                st.session_state.detalle_categoria = nombre

    # 4. APERTURA DE DETALLE
    if st.session_state.detalle_categoria:
        cat_sel = st.session_state.detalle_categoria
        df_det = dic_cats[cat_sel]
        
        st.markdown(f"### 🔎 Detalle: {cat_sel} ({len(df_det)})")
        if not df_det.empty:
            df_display = df_det[[m['nombre'], m['puesto'], m['empresa'], m['area']]].copy()
            df_display['Valor'] = df_det.apply(lambda r: f"R:{r[m['tablero']]:.0f}% / P:{r[m['comp']]:.0f}%", axis=1)
            st.dataframe(df_display, use_container_width=True)
            if st.button("✖️ Cerrar Listado"):
                st.session_state.detalle_categoria = None
                st.rerun()
        else:
            st.info("No hay colaboradores en esta categoría con los filtros actuales.")
            if st.button("✖️ Cerrar"): st.session_state.detalle_categoria = None; st.rerun()
        st.divider()

    # 5. ANALISTA Y MAPA
    st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio del grupo: <b>{df[m['final']].mean():.1f}%</b></div>', unsafe_allow_html=True)
    
    fig = px.scatter(df.dropna(subset=[m['comp'], m['tablero']]), 
                     x=m['tablero'], y=m['comp'], color=m['area'],
                     hover_name=m['nombre'], size=df.dropna(subset=[m['comp'], m['tablero']])[m['final']].fillna(50),
                     height=500, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Error de conexión.")
