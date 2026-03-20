import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Talento V35.0", layout="wide")

# Inicializar el estado para el detalle del listado
if 'detalle_categoria' not in st.session_state:
    st.session_state.detalle_categoria = None

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238; }
    .dotacion-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        border: 2px solid #dfe3e8;
    }
    .badge-valor {
        background-color: #3498db;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        display: inline-block;
    }
    /* Estilo para los botones de categoría */
    div.stButton > button {
        height: 80px;
        border-radius: 10px;
        border: 1px solid #ddd;
        background-color: white;
        transition: all 0.3s;
    }
    div.stButton > button:hover { border-color: #6f42c1; background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data_v35():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        sheet_name = urllib.parse.quote("DESEMPEÑO")
        csv_url = f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        
        # Mapeo por posición (Robustez)
        m = {
            'nombre': df.columns[0],
            'empresa': df.columns[2],
            'localidad': df.columns[3],
            'area': df.columns[4],
            'puesto': df.columns[5],
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS',
            'tablero': '% ACUMULADO TABLERO',
            'final': 'DESEMPEÑO'
        }

        # Limpieza Numérica
        for k in ['comp', 'tablero', 'final']:
            df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        return df, m
    except: return None, None

df_raw, m = load_data_v35()

# --- SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.markdown("### GESTIÓN RRHH")
    st.radio("Nav", ["🏠 Desempeño Gral.", "🧠 Competencias", "📑 Tableros"], label_visibility="collapsed")
    st.markdown("### COMERCIAL")
    st.radio("Nav2", ["📋 Perf. Comercial", "📍 Matriz 9-Box"], label_visibility="collapsed")

# --- PANEL PRINCIPAL ---
if df_raw is not None:
    st.header("Desempeño General")

    # 1. FILTROS + DOTACIÓN (Layout Horizontal)
    c1, c2, c3, c4, c_dot = st.columns([1.5, 1.5, 1.5, 2, 1.2])
    
    with c1: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with c2: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with c3: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    with c4: f_nom = st.text_input("COLABORADOR", placeholder="Buscar...")
    
    # Lógica de Filtrado
    df = df_raw.copy()
    if f_emp != "Todas": df = df[df[m['empresa']] == f_emp]
    if f_loc != "Todas": df = df[df[m['localidad']] == f_loc]
    if f_are != "Todas": df = df[df[m['area']] == f_are]
    if f_nom: df = df[df[m['nombre']].str.contains(f_nom, case=False, na=False)]

    # Cuadrante de Dotación (Estético)
    with c_dot:
        st.markdown(f"""
            <div class="dotacion-card">
                <span style="color: #636e72; font-size: 0.8rem; font-weight: bold;">DOTACIÓN</span><br>
                <span style="color: #2d3436; font-size: 1.8rem; font-weight: bold;">{len(df)}</span>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 2. BOTONES DE CATEGORÍA (Clickables para Detalle)
    # Definición de rangos (Ajustables según tu criterio)
    estrellas = df[ (df[m['tablero']] >= 85) & (df[m['comp']] >= 85) ]
    claves = df[ (df[m['final']] >= 70) & (df[m['final']] < 85) ]
    riesgos = df[ (df[m['final']] < 60) ]
    enigmas = df[ (df[m['comp']] >= 80) & (df[m['tablero']] < 70) ]
    profesionales = df[ (df[m['tablero']] >= 80) & (df[m['comp']] < 70) ]

    col_cats = st.columns(5)
    
    def set_cat(nombre): st.session_state.detalle_categoria = nombre

    with col_cats[0]:
        if st.button(f"⭐ ESTRELLA\n({len(estrellas)})"): set_cat("ESTRELLA")
    with col_cats[1]:
        if st.button(f"📘 PROFESIONAL\n({len(profesionales)})"): set_cat("PROFESIONAL")
    with col_cats[2]:
        if st.button(f"❓ ENIGMA\n({len(enigmas)})"): set_cat("ENIGMA")
    with col_cats[3]:
        if st.button(f"✅ CLAVE\n({len(claves)})"): set_cat("CLAVE")
    with col_cats[4]:
        if st.button(f"⚠️ RIESGO\n({len(riesgos)})"): set_cat("RIESGO")

    # 3. APERTURA DE DETALLE (Sólo si se hizo clic)
    if st.session_state.detalle_categoria:
        st.markdown(f"### Detalle: {st.session_state.detalle_categoria} ({len(eval(st.session_state.detalle_categoria.lower() + 's'))})")
        
        # Seleccionar el set de datos según el botón
        df_detalle = eval(st.session_state.detalle_categoria.lower() + 's')
        
        if not df_detalle.empty:
            # Construir visualización de tabla tipo "Apertura"
            # Formateamos los valores para que se vean como R:XX% P:XX%
            df_display = df_detalle[[m['nombre'], m['puesto'], m['empresa'], m['area']]].copy()
            df_display['Valor'] = df_detalle.apply(lambda row: f"R:{row[m['tablero']]:.0f}% / P:{row[m['comp']]:.0f}%", axis=1)
            
            st.table(df_display.head(15)) # Usamos table para que sea estático y limpio como tu imagen
            if st.button("✖️ Cerrar Detalle"):
                st.session_state.detalle_categoria = None
                st.rerun()
        else:
            st.info("No hay colaboradores en esta categoría para los filtros seleccionados.")
        st.divider()

    # 4. RESTO DEL DASHBOARD (Analista y Matriz)
    st.markdown(f"""
        <div class="analista-box">
            <strong>📝 Analista Virtual: Desempeño General</strong><br>
            Promedio General: <b>{df[m['final']].mean():.1f}%</b>. La dotación en {f_loc if f_loc != 'Todas' else 'todas las localidades'} presenta estabilidad.
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Mapa de Distribución")
    fig = px.scatter(df.dropna(subset=[m['comp'], m['tablero']]), 
                     x=m['tablero'], y=m['comp'], color=m['area'],
                     hover_name=m['nombre'], height=500, template="plotly_white")
    fig.add_hline(y=70, line_dash="dash", line_color="#dfe3e8")
    fig.add_vline(x=70, line_dash="dash", line_color="#dfe3e8")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Error cargando Google Sheets.")
