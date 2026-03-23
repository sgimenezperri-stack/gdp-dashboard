import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Desempeño | Grupo Cenoa", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS PREMIUM (DISEÑO CORPORATIVO Y ARMONÍA) ---
st.markdown("""
    <style>
    /* Fondo y Tipografía */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Sidebar Profesional */
    [data-testid="stSidebar"] { background-color: #1e272e !important; min-width: 320px !important; }
    .sidebar-header { padding: 10px; text-align: center; margin-bottom: 5px; border-bottom: 1px solid #34495e; }
    .sidebar-header h1 { color: white; font-size: 0.85rem; font-weight: 700; letter-spacing: 1.5px; line-height: 1.2; margin-top: 15px; }
    .update-text { color: #95a5a6; font-size: 0.7rem; margin-bottom: 15px; text-align: center; }

    /* Botones del Menú Lateral */
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label {
        padding: 12px 20px !important; background-color: #2c3e50 !important;
        border-radius: 10px !important; margin-bottom: 8px !important; transition: 0.3s;
    }
    [data-testid="stRadio"] label p { color: #bdc3c7 !important; font-size: 0.9rem !important; font-weight: 600 !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; box-shadow: 0 4px 10px rgba(52, 152, 219, 0.3); }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: 700 !important; }

    /* Cuadrante de Dotación (KPI Impactante) */
    .kpi-dotacion { 
        background: white; border-radius: 15px; padding: 15px; text-align: center; 
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .kpi-dotacion span { font-size: 0.7rem; font-weight: 700; color: #718096; text-transform: uppercase; }
    .kpi-dotacion h2 { font-size: 4rem !important; margin: 0; color: #2d3748; font-weight: 800; line-height: 1.1; }

    /* KPIs Generales */
    .kpi-card { background: white; border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #edf2f7; }
    .kpi-card h4 { margin: 0; font-size: 1.4rem; color: #2d3748; }
    .kpi-card p { margin: 0; font-size: 0.65rem; font-weight: 700; color: #a0aec0; text-transform: uppercase; }

    /* Botones de Categoría (Armónicos y Compactos) */
    div.stButton > button {
        border-radius: 10px; font-weight: 700; background-color: white; 
        border: 1px solid #e2e8f0; height: 55px !important; font-size: 0.85rem !important;
        transition: all 0.2s;
    }
    div.stButton > button:hover { border-color: #3498db; color: #3498db; background-color: #f0f9ff; }

    /* Botón de Actualizar */
    .stButton>button[kind="secondary"] { background-color: #34495e !important; color: white !important; height: 35px !important; font-size: 0.75rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=600)
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
        
        # Colores Semáforo
        cmap_v = {"Verde (>90%)": "#27ae60", "Amarillo (80-90%)": "#f1c40f", "Rojo (<80%)": "#c0392b", "Sin Dato": "#bdc3c7"}
        def get_sem(v):
            if pd.isna(v): return "Sin Dato"
            return "Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"
        
        df['Sem_Comp'] = df[m['comp']].apply(get_sem)
        df['Sem_Tab'] = df[m['tablero']].apply(get_sem)
        df['Inic'] = df[m['nombre']].apply(lambda x: (x.split()[0][0] + (x.split()[1][0] if len(x.split())>1 else "")).upper() if len(str(x))>3 else "")
        return df, m, datetime.now().strftime("%d/%m/%Y %H:%M"), cmap_v
    except: return None, None, None, None

df_raw, m, last_update, cmap_sem = load_all_data()

# --- 4. SIDEBAR (LOGO BLANCO + TÍTULO + NAV) ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
    # Mostramos el logo BLANCO proporcionado por el usuario
    try:
        st.image("LOGO CENOA BLANCO.png", width=120)
    except:
        st.markdown("🖼️ **[LOGO CENOA]**")
    st.markdown('<h1>GESTIÓN DE DESEMPEÑO<br>GRUPO CENOA</h1></div>', unsafe_allow_html=True)
    
    st.markdown(f'<p class="update-text">🕒 Actualizado: {last_update}</p>', unsafe_allow_html=True)
    if st.button("🔄 ACTUALIZAR DATOS", use_container_width=True, type="secondary"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    menu_items = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución"]
    seleccion = st.radio("Nav", menu_items, index=menu_items.index(st.session_state.pagina) if st.session_state.pagina in menu_items else 0, label_visibility="collapsed")
    if st.session_state.pagina != seleccion:
        st.session_state.pagina = seleccion
        st.session_state.det_sel = None
        st.rerun()

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    # FILTROS Y DOTACIÓN (ARMONÍA VISUAL)
    f_cols = st.columns([1.5, 1.5, 1.5, 2.5, 1.5])
    with f_cols[0]: f_emp = st.selectbox("🏢 Empresa", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with f_cols[1]: f_loc = st.selectbox("📍 Localidad", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with f_cols[2]: f_are = st.selectbox("📂 Área", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    
    df_f = df_raw.copy()
    if f_emp != "Todas": df_f = df_f[df_f[m['empresa']] == f_emp]
    if f_loc != "Todas": df_f = df_f[df_f[m['localidad']] == f_loc]
    if f_are != "Todas": df_f = df_f[df_f[m['area']] == f_are]

    nombres_disp = sorted(df_f[m['nombre']].unique().tolist())
    with f_cols[3]: f_nom = st.selectbox("🔍 Colaborador", ["Todos"] + nombres_disp)
    df_final = df_f if f_nom == "Todos" else df_f[df_f[m['nombre']] == f_nom]
    
    with f_cols[4]:
        # KPI DOTACIÓN GRANDES (Solución Punto 4)
        st.markdown(f'<div class="kpi-dotacion"><span>Dotación</span><h2>{len(df_final)}</h2></div>', unsafe_allow_html=True)
    
    st.divider()

    # --- LÓGICA DE PÁGINAS (CON GRÁFICOS RESTAURADOS) ---
    
    if "Desempeño Gral." in st.session_state.pagina:
        st.subheader("Burbujas de Desempeño (Competencias vs. Tablero)")
        cats = {"ESTRELLA": df_final[df_final[m['final']] >= 90], "PROFESIONAL": df_final[(df_final[m['final']] >= 80) & (df_final[m['final']] < 90)], "CLAVE": df_final[(df_final[m['final']] >= 70) & (df_final[m['final']] < 80)], "ENIGMA": df_final[(df_final[m['final']] >= 60) & (df_final[m['final']] < 70)], "RIESGO": df_final[df_final[m['final']] < 60]}
        c_btns = st.columns(5)
        for i, (k, v) in enumerate(cats.items()):
            if c_btns[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k
        if st.session_state.det_sel in cats:
            st.dataframe(cats[st.session_state.det_sel][[m['nombre'], m['puesto'], m['final']]], use_container_width=True)
            if st.button("✖️ Cerrar Detalle"): st.session_state.det_sel = None; st.rerun()
        
        st.markdown(f'<div class="analista-box"><strong>📊 People Analytics:</strong> El promedio general es de <b>{df_final[m["final"]].mean():.1f}%</b>.</div>', unsafe_allow_html=True)
        
        # RESTAURACIÓN GRÁFICO DE BURBUJAS (Punto 1)
        fig_bub = px.scatter(df_final.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
        fig_bub.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
        st.plotly_chart(fig_bub, use_container_width=True)

    elif st.session_state.pagina in ["🧠 Competencias", "📑 Tableros"]:
        is_comp = "Competencias" in st.session_state.pagina
        col_d = m['comp'] if is_comp else m['tablero']
        sem_d = 'Sem_Comp' if is_comp else 'Sem_Tab'
        evals = df_final[col_d].notna().sum(); no_evals = df_final[col_d].isna().sum()
        
        # Cuadrantes Superiores
        q = st.columns(4)
        q[0].markdown(f'<div class="kpi-card"><p>Total</p><h4>{len(df_final)}</h4></div>', unsafe_allow_html=True)
        q[1].markdown(f'<div class="kpi-card"><p>Evaluados</p><h4 style="color:#3498db;">{evals}</h4></div>', unsafe_allow_html=True)
        q[2].markdown(f'<div class="kpi-card"><p>Sin Dato</p><h4 style="color:#e74c3c;">{no_evals}</h4></div>', unsafe_allow_html=True)
        q[3].markdown(f'<div class="kpi-card"><p>Promedio %</p><h4 style="color:#2ecc71;">{df_final[col_d].mean():.1f}%</h4></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # RESTAURACIÓN DE BOTONES DE CATEGORÍA Y "SIN DATO" ARMÓNICO (Punto 2 y 3)
        cats_sub = {"CRÍTICO": df_final[df_final[col_d] < 70], "ESPERADO": df_final[(df_final[col_d] >= 70) & (df_final[col_d] < 85)], "ALTO": df_final[(df_final[col_d] >= 85) & (df_final[col_d] < 95)], "SOBRESALIENTE": df_final[df_final[col_d] >= 95], "SIN DATO": df_final[df_final[col_d].isna()]}
        
        b_cols = st.columns(5)
        for i, (k, v) in enumerate(cats_sub.items()):
            if b_cols[i].button(f"{k} ({len(v)})"): st.session_state.det_sel = k
        
        if st.session_state.det_sel in cats_sub:
            st.dataframe(cats_sub[st.session_state.det_sel][[m['nombre'], m['empresa'], col_d]], use_container_width=True)
            if st.button("✖️ Cerrar Lista"): st.session_state.det_sel = None; st.rerun()
            
        st.divider()
        st.subheader("Distribución de Resultados por Empresa")
        
        # RESTAURACIÓN GRÁFICO DE FRANJAS (Punto 1)
        fig_strip = px.strip(df_final.dropna(subset=[col_d]), x=m['empresa'], y=col_d, color=sem_d, color_discrete_map=cmap_sem, hover_name=m['nombre'], height=550, template="plotly_white")
        fig_strip.update_layout(showlegend=False)
        st.plotly_chart(fig_strip, use_container_width=True)

    elif "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            c_data = df_final.iloc[0]
            meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            vals = [float(str(c_data.iloc[i]).replace('%','').replace(',','.')) if str(c_data.iloc[i]) not in ['-','nan',''] else np.nan for i in range(15,27)]
            
            e1, e2 = st.columns([3, 1])
            with e1: st.markdown(f"### {f_nom}"); st.caption(f"{c_data[m['puesto']]} | {c_data[m['empresa']]}")
            with e2: st.markdown(f'<div class="kpi-card"><p>Prom. Anual</p><h4 style="color:#2ecc71;">{np.nanmean(vals):.1f}%</h4></div>', unsafe_allow_html=True)
            
            # RESTAURACIÓN GRÁFICO DE EVOLUCIÓN (Punto 1)
            fig_evol = go.Figure(go.Scatter(x=meses, y=vals, mode='lines+markers+text', line=dict(color='#3498db', width=4), text=[f"{v:.0f}%" if not np.isnan(v) else "" for v in vals], textposition="top center"))
            fig_evol.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="#27ae60", width=2, dash="dash"))
            fig_evol.update_layout(height=450, template="plotly_white", yaxis=dict(range=[0, 165], title="Alcance %"))
            st.plotly_chart(fig_evol, use_container_width=True)
        else: st.info("👈 Seleccione un colaborador en el filtro superior.")

else: st.error("Falla crítica al conectar con Google Sheets de Cenoa.")
