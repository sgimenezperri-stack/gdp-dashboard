import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTADO ---
st.set_page_config(page_title="Dashboard V35.4 | Grupo Cenoa", layout="wide")

if 'detalle_categoria' not in st.session_state:
    st.session_state.detalle_categoria = None

# --- 2. ESTILOS CSS (SIDEBAR OSCURO Y COMPONENTES) ---
st.markdown("""
    <style>
    /* Estilo del Margen Izquierdo (Sidebar) */
    [data-testid="stSidebar"] { background-color: #263238; color: white; }
    [data-testid="stSidebar"] h3 { color: #90a4ae; font-size: 0.8rem; margin-top: 25px; text-transform: uppercase; letter-spacing: 1px; }
    .stRadio > div { background-color: transparent !important; }
    .stRadio label { color: #cfd8dc !important; font-size: 0.9rem !important; padding: 10px !important; }
    
    /* Cuadrante de Dotación */
    .dotacion-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        border: 2px solid #dfe3e8;
    }
    
    /* Analista Virtual */
    .analista-box {
        background-color: #f8f9fa;
        border-left: 5px solid #6f42c1;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    
    /* Botones de Categoría */
    div.stButton > button {
        width: 100%;
        height: 70px;
        border-radius: 10px;
        border: 1px solid #eee;
        background-color: white;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:hover { border-color: #6f42c1; background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS (GOOGLE SHEETS) ---
@st.cache_data(ttl=60)
def load_data_final():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        sheet_name = urllib.parse.quote("DESEMPEÑO")
        csv_url = f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        
        # Mapeo: A=CUIL, B=Nombre (Indice 1)
        m = {
            'nombre': df.columns[1], 
            'empresa': df.columns[2],
            'localidad': df.columns[3],
            'area': df.columns[4],
            'puesto': df.columns[5],
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS',
            'tablero': '% ACUMULADO TABLERO',
            'final': 'DESEMPEÑO'
        }

        # Limpieza de datos
        df[m['nombre']] = df[m['nombre']].astype(str).str.upper()
        for k in ['comp', 'tablero', 'final']:
            if m[k] in df.columns:
                df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        return df, m
    except: return None, None

df_raw, m = load_data_final()

# --- 4. MARGEN IZQUIERDO (SIDEBAR RESTAURADO) ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V35.4 (Multi-Año)")
    
    st.markdown("### GESTIÓN RRHH")
    # Menu con iconos como en tu referencia
    st.radio("Menu_RRHH", ["🏠 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución"], label_visibility="collapsed")
    
    st.markdown("### COMERCIAL")
    st.radio("Menu_Comercial", ["📋 Perf. Comercial", "📍 Matriz 9-Box"], label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("💾 Guardar HTML", use_container_width=True):
        st.success("Reporte generado.")

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header("Desempeño General")

    # Filtros Superiores Horizontales
    c1, c2, c3, c4, c_dot = st.columns([1.5, 1.5, 1.5, 2.5, 1])
    with c1: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with c2: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with c3: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    with c4: f_nom = st.selectbox("COLABORADOR (Busca Apellido)", ["Todos"] + sorted(df_raw[m['nombre']].unique().tolist()))

    # Lógica de Filtrado
    df = df_raw.copy()
    if f_emp != "Todas": df = df[df[m['empresa']] == f_emp]
    if f_loc != "Todas": df = df[df[m['localidad']] == f_loc]
    if f_are != "Todas": df = df[df[m['area']] == f_are]
    if f_nom != "Todos": df = df[df[m['nombre']] == f_nom]

    with c_dot:
        st.markdown(f'<div class="dotacion-card"><span style="font-size:0.7rem;font-weight:bold;color:#636e72;">DOTACIÓN</span><br><span style="font-size:1.6rem;font-weight:bold;color:#2d3436;">{len(df)}</span></div>', unsafe_allow_html=True)

    st.divider()

    # 6. CATEGORÍAS Y BOTONES (Listados Clickables)
    dic_cats = {
        "ESTRELLA": df[ (df[m['tablero']] >= 85) & (df[m['comp']] >= 85) ],
        "PROFESIONAL": df[ (df[m['tablero']] >= 80) & (df[m['comp']] < 70) ],
        "ENIGMA": df[ (df[m['comp']] >= 80) & (df[m['tablero']] < 70) ],
        "CLAVE": df[ (df[m['final']] >= 70) & (df[m['final']] < 85) ],
        "RIESGO": df[ (df[m['final']] < 60) ]
    }

    cols_btn = st.columns(5)
    for i, (nombre, df_cat) in enumerate(dic_cats.items()):
        with cols_btn[i]:
            # Iconos visuales para los botones
            icono = "⭐ " if nombre == "ESTRELLA" else "⚠️ " if nombre == "RIESGO" else "✅ " if nombre == "CLAVE" else "📘 " if nombre == "PROFESIONAL" else "❓ "
            if st.button(f"{icono}{nombre}\n({len(df_cat)})"):
                st.session_state.detalle_categoria = nombre

    # 7. APERTURA DE DETALLE NOMINAL
    if st.session_state.detalle_categoria:
        cat_sel = st.session_state.detalle_categoria
        df_det = dic_cats[cat_sel]
        
        st.markdown(f"### 🔎 Detalle: {cat_sel} ({len(df_det)})")
        if not df_det.empty:
            df_display = df_det[[m['nombre'], m['puesto'], m['empresa'], m['area']]].copy()
            df_display['Valor'] = df_det.apply(lambda r: f"R:{r[m['tablero']]:.0f}% / P:{r[m['comp']]:.0f}%", axis=1)
            st.dataframe(df_display.sort_values(by=m['nombre']), use_container_width=True)
            if st.button("✖️ Cerrar Listado"):
                st.session_state.detalle_categoria = None
                st.rerun()
        else:
            st.info("No hay colaboradores en esta categoría para los filtros aplicados.")
            if st.button("Cerrar"): st.session_state.detalle_categoria = None; st.rerun()
        st.divider()

    # 8. ANALISTA VIRTUAL Y GRÁFICO
    st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> El promedio general es de <b>{df[m["final"]].mean():.1f}%</b> basado en <b>{len(df)}</b> colaboradores.</div>', unsafe_allow_html=True)
    
    st.subheader("Mapa de Distribución")
    df_plot = df.dropna(subset=[m['comp'], m['tablero']])
    if not df_plot.empty:
        fig = px.scatter(df_plot, 
                         x=m['tablero'], y=m['comp'], color=m['area'],
                         hover_name=m['nombre'], size=df_plot[m['final']].fillna(50),
                         height=500, template="plotly_white")
        fig.add_hline(y=75, line_dash="dash", line_color="#eceff1")
        fig.add_vline(x=75, line_dash="dash", line_color="#eceff1")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Error de conexión con la base de datos de Grupo Cenoa.")
