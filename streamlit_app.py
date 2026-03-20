import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard V36.0 | Grupo Cenoa", layout="wide")

# Estado para navegación y detalles
if 'pagina_actual' not in st.session_state: st.session_state.pagina_actual = "🏠 Desempeño Gral."
if 'detalle_categoria' not in st.session_state: st.session_state.detalle_categoria = None

# --- 2. ESTILOS CSS ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238; color: white; min-width: 250px; }
    [data-testid="stSidebar"] h3 { color: #90a4ae; font-size: 0.8rem; margin-top: 25px; text-transform: uppercase; }
    .dotacion-card { background-color: #f0f2f6; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #dfe3e8; }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    
    /* Estilo de métricas Competencias (Colores de la imagen) */
    .metric-comp { border-radius: 20px; padding: 15px; text-align: center; background: white; border: 1px solid #eee; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .line-critico { border-left: 8px solid #c0392b; }
    .line-esperado { border-left: 8px solid #f1c40f; }
    .line-alto { border-left: 8px solid #27ae60; }
    .line-sobre { border-left: 8px solid #2980b9; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data_cenoa():
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
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS', # Col M
            'tablero': '% ACUMULADO TABLERO',
            'final': 'DESEMPEÑO'
        }

        # Limpieza
        df[m['nombre']] = df[m['nombre']].astype(str).str.upper()
        for k in ['comp', 'tablero', 'final']:
            df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        return df, m
    except: return None, None

df_raw, m = load_data_cenoa()

# --- 4. MARGEN IZQUIERDO (SIDEBAR NAVEGABLE) ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V36.0")
    
    st.markdown("### GESTIÓN RRHH")
    paginas_rrhh = {
        "🏠 Desempeño Gral.": "🏠 Desempeño Gral.",
        "🧠 Competencias": "🧠 Competencias",
        "📑 Tablero": "📑 Tablero",
        "📈 Evolución": "📈 Evolución"
    }
    sel_rrhh = st.radio("RRHH", list(paginas_rrhh.keys()), label_visibility="collapsed")
    
    st.markdown("### COMERCIAL")
    paginas_com = {
        "🥇 Ranking": "🥇 Ranking",
        "📋 Performance": "📋 Performance",
        "📍 Matriz 9BOX": "📍 Matriz 9BOX"
    }
    sel_com = st.radio("COM", list(paginas_com.keys()), label_visibility="collapsed")
    
    # Actualizar página actual
    # (Pequeña lógica para que el último radio seleccionado mande)
    # Por simplicidad en este paso, usaremos el radio de RRHH si cambia.
    st.session_state.pagina_actual = sel_rrhh if sel_rrhh else sel_com

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    # --- FILTROS COMUNES ---
    st.header(st.session_state.pagina_actual.split(" ")[1]) # Título dinámico
    
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
        st.markdown(f'<div class="dotacion-card"><span style="font-size:0.7rem;font-weight:bold;">DOTACIÓN</span><br><span style="font-size:1.5rem;font-weight:bold;">{len(df)}</span></div>', unsafe_allow_html=True)
    st.divider()

    # --- DIMENSIÓN 1: DESEMPEÑO GENERAL ---
    if st.session_state.pagina_actual == "🏠 Desempeño Gral.":
        st.info("Visualizando Panel de Desempeño Unificado (Tablero + Competencias)")
        # (Aquí iría el código que ya terminamos de Desempeño General)
        st.write("Panel consolidado listo.")

    # --- DIMENSIÓN 2: COMPETENCIAS ---
    elif st.session_state.pagina_actual == "🧠 Competencias":
        
        # 1. Analista Virtual específico para Competencias
        prom_comp = df[m['comp']].mean()
        st.markdown(f"""
            <div class="analista-box">
                <strong>📝 Analista Virtual: Evaluación de Competencias</strong><br>
                Desempeño estable (Promedio: <b>{prom_comp:.1f}%</b>).<br>
                <span style="color: #6c757d;">💡 Sugerencia: Reforzar capacitaciones en los sectores con niveles 'Críticos'.</span>
            </div>
        """, unsafe_allow_html=True)

        # 2. Categorización de Competencias (Basado en imagen)
        cat_comp = {
            "Sobresaliente": df[df[m['comp']] >= 95],
            "Alto": df[(df[m['comp']] >= 85) & (df[m['comp']] < 95)],
            "Esperado": df[(df[m['comp']] >= 70) & (df[m['comp']] < 85)],
            "Crítico": df[df[m['comp']] < 70]
        }

        k1, k2, k3, k4 = st.columns(4)
        with k1: st.markdown(f'<div class="metric-comp line-critico"><span style="font-size:1.2rem;font-weight:bold;">{len(cat_comp["Crítico"])}</span><br>Crítico</div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="metric-comp line-esperado"><span style="font-size:1.2rem;font-weight:bold;">{len(cat_comp["Esperado"])}</span><br>Esperado</div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="metric-comp line-alto"><span style="font-size:1.2rem;font-weight:bold;">{len(cat_comp["Alto"])}</span><br>Alto</div>', unsafe_allow_html=True)
        with k4: st.markdown(f'<div class="metric-comp line-sobre"><span style="font-size:1.2rem;font-weight:bold;">{len(cat_comp["Sobresaliente"])}</span><br>Sobresaliente</div>', unsafe_allow_html=True)

        st.subheader("Mapa de Distribución")
        
        # Mapa de Distribución tipo "Strip Plot" como el de la imagen
        # Usamos Jitter para que los puntos no se encimen
        df_comp_plot = df.dropna(subset=[m['comp']])
        
        # Asignar color por categoría para el gráfico
        def color_map(val):
            if val >= 95: return "Sobresaliente"
            if val >= 85: return "Alto"
            if val >= 70: return "Esperado"
            return "Crítico"
        
        df_comp_plot['Cat'] = df_comp_plot[m['comp']].apply(color_map)

        fig_comp = px.strip(
            df_comp_plot, 
            x=m['area'], 
            y=m['comp'], 
            color='Cat',
            hover_name=m['nombre'],
            color_discrete_map={
                "Sobresaliente": "#2980b9",
                "Alto": "#27ae60",
                "Esperado": "#f1c40f",
                "Crítico": "#c0392b"
            },
            labels={m['comp']: "Puntaje Competencias %", m['area']: "Área Operativa"},
            stripmode='overlay'
        )
        fig_comp.update_layout(height=500, template="plotly_white")
        st.plotly_chart(fig_comp, use_container_width=True)

        # Listado inferior para Competencias
        with st.expander("Ver Listado de Evaluación de Competencias"):
            st.dataframe(df_comp_plot[[m['nombre'], m['area'], m['puesto'], m['comp']]].sort_values(m['comp'], ascending=False), use_container_width=True)

else:
    st.error("Error de conexión con Grupo Cenoa.")
