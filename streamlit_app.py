import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard V35.5 | Grupo Cenoa", layout="wide")

if 'detalle_categoria' not in st.session_state:
    st.session_state.detalle_categoria = None

# --- 2. ESTILOS CSS ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238; color: white; }
    [data-testid="stSidebar"] h3 { color: #90a4ae; font-size: 0.8rem; margin-top: 25px; text-transform: uppercase; }
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

# --- 3. CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data(ttl=60)
def load_data_v35_5():
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

        df[m['nombre']] = df[m['nombre']].astype(str).str.upper()
        for k in ['comp', 'tablero', 'final']:
            df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        # --- LÓGICA DE CATEGORIZACIÓN SIN HUECOS ---
        # Definimos una función para asignar categoría a CADA fila
        def categorizar(row):
            score = row[m['final']]
            if pd.isna(score): return "SIN DATO"
            if score >= 90: return "ESTRELLA"
            if score >= 80: return "PROFESIONAL"
            if score >= 70: return "CLAVE"
            if score >= 60: return "ENIGMA"
            return "RIESGO"

        df['CATEGORIA_AUTO'] = df.apply(categorizar, axis=1)
        return df, m
    except: return None, None

df_raw, m = load_data_v35_5()

# --- 4. MARGEN IZQUIERDO (SIDEBAR) ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V35.5 (Multi-Año)")
    st.markdown("### GESTIÓN RRHH")
    st.radio("N1", ["🏠 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución"], label_visibility="collapsed")
    st.markdown("### COMERCIAL")
    st.radio("N2", ["📋 Perf. Comercial", "📍 Matriz 9-Box"], label_visibility="collapsed")
    st.divider()
    if st.button("💾 Guardar HTML", use_container_width=True): st.info("Generando...")

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header("Desempeño General")

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
        st.markdown(f'<div class="dotacion-card"><span style="font-size:0.7rem;font-weight:bold;">DOTACIÓN</span><br><span style="font-size:1.6rem;font-weight:bold;">{len(df)}</span></div>', unsafe_allow_html=True)

    st.divider()

    # 6. BOTONES DE CATEGORÍA (Suma exacta a Dotación)
    col_btns = st.columns(5)
    categorias = ["ESTRELLA", "PROFESIONAL", "ENIGMA", "CLAVE", "RIESGO"]
    iconos = ["⭐", "📘", "❓", "✅", "⚠️"]

    for i, cat in enumerate(categorias):
        cant = len(df[df['CATEGORIA_AUTO'] == cat])
        with col_btns[i]:
            if st.button(f"{iconos[i]} {cat}\n({cant})"):
                st.session_state.detalle_categoria = cat

    # 7. APERTURA DE DETALLE
    if st.session_state.detalle_categoria:
        sel = st.session_state.detalle_categoria
        df_det = df[df['CATEGORIA_AUTO'] == sel]
        
        st.markdown(f"### 🔎 Detalle: {sel} ({len(df_det)})")
        if not df_det.empty:
            df_disp = df_det[[m['nombre'], m['puesto'], m['empresa'], m['area']]].copy()
            df_disp['Valor'] = df_det.apply(lambda r: f"R:{r[m['tablero']]:.0f}% / P:{r[m['comp']]:.0f}%", axis=1)
            st.dataframe(df_disp, use_container_width=True)
            if st.button("✖️ Cerrar Listado"):
                st.session_state.detalle_categoria = None
                st.rerun()
        st.divider()

    # 8. ANALISTA Y MAPA
    st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> El promedio es <b>{df[m["final"]].mean():.1f}%</b>.</div>', unsafe_allow_html=True)
    
    st.subheader("Mapa de Distribución")
    df_plot = df.dropna(subset=[m['comp'], m['tablero']])
    if not df_plot.empty:
        fig = px.scatter(df_plot, x=m['tablero'], y=m['comp'], color=m['area'],
                         hover_name=m['nombre'], size=df_plot[m['final']].fillna(50),
                         height=500, template="plotly_white")
        fig.add_hline(y=75, line_dash="dash", line_color="#eee")
        fig.add_vline(x=75, line_dash="dash", line_color="#eee")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Conexión fallida.")
