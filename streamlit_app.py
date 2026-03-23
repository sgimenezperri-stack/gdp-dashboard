import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Grupo Cenoa V43.3", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS PREMIUM (Sidebar + UX Centrada) ---
st.markdown("""
    <style>
    /* Fondo General y Fuentes */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #263238 !important; min-width: 320px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 12px 20px !important; background-color: transparent !important; border-radius: 10px !important; margin-bottom: 8px !important; transition: all 0.3s ease; position: relative; }
    [data-testid="stRadio"] label p { color: #cfd8dc !important; font-size: 1.05rem !important; font-weight: 500 !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }

    /* Título del Dashboard en Blanco Puro */
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1) { margin-top: 20px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1)::before {
        content: "GESTIÓN RRHH"; position: absolute; top: -35px; left: 10px;
        color: #ffffff !important; /* BLANCO PURO */
        font-size: 0.85rem; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;
    }

    /* --- CUADRANTE DOTACIÓN PERFECTAMENTE CENTRADO --- */
    .kpi-dotacion {
        background: linear-gradient(135deg, #ffffff 0%, #f9fbff 100%);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 2px solid #3498db;
        box-shadow: 0 6px 15px rgba(52, 152, 219, 0.15);
        display: flex;
        flex-direction: column;
        justify-content: center; /* Centrado Vertical */
        align-items: center;    /* Centrado Horizontal */
        min-height: 120px;
    }
    .kpi-dotacion h1 {
        font-size: 3.5rem !important; /* Número Grande */
        font-weight: 900;
        color: #2c3e50;
        margin: 0 !important;
        line-height: 1;
    }
    .kpi-dotacion span {
        font-size: 0.9rem;
        font-weight: 700;
        color: #3498db; /* Texto de etiqueta en azul */
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 5px;
    }

    /* Estilos de KPI Estándar */
    .kpi-card { background-color: #ffffff; border-radius: 15px; padding: 15px; text-align: center; border: 1px solid #e0e0e0; }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    
    /* Botones de Categoría Armónicos */
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; height: 65px; transition: 0.3s; border: 1px solid #dee2e6; }
    div.stButton > button:hover { border-color: #3498db; color: #3498db; background-color: #f0f7ff; }
    
    /* Botón especial para Auditoría (Sin Dato) */
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
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS', 'tablero': '% ACUMULADO TABLERO', 'final': 'DESEMPEÑO'
        }
        df[m['nombre']] = df[m['nombre']].astype(str).str.upper().str.strip()
        for k in ['comp', 'tablero', 'final']:
            df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        df['Sem_Comp'] = df[m['comp']].apply(lambda v: "Sin Dato" if pd.isna(v) else ("Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"))
        df['Sem_Tab'] = df[m['tablero']].apply(lambda v: "Sin Dato" if pd.isna(v) else ("Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"))
        df['Inic'] = df[m['nombre']].apply(lambda x: (str(x).split()[0][0] + (str(x).split()[1][0] if len(str(x).split())>1 else "")).upper() if pd.notna(x) and len(str(x))>3 else "")
        return df, m
    except: return None, None

df_raw, m = load_all_data()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard 2026 | V43.3")
    menu_items = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución"]
    seleccion = st.radio("Nav", menu_items, index=menu_items.index(st.session_state.pagina) if st.session_state.pagina in menu_items else 0, label_visibility="collapsed")
    if st.session_state.pagina != seleccion:
        st.session_state.pagina = seleccion
        st.session_state.det_sel = None
        st.rerun()

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # FILTROS
    cf1, cf2, cf3, cf4, ckpi = st.columns([1.5, 1.5, 1.5, 2.5, 1.3])
    with cf1: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with cf2: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with cf3: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    
    df_f = df_raw.copy()
    if f_emp != "Todas": df_f = df_f[df_f[m['empresa']] == f_emp]
    if f_loc != "Todas": df_f = df_f[df_f[m['localidad']] == f_loc]
    if f_are != "Todas": df_f = df_f[df_f[m['area']] == f_are]

    with cf4: f_nom = st.selectbox("COLABORADOR", ["Todos"] + sorted(df_f[m['nombre']].unique().tolist()))
    df_final = df_f if f_nom == "Todos" else df_f[df_f[m['nombre']] == f_nom]
    
    with ckpi:
        # DOTACIÓN CENTRADA Y ESTÉTICA
        st.markdown(f'<div class="kpi-dotacion"><h1>{len(df_final)}</h1><span>DOTACIÓN</span></div>', unsafe_allow_html=True)
    st.divider()

    # --- PÁGINAS ---
    if "Desempeño Gral." in st.session_state.pagina:
        # Matriz 5 Botones
        cats_g = {"ESTRELLA": df_final[df_final[m['final']] >= 90], "PROFESIONAL": df_final[(df_final[m['final']] >= 80) & (df_final[m['final']] < 90)], "CLAVE": df_final[(df_final[m['final']] >= 70) & (df_final[m['final']] < 80)], "ENIGMA": df_final[(df_final[m['final']] >= 60) & (df_final[m['final']] < 70)], "RIESGO": df_final[df_final[m['final']] < 60]}
        cb = st.columns(5)
        for i, (k, v) in enumerate(cats_g.items()):
            if cb[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k
        if st.session_state.det_sel in cats_g:
            st.dataframe(cats_g[st.session_state.det_sel][[m['nombre'], m['puesto'], m['final']]], use_container_width=True)
            if st.button("✖️ Cerrar Detalle"): st.session_state.det_sel = None; st.rerun()
        
        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio del grupo: <b>{df_final[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        fig = px.scatter(df_final.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
        fig.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
        st.plotly_chart(fig, use_container_width=True)

    elif st.session_state.pagina in ["🧠 Competencias", "📑 Tableros"]:
        is_comp = "Competencias" in st.session_state.pagina
        col_d = m['comp'] if is_comp else m['tablero']
        evals = df_final[col_d].notna().sum(); no_evals = df_final[col_d].isna().sum()
        
        # 4 KPIs Superiores
        q = st.columns(4)
        q[0].markdown(f'<div class="kpi-card"><b>TOTAL</b><br><h3>{len(df_final)}</h3></div>', unsafe_allow_html=True)
        q[1].markdown(f'<div class="kpi-card"><b>CON DATO</b><br><h3 style="color:#3498db;">{evals}</h3></div>', unsafe_allow_html=True)
        q[2].markdown(f'<div class="kpi-card"><b>PENDIENTES</b><br><h3 style="color:#e74c3c;">{no_evals}</h3></div>', unsafe_allow_html=True)
        q[3].markdown(f'<div class="kpi-card"><b>PROMEDIO %</b><br><h3>{df_final[col_d].mean():.1f}%</h3></div>', unsafe_allow_html=True)
        
        st.divider()
        # RESTAURACIÓN DE BOTONES DE RANGO
        cats_r = {"CRÍTICO (<70)": df_final[df_final[col_d] < 70], "ESPERADO (70-85)": df_final[(df_final[col_d] >= 70) & (df_final[col_d] < 85)], "ALTO (85-95)": df_final[(df_final[col_d] >= 85) & (df_final[col_d] < 95)], "SOBRESALIENTE (>95)": df_final[df_final[col_d] >= 95]}
        
        cr = st.columns(5)
        for i, (k, v) in enumerate(cats_r.items()):
            if cr[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k
        with cr[4]:
            st.markdown('<div class="btn-audit">', unsafe_allow_html=True)
            if st.button(f"SIN DATO\n({no_evals})"): st.session_state.det_sel = "SIN_DATO"
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.det_sel == "SIN_DATO":
            st.error("Colaboradores sin información cargada:")
            st.dataframe(df_final[df_final[col_d].isna()][[m['nombre'], m['empresa'], m['area']]], use_container_width=True)
            if st.button("Cerrar Lista"): st.session_state.det_sel = None; st.rerun()
        elif st.session_state.det_sel in cats_r:
            st.success(f"Listado: {st.session_state.det_sel}")
            st.dataframe(cats_r[st.session_state.det_sel][[m['nombre'], m['area'], col_d]], use_container_width=True)
            if st.button("Cerrar Lista"): st.session_state.det_sel = None; st.rerun()

        st.plotly_chart(px.strip(df_final.dropna(subset=[col_d]), x=m['empresa'], y=col_d, color=m['empresa'], hover_name=m['nombre'], height=500, template="plotly_white"), use_container_width=True)

    elif "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            c_data = df_final.iloc[0]
            meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            vals = [float(str(c_data.iloc[i]).replace('%','').replace(',','.')) if str(c_data.iloc[i]) not in ['-','nan',''] else np.nan for i in range(15,27)]
            h1, h2 = st.columns([3, 1])
            with h1: st.title(f_nom); st.subheader(f"{c_data[m['puesto']]} | {c_data[m['empresa']]}")
            with h2: st.markdown(f'<div class="kpi-card"><h2 style="color:#27ae60;">{np.nanmean(vals):.1f}%</h2>PROM. ANUAL</div>', unsafe_allow_html=True)
            fig_e = go.Figure(go.Scatter(x=meses, y=vals, mode='lines+markers+text', line=dict(color='#3498db', width=4), text=[f"{v:.0f}%" if not np.isnan(v) else "" for v in vals], textposition="top center"))
            fig_e.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="green", width=2, dash="dash"))
            st.plotly_chart(fig_e.update_layout(height=500, template="plotly_white", yaxis=dict(range=[0, 165])), use_container_width=True)
        else: st.info("👈 Seleccione un colaborador.")

else: st.error("Error al cargar datos.")
