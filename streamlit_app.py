import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Desempeño Grupo Cenoa | RRHH", layout="wide")

# Inicialización de estados
if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS PREMIUM (Blindaje de Diseño Corporativo y UI Compacta) ---
st.markdown("""
    <style>
    /* Fondo y Tipografía Global */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }

    /* Sidebar Profesional Oscuro */
    [data-testid="stSidebar"] { background-color: #1a202c !important; min-width: 320px !important; }
    
    /* Cabecera Sidebar Blindada (Logo y Título BLANCOS) */
    .sidebar-header { padding: 10px; text-align: center; margin-bottom: 5px; border-bottom: 1px solid #34495e; }
    /* SOLUCIÓN PUNTO 1: Título Forzado a Blanco */
    .sidebar-header h1 { color: white !important; font-size: 0.85rem; font-weight: 700; letter-spacing: 1.5px; line-height: 1.2; margin-top: 15px; }
    /* Info de Actualización Forzada a Blanco sutil */
    .update-text { color: #bdc3c7 !important; font-size: 0.7rem; margin-bottom: 15px; text-align: center; font-weight: 400; }

    /* Botones del Menú Lateral */
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label {
        padding: 12px 20px !important; background-color: #2c3e50 !important;
        border-radius: 10px !important; margin-bottom: 8px !important; transition: 0.3s;
    }
    [data-testid="stRadio"] label p { color: #dee2e6 !important; font-size: 0.9rem !important; font-weight: 600 !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; box-shadow: 0 4px 10px rgba(52, 152, 219, 0.3); }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: 700 !important; }

    /* --- CUADRANTE DE DOTACIÓN (AJUSTE SOLICITADO: COMPACTO) --- */
    .kpi-dotacion { 
        background: white; border-radius: 12px; padding: 5px 10px; text-align: center; 
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        display: flex; flex-direction: column; justify-content: center;
        height: 90px !important; /* SOLUCIÓN PUNTO 2: Altura reducida y compacta */
        margin-top: 5px;
    }
    /* Letra "Dotación" armoniosa */
    .kpi-dotacion span { font-size: 0.8rem; font-weight: 700; color: #4a5568; text-transform: uppercase; letter-spacing: 1px; margin-bottom: -2px;}
    /* Número grande pero armonioso (reducido de 4.8rem a 3rem) */
    .kpi-dotacion h2 { font-size: 3rem !important; margin: 0; color: #1a202c; font-weight: 800; line-height: 1; }

    /* KPIs Generales */
    .kpi-card { background: white; border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #edf2f7; }
    .kpi-card h4 { margin: 0; font-size: 1.4rem; color: #2d3748; }
    .kpi-card p { margin: 0; font-size: 0.65rem; font-weight: 700; color: #a0aec0; text-transform: uppercase; }

    /* Botones de Categoría (Armónicos) */
    div.stButton > button {
        border-radius: 10px; font-weight: 700; background-color: white; 
        border: 1px solid #e2e8f0; height: 55px !important; font-size: 0.85rem !important;
        transition: all 0.2s;
    }
    div.stButton > button:hover { border-color: #3498db; color: #3498db; background-color: #f0f9ff; }

    /* Filtros profesionales */
    div[data-baseweb="select"] > div { border-radius: 10px !important; background-color: white !important; }
    
    /* Botón de Actualizar sutil en sidebar */
    .stButton>button[kind="secondary"] { background-color: #34495e !important; color: white !important; height: 35px !important; font-size: 0.75rem !important; border: none !important; }
    .stButton>button[kind="secondary"]:hover { background-color: #4e6b8a !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MOTOR DE CARGA DE DATOS (BLINDADO) ---
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
        
        # Colores Semáforo estables
        cmap_v = {"Verde (>90%)": "#27ae60", "Amarillo (80-90%)": "#f1c40f", "Rojo (<80%)": "#c0392b", "Sin Dato": "#bdc3c7"}
        def get_sem(v):
            if pd.isna(v): return "Sin Dato"
            return "Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"
        
        df['Sem_Comp'] = df[m['comp']].apply(get_sem)
        df['Sem_Tab'] = df[m['tablero']].apply(get_sem)
        # Aseguramos que 'Inic' se calcule correctamente
        df['Inic'] = df[m['nombre']].apply(lambda x: (str(x).split()[0][0] + (str(x).split()[1][0] if len(str(x).split())>1 else "")).upper() if pd.notna(x) and len(str(x))>3 else "")
        return df, m, datetime.now().strftime("%d/%m/%Y %H:%M"), cmap_v
    except Exception as e:
        st.error(f"Error crítico de conexión: {e}")
        return None, None, None, None

df_raw, m, last_update, cmap_sem = load_all_data()

# --- 4. SIDEBAR (LOGO BLANCO AJUSTADO + NAVEGACIÓN BLINDADA) ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
    
    # SOLUCIÓN PUNTO 1: Mostrar Logo Cenoa Blanco adjuntado
    try:
        # Asegúrate de que el archivo 'LOGO CENOA BLANCO.png' esté en la misma carpeta que el script
        st.image("LOGO CENOA BLANCO.png", width=120) 
    except:
        st.markdown("🖼️ **[LOGO GRUPO CENOA]**")
    
    # Título blindado en blanco corporativo por CSS
    st.markdown('<h1>GESTIÓN DE DESEMPEÑO<br>GRUPO CENOA</h1></div>', unsafe_allow_html=True)
    
    # Actualización en blanco sutil por CSS
    st.markdown(f'<p class="update-text">🕒 Datos actualizados: {last_update}</p>', unsafe_allow_html=True)
    if st.button("🔄 ACTUALIZAR AHORA", use_container_width=True, type="secondary"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    menu_items = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución"]
    seleccion = st.radio("Nav", menu_items, index=menu_items.index(st.session_state.pagina) if st.session_state.pagina in menu_items else 0, label_visibility="collapsed")
    if st.session_state.pagina != seleccion:
        st.session_state.pagina = seleccion
        st.session_state.det_sel = None
        st.rerun()

# --- 5. PANEL PRINCIPAL (BLINDADO) ---
if df_raw is not None:
    # FILTROS Y DOTACIÓN (ARMONÍA VISUAL CON KPI COMPACTO)
    f_cols = st.columns([1.5, 1.5, 1.5, 2.5, 1.2]) # Mantenemos el ancho 1.2 para dotación
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
        # SOLUCIÓN PUNTO 2: KPI DOTACIÓN COMPACTO (Ajustado via CSS .kpi-dotacion)
        st.markdown(f'<div class="kpi-dotacion"><span>Dotación</span><h2>{len(df_final)}</h2></div>', unsafe_allow_html=True)
    
    st.divider()

    # --- LÓGICA DE PÁGINAS (BLINDADA) ---
    
    # 👤 DESEMPEÑO GRAL
    if "Desempeño Gral." in st.session_state.pagina:
        st.subheader("Burbujas de Desempeño: Competencias vs. Tablero")
        cats = {"ESTRELLA": df_final[df_final[m['final']] >= 90], "PROFESIONAL": df_final[(df_final[m['final']] >= 80) & (df_final[m['final']] < 90)], "CLAVE": df_final[(df_final[m['final']] >= 70) & (df_final[m['final']] < 80)], "ENIGMA": df_final[(df_final[m['final']] >= 60) & (df_final[m['final']] < 70)], "RIESGO": df_final[df_final[m['final']] < 60]}
        c_btns = st.columns(5)
        for i, (k, v) in enumerate(cats.items()):
            if c_btns[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k
        if st.session_state.det_sel in cats:
            st.dataframe(cats[st.session_state.det_sel][[m['nombre'], m['puesto'], m['final']]], use_container_width=True)
            if st.button("✖️ Cerrar Detalle"): st.session_state.det_sel = None; st.rerun()
        
        st.markdown(f'<div class="analista-box"><strong>📊 People Analytics:</strong> El promedio general es de <b>{df_final[m["final"]].mean():.1f}%</b>.</div>', unsafe_allow_html=True)
        
        if not df_final.dropna(subset=[m['comp'], m['tablero']]).empty:
            fig_bub = px.scatter(df_final.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
            fig_bub.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
            st.plotly_chart(fig_bub, use_container_width=True)
        else: st.warning("No hay datos suficientes para graficar las burbujas.")

    # 🧠 COMPETENCIAS / 📑 TABLEROS
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
        
        # Botones de Categoría Armónicos
        cats_sub = {"CRÍTICO": df_final[df_final[col_d] < 70], "ESPERADO": df_final[(df_final[col_d] >= 70) & (df_final[col_d] < 85)], "ALTO": df_final[(df_final[col_d] >= 85) & (df_final[col_d] < 95)], "SOBRESALIENTE": df_final[df_final[col_d] >= 95], "SIN DATO": df_final[df_final[col_d].isna()]}
        
        b_cols = st.columns(5)
        for i, (k, v) in enumerate(cats_sub.items()):
            if b_cols[i].button(f"{k} ({len(v)})"): st.session_state.det_sel = k
        
        if st.session_state.det_sel in cats_sub:
            st.dataframe(cats_sub[st.session_state.det_sel][[m['nombre'], m['empresa'], col_d]], use_container_width=True)
            if st.button("✖️ Cerrar Lista"): st.session_state.det_sel = None; st.rerun()
            
        st.divider()
        st.subheader("Distribución de Resultados por Empresa")
        
        if evals > 0:
            fig_strip = px.strip(df_final.dropna(subset=[col_d]), x=m['empresa'], y=col_d, color=sem_d, color_discrete_map=cmap_sem, hover_name=m['nombre'], height=550, template="plotly_white")
            fig_strip.update_layout(showlegend=False)
            st.plotly_chart(fig_strip, use_container_width=True)
        else: st.warning("No hay datos de resultados para graficar.")

    # 📈 EVOLUCIÓN
    elif "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            c_data = df_final.iloc[0]
            meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            vals = []
            # Aseguramos blindaje en la lectura de columnas de meses (Indices 15 a 26)
            for i in range(15, 27):
                try:
                    vals.append(float(str(c_data.iloc[i]).replace('%','').replace(',','.')))
                except:
                    vals.append(np.nan)
            
            e1, e2 = st.columns([3, 1])
            with e1: st.markdown(f"### {f_nom}"); st.caption(f"{c_data[m['puesto']]} | {c_data[m['empresa']]}")
            
            prom_e = np.nanmean(vals) if not np.all(np.isnan(vals)) else 0
            with e2: st.markdown(f'<div class="kpi-card"><p>Prom. Anual</p><h4 style="color:#2ecc71;">{prom_e:.1f}%</h4></div>', unsafe_allow_html=True)
            
            if evals > 0:
                fig_evol = go.Figure(go.Scatter(x=meses, y=vals, mode='lines+markers+text', line=dict(color='#3498db', width=4), text=[f"{v:.0f}%" if not np.isnan(v) else "" for v in vals], textposition="top center"))
                fig_evol.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="#27ae60", width=2, dash="dash"))
                st.plotly_chart(fig_evol.update_layout(height=450, template="plotly_white", yaxis=dict(range=[0, 165], title="Alcance %")), use_container_width=True)
            else: st.warning("No hay datos históricos para este colaborador.")
        else: st.info("👈 Seleccione un colaborador en el filtro superior.")

else: st.error("Falla crítica al conectar con Google Sheets de Cenoa.")
