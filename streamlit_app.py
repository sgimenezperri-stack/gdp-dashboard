import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Talento V35.1", layout="wide")

if 'detalle_categoria' not in st.session_state:
    st.session_state.detalle_categoria = None

# --- ESTILOS CSS ---
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
    .analista-box {
        background-color: #f8f9fa;
        border-left: 5px solid #6f42c1;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data_v35_1():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        sheet_name = urllib.parse.quote("DESEMPEÑO")
        csv_url = f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        
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

        # LIMPIEZA CRÍTICA: Asegurar que los nombres sean TEXTO para evitar el error anterior
        df[m['nombre']] = df[m['nombre']].astype(str).str.strip()

        # Limpieza Numérica
        for k in ['comp', 'tablero', 'final']:
            df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        return df, m
    except: return None, None

df_raw, m = load_data_v35_1()

# --- SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.markdown("### GESTIÓN RRHH")
    st.radio("Nav", ["🏠 Desempeño Gral.", "🧠 Competencias", "📑 Tableros"], label_visibility="collapsed")
    st.divider()
    if st.button("💾 Guardar HTML", use_container_width=True):
        st.info("Generando reporte...")

# --- PANEL PRINCIPAL ---
if df_raw is not None:
    st.header("Desempeño General")

    # 1. FILTROS SUPERIORES CON AUTOCOMPLETADO
    c1, c2, c3, c4, c_dot = st.columns([1.5, 1.5, 1.5, 2.5, 1])
    
    with c1: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with c2: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with c3: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    
    # NUEVO FILTRO: Selectbox con búsqueda para Colaborador
    with c4: 
        lista_nombres = ["Todos"] + sorted(df_raw[m['nombre']].unique().tolist())
        f_nom = st.selectbox("COLABORADOR (Escribe para buscar)", options=lista_nombres)
    
    # Lógica de Filtrado
    df = df_raw.copy()
    if f_emp != "Todas": df = df[df[m['empresa']] == f_emp]
    if f_loc != "Todas": df = df[df[m['localidad']] == f_loc]
    if f_are != "Todas": df = df[df[m['area']] == f_are]
    if f_nom != "Todos": df = df[df[m['nombre']] == f_nom]

    # Cuadrante de Dotación
    with c_dot:
        st.markdown(f"""
            <div class="dotacion-card">
                <span style="color: #636e72; font-size: 0.7rem; font-weight: bold;">DOTACIÓN</span><br>
                <span style="color: #2d3436; font-size: 1.6rem; font-weight: bold;">{len(df)}</span>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 2. BOTONES DE CATEGORÍA
    # (Lógica de agrupación de categorías...)
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

    # 3. DETALLE DE CATEGORÍA
    if st.session_state.detalle_categoria:
        cat_actual = st.session_state.detalle_categoria
        df_det = eval(cat_actual.lower() + 's')
        st.markdown(f"### Detalle: {cat_actual} ({len(df_det)})")
        
        if not df_det.empty:
            df_display = df_det[[m['nombre'], m['puesto'], m['empresa'], m['area']]].copy()
            df_display['Valor'] = df_det.apply(lambda r: f"R:{r[m['tablero']]:.0f}% / P:{r[m['comp']]:.0f}%", axis=1)
            st.dataframe(df_display, use_container_width=True) # Dataframe para scroll si hay muchos
            if st.button("Cerrar Detalle"):
                st.session_state.detalle_categoria = None
                st.rerun()
        st.divider()

    # 4. ANALISTA Y MAPA
    st.markdown(f"""
        <div class="analista-box">
            <strong>📝 Analista Virtual</strong><br>
            Promedio General: <b>{df[m['final']].mean():.1f}%</b>.
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Mapa de Distribución")
    fig = px.scatter(df.dropna(subset=[m['comp'], m['tablero']]), 
                     x=m['tablero'], y=m['comp'], color=m['area'],
                     hover_name=m['nombre'], size=df.dropna(subset=[m['comp'], m['tablero']])[m['final']].fillna(50),
                     height=500, template="plotly_white")
    fig.add_hline(y=75, line_dash="dash", line_color="#eceff1")
    fig.add_vline(x=75, line_dash="dash", line_color="#eceff1")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Conexión fallida con Google Sheets.")
