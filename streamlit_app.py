import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Desempeño | Grupo Cenoa", layout="wide", initial_sidebar_state="expanded")

# Inicialización de estados
if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS AVANZADO (DISEÑO PROFESIONAL) ---
st.markdown("""
    <style>
    /* Fondo General y Fuentes */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Sidebar Profesional */
    [data-testid="stSidebar"] { background-color: #1e272e !important; min-width: 320px !important; }
    
    /* Logo y Título Sidebar */
    .sidebar-header { padding: 20px; text-align: center; border-bottom: 1px solid #34495e; margin-bottom: 20px; }
    .sidebar-header h1 { color: white; font-size: 0.9rem; font-weight: 800; letter-spacing: 2px; margin-top: 10px; }
    .update-text { color: #95a5a6; font-size: 0.7rem; margin-bottom: 15px; }

    /* Ocultar Radio Nativo y Estilar Botones de Menú */
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label {
        padding: 14px 20px !important;
        background-color: #2c3e50 !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
        transition: all 0.3s ease;
        border: 1px solid transparent;
        cursor: pointer;
    }
    [data-testid="stRadio"] label p { color: #bdc3c7 !important; font-size: 0.95rem !important; font-weight: 600 !important; }
    
    /* Botón de Menú Seleccionado */
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] {
        background-color: #3498db !important;
        border: 1px solid #5dade2;
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4);
    }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: 800 !important; }

    /* Estilo de los Filtros (Selectboxes) */
    div[data-baseweb="select"] > div {
        background-color: #f8f9fa !important;
        border-radius: 10px !important;
        border: 1px solid #dee2e6 !important;
    }
    
    /* Cuadrantes KPI */
    .kpi-card { 
        background: white; border-radius: 16px; padding: 20px; text-align: center; 
        border: 1px solid #edf2f7; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
    }
    .kpi-card h3 { margin: 10px 0 0 0; font-size: 1.8rem; color: #2d3748; }
    .kpi-card span { font-size: 0.75rem; font-weight: 700; color: #718096; text-transform: uppercase; }

    /* Botones de Categoría */
    div.stButton > button {
        border-radius: 12px; font-weight: 700; background-color: white; 
        border: 1px solid #e2e8f0; height: 75px; transition: all 0.2s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    div.stButton > button:hover { border-color: #3498db; color: #3498db; transform: translateY(-2px); }
    
    /* Botón Actualizar Sidebar */
    .stButton>button[kind="secondary"] {
        background-color: #34495e !important; color: white !important;
        height: 35px !important; font-size: 0.8rem !important; border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=600) # Se actualiza cada 10 min o manualmente
def load_all_data():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5o (Tú URL Real)"
    # Como ejemplo uso la URL del usuario de los turnos anteriores:
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
        
        df['Inic'] = df[m['nombre']].apply(lambda x: (x.split()[0][0] + (x.split()[1][0] if len(x.split())>1 else "")).upper() if len(x)>3 else "")
        return df, m, datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    except: return None, None, None

df_raw, m, last_update = load_all_data()

# --- 4. MARGEN IZQUIERDO (CABECERA + NAVEGACIÓN) ---
with st.sidebar:
    # Header con Logo y Título
    st.markdown(f"""
        <div class="sidebar-header">
            <img src="https://logodownload.org/wp-content/uploads/2014/10/toyota-logo-2-1.png" width="80" style="filter: brightness(0) invert(1);">
            <h1>GESTIÓN DE DESEMPEÑO<br>GRUPO CENOA</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Info de Actualización y Botón
    st.markdown(f'<p class="update-text" style="text-align:center;">🕒 Última actualización:<br><b>{last_update}</b></p>', unsafe_allow_html=True)
    if st.button("🔄 ACTUALIZAR AHORA", use_container_width=True, type="secondary"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Menú de Navegación
    menu_items = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución"]
    seleccion = st.radio("Nav", menu_items, index=menu_items.index(st.session_state.pagina) if st.session_state.pagina in menu_items else 0, label_visibility="collapsed")
    if st.session_state.pagina != seleccion:
        st.session_state.pagina = seleccion
        st.session_state.det_sel = None
        st.rerun()

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.markdown(f"<h2 style='color:#1a202c;'>{st.session_state.pagina.split(' ', 1)[1]}</h2>", unsafe_allow_html=True)

    # FILTROS ESTILIZADOS
    with st.container():
        cf1, cf2, cf3, cf4, ckpi = st.columns([1.5, 1.5, 1.5, 2.5, 1])
        with cf1: f_emp = st.selectbox("🏢 EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
        with cf2: f_loc = st.selectbox("📍 LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
        with cf3: f_are = st.selectbox("📂 ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
        
        df_f = df_raw.copy()
        if f_emp != "Todas": df_f = df_f[df_f[m['empresa']] == f_emp]
        if f_loc != "Todas": df_f = df_f[df_f[m['localidad']] == f_loc]
        if f_are != "Todas": df_f = df_f[df_f[m['area']] == f_are]

        nombres_disp = sorted(df_f[m['nombre']].unique().tolist())
        with cf4: f_nom = st.selectbox("🔍 COLABORADOR", ["Todos"] + nombres_disp)
        df_final = df_f if f_nom == "Todos" else df_f[df_f[m['nombre']] == f_nom]
        
        with ckpi:
            st.markdown(f'<div class="kpi-card"><span>Dotación</span><h3>{len(df_final)}</h3></div>', unsafe_allow_html=True)
    st.divider()

    # --- PÁGINA: DESEMPEÑO GRAL ---
    if "Desempeño Gral." in st.session_state.pagina:
        cats_g = {"ESTRELLA": df_final[df_final[m['final']] >= 90], "PROFESIONAL": df_final[(df_final[m['final']] >= 80) & (df_final[m['final']] < 90)], "CLAVE": df_final[(df_final[m['final']] >= 70) & (df_final[m['final']] < 80)], "ENIGMA": df_final[(df_final[m['final']] >= 60) & (df_final[m['final']] < 70)], "RIESGO": df_final[df_final[m['final']] < 60]}
        cb = st.columns(5)
        for i, (k, v) in enumerate(cats_g.items()):
            if cb[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k
        if st.session_state.det_sel in cats_g:
            st.dataframe(cats_g[st.session_state.det_sel][[m['nombre'], m['puesto'], m['final']]], use_container_width=True)
            if st.button("✖️ Cerrar Detalle"): st.session_state.det_sel = None; st.rerun()
        
        st.markdown(f'<div class="analista-box"><strong>📊 People Analytics:</strong> El promedio del grupo filtrado es de <b>{df_final[m["final"]].mean():.1f}%</b>.</div>', unsafe_allow_html=True)
        
        fig = px.scatter(df_final.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
        fig.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
        st.plotly_chart(fig, use_container_width=True)

    # --- PÁGINA: COMPETENCIAS / TABLEROS ---
    elif st.session_state.pagina in ["🧠 Competencias", "📑 Tableros"]:
        is_comp = "Competencias" in st.session_state.pagina
        col_d = m['comp'] if is_comp else m['tablero']
        evals = df_final[col_d].notna().sum(); no_evals = df_final[col_d].isna().sum(); prom = df_final[col_d].mean() if evals > 0 else 0
        
        q1, q2, q3, q4 = st.columns(4)
        with q1: st.markdown(f'<div class="kpi-card"><span>Total</span><h3>{len(df_final)}</h3></div>', unsafe_allow_html=True)
        with q2: st.markdown(f'<div class="kpi-card"><span>Evaluados</span><h3 style="color:#3498db;">{evals}</h3></div>', unsafe_allow_html=True)
        with q3:
            st.markdown('<div class="btn-audit">', unsafe_allow_html=True)
            if st.button(f"SIN DATO\n({no_evals})"): st.session_state.det_sel = "AUDIT"
            st.markdown('</div>', unsafe_allow_html=True)
        with q4: st.markdown(f'<div class="kpi-card"><span>Promedio %</span><h3 style="color:#2ecc71;">{prom:.1f}%</h3></div>', unsafe_allow_html=True)
        
        if st.session_state.det_sel == "AUDIT":
            st.dataframe(df_final[df_final[col_d].isna()][[m['nombre'], m['empresa'], m['area'], m['puesto']]], use_container_width=True)
            if st.button("✖️ Cerrar Auditoría"): st.session_state.det_sel = None; st.rerun()
        
        st.divider()
        fig_s = px.strip(df_final.dropna(subset=[col_d]), x=m['empresa'], y=col_d, color=m['empresa'], hover_name=m['nombre'], height=500, template="plotly_white")
        st.plotly_chart(fig_s, use_container_width=True)

    # --- PÁGINA: EVOLUCIÓN ---
    elif "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            c_data = df_final.iloc[0]
            meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            vals = [float(str(c_data.iloc[i]).replace('%','').replace(',','.')) if str(c_data.iloc[i]) not in ['-','nan',''] else np.nan for i in range(15,27)]
            prom_e = np.nanmean(vals) if not np.all(np.isnan(vals)) else 0
            
            e1, e2 = st.columns([3, 1])
            with e1: st.markdown(f"### {f_nom}"); st.caption(f"{c_data[m['puesto']]} | {c_data[m['empresa']]}")
            with e2: st.markdown(f'<div class="kpi-card"><span>Prom. Anual</span><h3 style="color:#2ecc71;">{prom_e:.1f}%</h3></div>', unsafe_allow_html=True)
            
            fig_e = go.Figure(go.Scatter(x=meses, y=vals, mode='lines+markers+text', line=dict(color='#3498db', width=4), text=[f"{v:.0f}%" if not np.isnan(v) else "" for v in vals], textposition="top center"))
            fig_e.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="#27ae60", width=2, dash="dash"))
            fig_e.update_layout(height=500, template="plotly_white", yaxis=dict(range=[0, 165], title="Alcance %"))
            st.plotly_chart(fig_e, use_container_width=True)
        else: st.info("👈 Seleccione un colaborador en el filtro superior.")

else: st.error("Falla en la lectura del Google Sheets. Verifique permisos y nombre de solapas.")
