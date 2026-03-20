import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard V38.6 | Grupo Cenoa", layout="wide")

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
    
    .kpi-card { 
        background-color: #ffffff; border-radius: 15px; padding: 15px; text-align: center; 
        border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
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
        
        def get_sem(v):
            if pd.isna(v): return "Sin Dato"
            return "Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"
        df['Sem_Comp'] = df[m['comp']].apply(get_sem)
        df['Sem_Tab'] = df[m['tablero']].apply(get_sem)
        df['Inic'] = df[m['nombre']].apply(lambda x: (x.split()[0][0] + (x.split()[1][0] if len(x.split())>1 else "")).upper() if len(x)>3 else "")
        return df, m
    except: return None, None

df_raw, m = load_all_data()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard 2026")
    st.markdown('<p class="sidebar-title">GESTIÓN RRHH</p>', unsafe_allow_html=True)
    menu = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    st.session_state.pagina = st.radio("Menu", menu, label_visibility="collapsed")

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # FILTROS
    cols_f = st.columns([1.5, 1.5, 1.5, 2.5, 1])
    with cols_f[0]: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with cols_f[1]: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with cols_f[2]: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    
    df_f = df_raw.copy()
    if f_emp != "Todas": df_f = df_f[df_f[m['empresa']] == f_emp]
    if f_loc != "Todas": df_f = df_f[df_f[m['localidad']] == f_loc]
    if f_are != "Todas": df_f = df_f[df_f[m['area']] == f_are]

    with cols_f[3]: f_nom = st.selectbox("COLABORADOR", ["Todos"] + sorted(df_f[m['nombre']].unique().tolist()))
    df_final = df_f if f_nom == "Todos" else df_f[df_f[m['nombre']] == f_nom]
    
    with cols_f[4]:
        st.markdown(f'<div class="kpi-card"><span style="font-size:0.6rem;font-weight:bold;">DOTACIÓN</span><br><span style="font-size:1.3rem;font-weight:bold;">{len(df_final)}</span></div>', unsafe_allow_html=True)
    st.divider()

    # Mapa de Colores Semáforo
    cmap = {"Verde (>90%)": "#27ae60", "Amarillo (80-90%)": "#f1c40f", "Rojo (<80%)": "#c0392b", "Sin Dato": "#bdc3c7"}

    # --- PÁGINA: DESEMPEÑO GRAL ---
    if "Desempeño Gral." in st.session_state.pagina:
        cats = {
            "ESTRELLA": df_final[df_final[m['final']] >= 90],
            "PROFESIONAL": df_final[(df_final[m['final']] >= 80) & (df_final[m['final']] < 90)],
            "CLAVE": df_final[(df_final[m['final']] >= 70) & (df_final[m['final']] < 80)],
            "ENIGMA": df_final[(df_final[m['final']] >= 60) & (df_final[m['final']] < 70)],
            "RIESGO": df_final[df_final[m['final']] < 60]
        }
        c_btns = st.columns(5)
        for i, (k, v) in enumerate(cats.items()):
            if c_btns[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k
        
        if st.session_state.det_sel in cats:
            st.write(f"### Detalle: {st.session_state.det_sel}")
            st.dataframe(cats[st.session_state.det_sel][[m['nombre'], m['puesto'], m['final']]], use_container_width=True)
            if st.button("Cerrar Detalle"): st.session_state.det_sel = None; st.rerun()

        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio: <b>{df_final[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        df_p = df_final.dropna(subset=[m['comp'], m['tablero']])
        if not df_p.empty:
            fig = px.scatter(df_p, x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
            fig.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
            st.plotly_chart(fig, use_container_width=True)

    # --- PÁGINA: COMPETENCIAS ---
    elif "Competencias" in st.session_state.pagina:
        evals = df_final[m['comp']].notna().sum()
        no_evals = df_final[m['comp']].isna().sum()
        prom = df_final[m['comp']].mean() if evals > 0 else 0

        q1, q2, q3, q4 = st.columns(4)
        with q1: st.markdown(f'<div class="kpi-card"><b>TOTAL</b><br><h3>{len(df_final)}</h3></div>', unsafe_allow_html=True)
        with q2: st.markdown(f'<div class="kpi-card"><b>EVALUADOS</b><br><h3 style="color:#3498db;">{evals}</h3></div>', unsafe_allow_html=True)
        with q3: st.markdown(f'<div class="kpi-card"><b>SIN EVALUAR</b><br><h3 style="color:#e74c3c;">{no_evals}</h3></div>', unsafe_allow_html=True)
        with q4: st.markdown(f'<div class="kpi-card"><b>PROMEDIO COMP.</b><br><h3 style="color:#6f42c1;">{prom:.1f}%</h3></div>', unsafe_allow_html=True)
        
        st.divider()
        fig_c = px.strip(df_final.dropna(subset=[m['comp']]), x=m['empresa'], y=m['comp'], color='Sem_Comp', color_discrete_map=cmap, hover_name=m['nombre'], height=500, template="plotly_white")
        st.plotly_chart(fig_c, use_container_width=True)

    # --- PÁGINA: TABLEROS (RESTAURADO) ---
    elif "Tableros" in st.session_state.pagina:
        tienen = df_final[m['tablero']].notna().sum()
        no_tienen = df_final[m['tablero']].isna().sum()
        prom_t = df_final[m['tablero']].mean() if tienen > 0 else 0

        qt1, qt2, qt3, qt4 = st.columns(4)
        with qt1: st.markdown(f'<div class="kpi-card"><b>TOTAL</b><br><h3>{len(df_final)}</h3></div>', unsafe_allow_html=True)
        with qt2: st.markdown(f'<div class="kpi-card"><b>TIENEN TABLERO</b><br><h3 style="color:#3498db;">{tienen}</h3></div>', unsafe_allow_html=True)
        with qt3: st.markdown(f'<div class="kpi-card"><b>SIN TABLERO</b><br><h3 style="color:#e74c3c;">{no_tienen}</h3></div>', unsafe_allow_html=True)
        with qt4: st.markdown(f'<div class="kpi-card"><b>PROMEDIO TABLERO</b><br><h3 style="color:#27ae60;">{prom_t:.1f}%</h3></div>', unsafe_allow_html=True)
        
        st.divider()
        # REINSERCIÓN DEL GRÁFICO DE TABLERO
        df_t = df_final.dropna(subset=[m['tablero']])
        if not df_t.empty:
            fig_t = px.strip(df_t, x=m['empresa'], y=m['tablero'], color='Sem_Tab', color_discrete_map=cmap, hover_name=m['nombre'], height=550, template="plotly_white")
            fig_t.update_traces(marker=dict(size=12, opacity=0.7))
            st.plotly_chart(fig_t, use_container_width=True)
        else:
            st.info("No hay datos de Tablero para mostrar el gráfico con los filtros actuales.")

    # --- PÁGINA: EVOLUCIÓN ---
    elif "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            c_data = df_final.iloc[0]
            meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            vals = [float(str(c_data.iloc[i]).replace('%','').replace(',','.')) if str(c_data.iloc[i]) not in ['-','nan',''] else np.nan for i in range(15,27)]
            prom_e = np.nanmean(vals) if not np.all(np.isnan(vals)) else 0
            h1, h2 = st.columns([3, 1])
            with h1: st.title(f_nom); st.subheader(f"{c_data[m['puesto']]} | {c_data[m['empresa']]}")
            with h2: st.markdown(f'<div class="kpi-card"><span style="color:#27ae60;font-size:2rem;font-weight:bold;">{prom_e:.1f}%</span><br>PROM. ANUAL</div>', unsafe_allow_html=True)
            fig_e = go.Figure(go.Scatter(x=meses, y=vals, mode='lines+markers+text', line=dict(color='#3498db', width=4), text=[f"{v:.0f}%" if not np.isnan(v) else "" for v in vals], textposition="top center"))
            fig_e.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="green", width=2, dash="dash"))
            fig_e.update_layout(height=500, template="plotly_white", yaxis=dict(range=[0, 165], title="Alcance %"))
            st.plotly_chart(fig_e, use_container_width=True)

else:
    st.error("Error al cargar la información.")
