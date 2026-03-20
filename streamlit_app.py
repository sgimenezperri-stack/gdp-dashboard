import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard V37.8 | Grupo Cenoa", layout="wide")

# Estados de navegación
if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS AVANZADO (Sidebar y Componentes) ---
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
    .prom-box-evol { text-align: right; background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
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
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS', 'tablero': '% ACUMULADO TABLERO', 'final': 'DESEMPEÑO'
        }
        df[m['nombre']] = df[m['nombre']].astype(str).str.upper().str.strip()
        for k in ['comp', 'tablero', 'final']:
            df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        def get_sem(v):
            if pd.isna(v): return "Sin Dato"
            return "Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"
        df['Sem_Comp'] = df[m['comp']].apply(get_sem)
        df['Sem_Tab'] = df[m['tablero']].apply(get_sem)
        
        def calc_init(name):
            parts = name.split()
            if len(parts) >= 2: return (parts[0][0] + parts[1][0]).upper()
            return parts[0][0].upper() if parts else ""
        df['Inic'] = df[m['nombre']].apply(calc_init)
        return df, m
    except Exception as e:
        st.error(f"Error crítico: {e}")
        return None, None

df_raw, m = load_all_data()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V37.8")
    st.markdown('<p class="sidebar-title">GESTIÓN RRHH</p>', unsafe_allow_html=True)
    menu = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    st.session_state.pagina = st.radio("Menu", menu, label_visibility="collapsed")

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # Filtros
    cols_f = st.columns([1, 1.2, 1.2, 1.2, 2.5, 0.8])
    with cols_f[0]: f_anio = st.selectbox("AÑO", ["2025", "2026"])
    with cols_f[1]: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with cols_f[2]: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with cols_f[3]: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    with cols_f[4]: f_nom = st.selectbox("COLABORADOR", ["Todos"] + sorted(df_raw[m['nombre']].unique().tolist()))

    df = df_raw.copy()
    if f_emp != "Todas": df = df[df[m['empresa']] == f_emp]
    if f_loc != "Todas": df = df[df[m['localidad']] == f_loc]
    if f_are != "Todas": df = df[df[m['area']] == f_are]
    if f_nom != "Todos": df = df[df[m['nombre']] == f_nom]

    with cols_f[5]:
        st.markdown(f'<div class="dotacion-card"><span style="font-size:0.6rem;font-weight:bold;">DOTACIÓN</span><br><span style="font-size:1.3rem;font-weight:bold;">{len(df)}</span></div>', unsafe_allow_html=True)
    st.divider()

    # --- PÁGINA: EVOLUCIÓN ---
    if "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            c_data = df[df[m['nombre']] == f_nom].iloc[0]
            h1, h2 = st.columns([3, 1])
            with h1:
                st.title(f_nom)
                st.subheader(f"{c_data[m['puesto']]} | {c_data[m['empresa']]}")
            
            # Limpieza segura para NumPy
            meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            valores = []
            for i in range(15, 27): # Columnas P a AA
                try:
                    val_raw = str(c_data.iloc[i]).replace('%', '').replace(',', '.').strip()
                    if val_raw in ['-', 'nan', '', 'None', 'NULL']:
                        valores.append(np.nan) # USAR np.nan es la clave para evitar el TypeError
                    else:
                        valores.append(float(val_raw))
                except:
                    valores.append(np.nan)
            
            # Cálculo de promedio ignorando NaNs
            prom_real = np.nanmean(valores) if not np.all(np.isnan(valores)) else 0
            
            with h2:
                st.markdown(f"""
                    <div class="prom-box-evol">
                        <span style="font-size:2rem; font-weight:bold; color:#27ae60;">{prom_real:.1f}%</span><br>
                        <span style="color:#636e72; font-weight:bold;">PROM. ANUAL</span>
                    </div>
                """, unsafe_allow_html=True)

            fig_e = go.Figure()
            fig_e.add_trace(go.Scatter(x=meses_nombres, y=valores, mode='lines+markers+text',
                line=dict(color='#3498db', width=4), marker=dict(size=12, color='#1e88e5', line=dict(width=2, color='white')),
                text=[f"{v:.0f}%" if not np.isnan(v) else "" for v in valores], textposition="top center"))
            fig_e.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="green", width=2, dash="dash"))
            fig_e.update_layout(height=500, template="plotly_white", yaxis=dict(range=[0, 165], dtick=20, title="Alcance %"))
            st.plotly_chart(fig_e, use_container_width=True)
        else:
            st.info("👈 Selecciona un colaborador para ver su evolución mensual.")

    # --- RESTO DE PANELES ---
    elif "Desempeño Gral." in st.session_state.pagina:
        cats = {"ESTRELLA": df[df[m['final']]>=90], "PROFESIONAL": df[(df[m['final']]>=80)&(df[m['final']]<90)], "CLAVE": df[(df[m['final']]>=70)&(df[m['final']]<80)], "ENIGMA": df[(df[m['final']]>=60)&(df[m['final']]<70)], "RIESGO": df[df[m['final']]<60]}
        cb = st.columns(5)
        for i, (k, v) in enumerate(cats.items()):
            if cb[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k
        if st.session_state.det_sel:
            st.dataframe(cats[st.session_state.det_sel][[m['nombre'], m['puesto'], m['final']]], use_container_width=True)
            if st.button("Cerrar Detalle"): st.session_state.det_sel = None; st.rerun()
        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio: <b>{df[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        df_p = df.dropna(subset=[m['comp'], m['tablero']])
        if not df_p.empty:
            fig = px.scatter(df_p, x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
            fig.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
            st.plotly_chart(fig, use_container_width=True)

    elif st.session_state.pagina in ["🧠 Competencias", "📑 Tableros"]:
        is_comp = "Competencias" in st.session_state.pagina
        col_data = m['comp'] if is_comp else m['tablero']
        sem_col = 'Sem_Comp' if is_comp else 'Sem_Tab'
        cmap = {"Verde (>90%)": "#27ae60", "Amarillo (80-90%)": "#f1c40f", "Rojo (<80%)": "#c0392b", "Sin Dato": "#bdc3c7"}
        st.subheader(f"Dispersión por Empresa")
        df_s = df.dropna(subset=[col_data])
        fig_s = px.strip(df_s, x=m['empresa'], y=col_data, color=sem_col, color_discrete_map=cmap, hover_name=m['nombre'], height=550, template="plotly_white")
        st.plotly_chart(fig_s, use_container_width=True)
