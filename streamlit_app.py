import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Grupo Cenoa V43.2", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS PREMIUM (Sidebar + UX Mejorada) ---
st.markdown("""
    <style>
    /* Fondo General y Fuentes */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    
    [data-testid="stSidebar"] { background-color: #263238 !important; min-width: 320px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 12px 20px !important; background-color: transparent !important; border-radius: 10px !important; margin-bottom: 8px !important; transition: all 0.3s ease; position: relative; }
    [data-testid="stRadio"] label p { color: #cfd8dc !important; font-size: 1.05rem !important; font-weight: 500 !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }

    /* --- AJUSTE SOLICITADO: Título del Dashboard Legible --- */
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1) { margin-top: 20px !important; } /* Ajuste de margen sin logo */
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1)::before {
        content: "GESTIÓN RRHH"; position: absolute; top: -35px; left: 10px;
        color: #ffffff !important; /* COLOR CAMBIADO A BLANCO PURO PARA MÁXIMA LEGIBILIDAD */
        font-size: 0.85rem; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;
    }

    /* Estilos de KPI Estándar */
    .kpi-card { background-color: #ffffff; border-radius: 15px; padding: 15px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    
    /* --- AJUSTE SOLICITADO: Cuadrante Dotación Estético y Número Gigante --- */
    .kpi-dotacion {
        background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%); /* Fondo degradado estético */
        border-radius: 15px;
        padding: 10px 15px;
        text-align: center;
        border: 2px solid #3498db; /* Borde corporativo grueso */
        box-shadow: 0 6px 15px rgba(52, 152, 219, 0.2); /* Sombra suave azulada */
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        min-height: 110px;
    }
    .kpi-dotacion h1 {
        font-size: 4rem !important; /* NÚMERO GIGANTE: Lo que más se debe ver */
        font-weight: 900;
        color: #3498db; /* Azul Corporativo */
        margin: 0; padding: 0; line-height: 1;
    }
    .kpi-dotacion span {
        font-size: 0.8rem;
        font-weight: 700;
        color: #7f8c8d; /* Gris elegante */
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: -5px;
    }

    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; height: 75px; transition: 0.3s; }
    
    /* Resaltado especial para botones de "Sin Dato" */
    .btn-audit button { border: 1px dashed #e74c3c !important; color: #e74c3c !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS (MANTENIENDO BLINDAJE) ---
@st.cache_data(ttl=60)
def load_all_data():
    # URL de solo lectura para evitar problemas de carga
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
        
        # Limpieza blindada de datos numéricos
        for k in ['comp', 'tablero', 'final']:
            df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        # Generación blindada de semáforos e iniciales
        df['Sem_Comp'] = df[m['comp']].apply(lambda v: "Sin Dato" if pd.isna(v) else ("Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"))
        df['Sem_Tab'] = df[m['tablero']].apply(lambda v: "Sin Dato" if pd.isna(v) else ("Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"))
        df['Inic'] = df[m['nombre']].apply(lambda x: (str(x).split()[0][0] + (str(x).split()[1][0] if len(str(x).split())>1 else "")).upper() if pd.notna(x) and len(str(x))>3 else "")
        return df, m
    except: return None, None

df_raw, m = load_all_data()

# --- 4. SIDEBAR (LOGO ELIMINADO) ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard 2026 | V43.2 (Analytics Focus)")
    menu_items = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución"]
    
    # Navegación blindada
    seleccion = st.radio("Nav", menu_items, index=menu_items.index(st.session_state.pagina) if st.session_state.pagina in menu_items else 0, label_visibility="collapsed")
    if st.session_state.pagina != seleccion:
        st.session_state.pagina = seleccion
        st.session_state.det_sel = None
        st.rerun()

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # FILTROS ESTILIZADOS
    cf1, cf2, cf3, cf4, ckpi = st.columns([1.5, 1.5, 1.5, 2.5, 1.2]) # Ajuste ligero de ancho para KPI dotación
    with cf1: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with cf2: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with cf3: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    
    # Lógica de filtrado blindada
    df_f = df_raw.copy()
    if f_emp != "Todas": df_f = df_f[df_f[m['empresa']] == f_emp]
    if f_loc != "Todas": df_f = df_f[df_f[m['localidad']] == f_loc]
    if f_are != "Todas": df_f = df_f[df_f[m['area']] == f_are]

    nombres_disp = sorted(df_f[m['nombre']].unique().tolist())
    with cf4: f_nom = st.selectbox("COLABORADOR", ["Todos"] + nombres_disp)
    df_final = df_f if f_nom == "Todos" else df_f[df_f[m['nombre']] == f_nom]
    
    # --- AJUSTE SOLICITADO: Renderizado de Dotación Estético y Gigante ---
    with ckpi:
        st.markdown(f'<div class="kpi-dotacion"><h1>{len(df_final)}</h1><span>DOTACIÓN</span></div>', unsafe_allow_html=True)
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
        
        if not df_final.empty:
            st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio del grupo filtrado: <b>{df_final[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        
        # Gráfico blindado contra NaNs
        df_bub = df_final.dropna(subset=[m['comp'], m['tablero']])
        if not df_bub.empty:
            fig = px.scatter(df_bub, x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
            fig.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
            st.plotly_chart(fig, use_container_width=True)
        else: st.warning("No hay datos suficientes de Competencias y Tablero para mostrar la matriz.")

    # --- PÁGINA: COMPETENCIAS ---
    elif "Competencias" in st.session_state.pagina:
        evals = df_final[m['comp']].notna().sum(); no_evals = df_final[m['comp']].isna().sum(); prom_c = df_final[m['comp']].mean() if evals > 0 else 0
        q1, q2, q3, q4 = st.columns(4)
        with q1: st.markdown(f'<div class="kpi-card"><b>TOTAL</b><br><h3>{len(df_final)}</h3></div>', unsafe_allow_html=True)
        with q2: st.markdown(f'<div class="kpi-card"><b>EVALUADOS</b><br><h3 style="color:#3498db;">{evals}</h3></div>', unsafe_allow_html=True)
        with q3:
            st.markdown('<div class="btn-audit">', unsafe_allow_html=True)
            if st.button(f"SIN EVALUAR\n({no_evals})"): st.session_state.det_sel = "AUDIT_COMP"
            st.markdown('</div>', unsafe_allow_html=True)
        with q4: st.markdown(f'<div class="kpi-card"><b>PROMEDIO COMP.</b><br><h3 style="color:#6f42c1;">{prom_c:.1f}%</h3></div>', unsafe_allow_html=True)
        
        if st.session_state.det_sel == "AUDIT_COMP":
            st.error(f"⚠️ Colaboradores sin Evaluación ({no_evals})")
            st.dataframe(df_final[df_final[m['comp']].isna()][[m['nombre'], m['empresa'], m['area'], m['puesto']]], use_container_width=True)
            if st.button("✖️ Cerrar Auditoría"): st.session_state.det_sel = None; st.rerun()
        
        st.divider()
        # Gráfico blindado contra NaNs
        df_strip = df_final.dropna(subset=[m['comp']])
        if not df_strip.empty:
            st.plotly_chart(px.strip(df_strip, x=m['empresa'], y=m['comp'], color='Sem_Comp', color_discrete_map={"Verde (>90%)": "#27ae60", "Amarillo (80-90%)": "#f1c40f", "Rojo (<80%)": "#c0392b"}, hover_name=m['nombre'], height=500, template="plotly_white"), use_container_width=True)

    # --- PÁGINA: TABLEROS ---
    elif "Tableros" in st.session_state.pagina:
        tienen = df_final[m['tablero']].notna().sum(); no_tienen = df_final[m['tablero']].isna().sum(); prom_t = df_final[m['tablero']].mean() if tienen > 0 else 0
        qt1, qt2, qt3, qt4 = st.columns(4)
        with qt1: st.markdown(f'<div class="kpi-card"><b>TOTAL</b><br><h3>{len(df_final)}</h3></div>', unsafe_allow_html=True)
        with qt2: st.markdown(f'<div class="kpi-card"><b>CON TABLERO</b><br><h3 style="color:#3498db;">{tienen}</h3></div>', unsafe_allow_html=True)
        with qt3:
            st.markdown('<div class="btn-audit">', unsafe_allow_html=True)
            if st.button(f"SIN TABLERO\n({no_tienen})"): st.session_state.det_sel = "AUDIT_TAB"
            st.markdown('</div>', unsafe_allow_html=True)
        with qt4: st.markdown(f'<div class="kpi-card"><b>PROMEDIO TABLERO</b><br><h3 style="color:#27ae60;">{prom_t:.1f}%</h3></div>', unsafe_allow_html=True)
        
        if st.session_state.det_sel == "AUDIT_TAB":
            st.error(f"⚠️ Colaboradores sin Tablero ({no_tienen})")
            st.dataframe(df_final[df_final[m['tablero']].isna()][[m['nombre'], m['empresa'], m['area'], m['puesto']]], use_container_width=True)
            if st.button("✖️ Cerrar Auditoría"): st.session_state.det_sel = None; st.rerun()
        
        st.divider()
        # Gráfico blindado contra NaNs
        df_strip_t = df_final.dropna(subset=[m['tablero']])
        if not df_strip_t.empty:
            st.plotly_chart(px.strip(df_strip_t, x=m['empresa'], y=m['tablero'], color='Sem_Tab', color_discrete_map={"Verde (>90%)": "#27ae60", "Amarillo (80-90%)": "#f1c40f", "Rojo (<80%)": "#c0392b"}, hover_name=m['nombre'], height=550, template="plotly_white"), use_container_width=True)

    # --- PÁGINA: EVOLUCIÓN ---
    elif "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            c_data = df_final.iloc[0]
            meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            # Blindaje en la conversión histórica
            try:
                vals = [float(str(c_data.iloc[i]).replace('%','').replace(',','.')) if str(c_data.iloc[i]) not in ['-','nan',''] else np.nan for i in range(15,27)]
                prom_e = np.nanmean(vals) if not np.all(np.isnan(vals)) else 0
                h1, h2 = st.columns([3, 1])
                with h1: st.title(f_nom); st.subheader(f"{c_data[m['puesto']]} | {c_data[m['empresa']]}")
                with h2: st.markdown(f'<div class="kpi-card"><span style="color:#27ae60;font-size:2rem;font-weight:bold;">{prom_e:.1f}%</span><br>PROM. ANUAL</div>', unsafe_allow_html=True)
                fig_e = go.Figure(go.Scatter(x=meses, y=vals, mode='lines+markers+text', line=dict(color='#3498db', width=4), text=[f"{v:.0f}%" if not np.isnan(v) else "" for v in vals], textposition="top center"))
                fig_e.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="green", width=2, dash="dash"))
                fig_e.update_layout(height=500, template="plotly_white", yaxis=dict(range=[0, 165], title="Alcance %"))
                st.plotly_chart(fig_e, use_container_width=True)
            except Exception as e: st.error(f"Error al procesar historial: {e}")
        else: st.info("👈 Seleccione un colaborador en el filtro superior para ver resultados.")

else: st.error("Error al cargar datos de la solapa DESEMPEÑO.")
