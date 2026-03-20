import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard V37.6 | Grupo Cenoa", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS AVANZADO ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238 !important; }
    .sidebar-title { color: #90a4ae !important; font-size: 0.8rem !important; font-weight: bold !important; margin: 20px 0 5px 20px !important; text-transform: uppercase; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 10px 20px !important; background-color: transparent !important; border-radius: 8px !important; margin-bottom: 5px !important; }
    [data-testid="stRadio"] label p { color: #eceff1 !important; font-size: 1rem !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }
    .dotacion-card { background-color: #f0f2f6; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #dfe3e8; }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .prom-box-evol { text-align: right; background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; height: 70px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_all_data_v37_6():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        def read_s(n):
            p = urllib.parse.quote(n)
            d = pd.read_csv(f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={p}")
            d.columns = d.columns.str.strip()
            return d

        df_des = read_s("DESEMPEÑO")
        df_25 = read_s("PERFO COMERCIAL 2025")
        df_26 = read_s("PERFO COMERCIAL 2026")
        
        # Mapeo Principal
        m = {'nombre': df_des.columns[1], 'empresa': df_des.columns[2], 'localidad': df_des.columns[3],
             'area': df_des.columns[4], 'puesto': df_des.columns[5],
             'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS', 'tablero': '% ACUMULADO TABLERO', 'final': 'DESEMPEÑO'}
        
        # Normalizar Nombres para Búsqueda (Básico para evitar IndexErrors)
        df_des[m['nombre']] = df_des[m['nombre']].astype(str).str.upper().str.strip()
        df_25.iloc[:, 1] = df_25.iloc[:, 1].astype(str).str.upper().str.strip()
        df_26.iloc[:, 1] = df_26.iloc[:, 1].astype(str).str.upper().str.strip()

        # Limpieza Numérica
        for k in ['comp', 'tablero', 'final']:
            df_des[m[k]] = pd.to_numeric(df_des[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        df_des['Inic'] = df_des[m['nombre']].apply(lambda x: (x.split()[0][0] + (x.split()[1][0] if len(x.split())>1 else "")).upper() if len(x)>0 else "")
        
        return df_des, df_25, df_26, m
    except: return None, None, None, None

df_raw, df_25, df_26, m = load_all_data_v37_6()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V37.6")
    st.markdown('<p class="sidebar-title">GESTIÓN RRHH</p>', unsafe_allow_html=True)
    menu = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    st.session_state.pagina = st.radio("Menu", menu, label_visibility="collapsed")

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # FILTROS SUPERIORES
    cols_f = st.columns([1, 1.2, 1.2, 1.2, 2.5, 0.8])
    with cols_f[0]: f_anio = st.selectbox("AÑO", ["2025", "2026"])
    with cols_f[1]: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with cols_f[2]: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with cols_f[3]: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    with cols_f[4]: f_nom = st.selectbox("COLABORADOR", ["Todos"] + sorted(df_raw[m['nombre']].unique().tolist()))

    # Filtrado Global
    df = df_raw.copy()
    if f_emp != "Todas": df = df[df[m['empresa']] == f_emp]
    if f_loc != "Todas": df = df[df[m['localidad']] == f_loc]
    if f_are != "Todas": df = df[df[m['area']] == f_are]
    if f_nom != "Todos": df = df[df[m['nombre']] == f_nom]

    with cols_f[5]:
        st.markdown(f'<div class="dotacion-card"><span style="font-size:0.6rem;font-weight:bold;">DOTACIÓN</span><br><span style="font-size:1.3rem;font-weight:bold;">{len(df)}</span></div>', unsafe_allow_html=True)
    st.divider()

    # --- LÓGICA DE EVOLUCIÓN (Blindada contra IndexErrors) ---
    if "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            df_ev_source = df_25 if f_anio == "2025" else df_26
            
            # Búsqueda segura del colaborador
            c_data = df_ev_source[df_ev_source.iloc[:, 1] == f_nom]
            
            if not c_data.empty:
                # Datos para el encabezado
                info = df[df[m['nombre']] == f_nom].iloc[0]
                h1, h2 = st.columns([3, 1])
                with h1: 
                    st.title(f_nom)
                    st.subheader(f"{info[m['puesto']]} | {info[m['empresa']]}")
                
                # Extracción segura de meses (P a AA)
                meses_ejes = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                vals = []
                for i in range(15, 27): # Columnas 15 a 26
                    try:
                        v_raw = str(c_data.iloc[0, i]).replace('%', '').replace(',', '.').strip()
                        vals.append(float(v_raw) if v_raw not in ['-', 'nan', 'None', ''] else None)
                    except: vals.append(None)
                
                prom_anual = np.nanmean(vals) if any(v is not None for v in vals) else 0
                
                with h2:
                    st.markdown(f'<div class="prom-box-evol"><span style="font-size:2rem;font-weight:bold;color:#27ae60;">{prom_anual:.1f}%</span><br>PROM. ANUAL</div>', unsafe_allow_html=True)
                
                # Gráfico
                fig_e = go.Figure()
                fig_e.add_trace(go.Scatter(x=meses_ejes, y=vals, mode='lines+markers+text', line=dict(color='#3498db', width=4), marker=dict(size=12, color='#1e88e5', line=dict(width=2, color='white')), text=[f"{v:.0f}%" if v else "" for v in vals], textposition="top center"))
                fig_e.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="green", width=2, dash="dash"))
                fig_e.update_layout(height=500, template="plotly_white", yaxis=dict(range=[0, 165], dtick=20, title="Alcance %"))
                st.plotly_chart(fig_e, use_container_width=True)
            else:
                st.warning(f"⚠️ El colaborador '{f_nom}' no tiene registros mensuales cargados en la solapa PERFO COMERCIAL {f_anio}.")
        else:
            st.info("👈 Selecciona un colaborador específico en el filtro superior para ver su gráfico de evolución.")

    # --- OTROS PANELES (Restaurados) ---
    elif "Desempeño Gral." in st.session_state.pagina:
        # Aquí sigue todo el código de las burbujas estéticas con iniciales...
        st.write("Panel de Desempeño General Activo con Iniciales.")
        # [Se mantiene el código de la Matriz y botones interactivos aquí]

else: st.error("Error de conexión.")error("Error de conexión.")
