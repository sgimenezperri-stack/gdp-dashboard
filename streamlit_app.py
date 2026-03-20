import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard V37.2 | Grupo Cenoa", layout="wide")

# Inicialización de estados
if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_gen' not in st.session_state: st.session_state.det_gen = None
if 'det_comp' not in st.session_state: st.session_state.det_comp = None
if 'det_tab' not in st.session_state: st.session_state.det_tab = None
if 'colab_evol' not in st.session_state: st.session_state.colab_evol = None

# --- 2. CSS AVANZADO (Sidebar + Estilos Evolución) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238 !important; }
    .sidebar-title { color: #90a4ae !important; font-size: 0.8rem !important; font-weight: bold !important; margin: 20px 0 5px 20px !important; text-transform: uppercase; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 10px 20px !important; background-color: transparent !important; border-radius: 8px !important; margin-bottom: 5px !important; width: 100% !important; }
    [data-testid="stRadio"] label p { color: #eceff1 !important; font-size: 1.05rem !important; font-weight: 500 !important; margin: 0 !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }
    
    /* Contenedores Evolución */
    .list-container { height: 600px; overflow-y: auto; border-right: 1px solid #eee; padding-right: 10px; }
    .colab-card { padding: 10px; border-bottom: 1px solid #f0f0f0; cursor: pointer; border-radius: 5px; margin-bottom: 5px; }
    .colab-card:hover { background-color: #f8f9fa; }
    .colab-selected { background-color: #e3f2fd; border-left: 4px solid #1e88e5; }
    .prom-box { text-align: right; background-color: #ffffff; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data_v37_2():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        # Cargamos las 3 solapas necesarias
        def read_sheet(name):
            p = urllib.parse.quote(name)
            return pd.read_csv(f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={p}")

        df_des = read_sheet("DESEMPEÑO")
        df_2025 = read_sheet("PERFO COMERCIAL 2025")
        df_2026 = read_sheet("PERFO COMERCIAL 2026")
        
        for d in [df_des, df_2025, df_2026]: d.columns = d.columns.str.strip()

        m = {
            'nombre': df_des.columns[1], 'empresa': df_des.columns[2], 'localidad': df_des.columns[3],
            'area': df_des.columns[4], 'puesto': df_des.columns[5],
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS',
            'tablero': '% ACUMULADO TABLERO', 'final': 'DESEMPEÑO'
        }
        
        # Limpieza numérica de scores
        for k in ['comp', 'tablero', 'final']:
            df_des[m[k]] = pd.to_numeric(df_des[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        # Iniciales para el gráfico scatter
        df_des['Inic'] = df_des[m['nombre']].astype(str).apply(lambda x: (x.split()[0][0] + (x.split()[1][0] if len(x.split())>1 else "")).upper())
        
        return df_des, df_2025, df_2026, m
    except: return None, None, None, None

df_raw, df_25, df_26, m = load_data_v37_2()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard V37.2")
    st.markdown('<p class="sidebar-title">GESTIÓN RRHH</p>', unsafe_allow_html=True)
    menu = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    st.session_state.pagina = st.radio("Menu", menu, label_visibility="collapsed")

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # Filtros Comunes (Añadimos AÑO para Evolución)
    cols_f = st.columns([1, 1.2, 1.2, 1.2, 2, 0.8])
    with cols_f[0]: f_anio = st.selectbox("AÑO", ["2025", "2026"])
    with cols_f[1]: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
    with cols_f[2]: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
    with cols_f[3]: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
    with cols_f[4]: f_nom_filtro = st.text_input("BUSCAR COLABORADOR...", placeholder="Escribe nombre...")

    # Aplicar filtros a la base de Evolución
    df_evol_base = df_25 if f_anio == "2025" else df_26
    df_evol_base.columns = df_evol_base.columns.str.strip()
    
    # Filtrado lógico
    df = df_raw.copy()
    if f_emp != "Todas": df = df[df[m['empresa']] == f_emp]
    if f_loc != "Todas": df = df[df[m['localidad']] == f_loc]
    if f_are != "Todas": df = df[df[m['area']] == f_are]
    if f_nom_filtro: df = df[df[m['nombre']].str.contains(f_nom_filtro, case=False, na=False)]

    with cols_f[5]:
        st.markdown(f'<div class="dotacion-card"><span style="font-size:0.6rem;font-weight:bold;">DOTACIÓN</span><br><span style="font-size:1.3rem;font-weight:bold;">{len(df)}</span></div>', unsafe_allow_html=True)
    st.divider()

    # --- PÁGINA: EVOLUCIÓN ---
    if "Evolución" in st.session_state.pagina:
        c_lista, c_grafico = st.columns([1, 3])

        with c_lista:
            st.markdown('<div class="list-container">', unsafe_allow_html=True)
            for _, row in df.iterrows():
                nombre = row[m['nombre']]
                puesto = row[m['puesto']]
                empresa = row[m['empresa']]
                
                # Clase para resaltar seleccionado
                css_class = "colab-card colab-selected" if st.session_state.colab_evol == nombre else "colab-card"
                
                if st.button(f"{nombre}\n{puesto} | {empresa}", key=f"btn_{nombre}", use_container_width=True):
                    st.session_state.colab_evol = nombre
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with c_grafico:
            if st.session_state.colab_evol:
                # Obtener datos del colaborador seleccionado en la hoja de evolución
                colab_data = df_evol_base[df_evol_base.iloc[:, 1].astype(str).str.contains(st.session_state.colab_evol, na=False)]
                
                if not colab_data.empty:
                    # Datos del encabezado
                    info = df[df[m['nombre']] == st.session_state.colab_evol].iloc[0]
                    
                    head_l, head_r = st.columns([3, 1])
                    with head_l:
                        st.title(st.session_state.colab_evol)
                        st.subheader(f"{info[m['puesto']]} | {info[m['empresa']]}")
                    
                    # Extraer meses (Columnas P a AA -> Índices 15 a 26)
                    meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                    valores_meses = []
                    
                    # Limpieza de valores (ignorar "-")
                    for i in range(15, 27):
                        val = str(colab_data.iloc[0, i]).replace('%', '').replace(',', '.')
                        if val == '-' or val == 'nan':
                            valores_meses.append(None)
                        else:
                            try: valores_meses.append(float(val))
                            except: valores_meses.append(None)
                    
                    promedio_val = np.nanmean([v for v in valores_meses if v is not None])
                    
                    with head_r:
                        st.markdown(f"""
                            <div class="prom-box">
                                <span style="font-size:2.2rem; font-weight:bold; color:#27ae60;">{promedio_val:.1f}%</span><br>
                                <span style="color:#636e72;">PROM. ANUAL</span>
                            </div>
                        """, unsafe_allow_html=True)

                    # GRÁFICO DE EVOLUCIÓN
                    fig_evol = go.Figure()
                    
                    # Línea de Datos
                    fig_evol.add_trace(go.Scatter(
                        x=meses_nombres, y=valores_meses,
                        mode='lines+markers+text',
                        name='Alcance',
                        line=dict(color='#3498db', width=4),
                        marker=dict(size=10, color='#1e88e5', line=dict(width=2, color='white')),
                        text=[f"{v:.0f}%" if v is not None else "" for v in valores_meses],
                        textposition="top center"
                    ))

                    # Línea de Meta (100%)
                    fig_evol.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="green", width=2, dash="dash"))
                    
                    fig_evol.update_layout(
                        height=500,
                        template="plotly_white",
                        yaxis=dict(title="Alcance Tablero %", range=[0, 165], tickmode='linear', tick0=0, dtick=20),
                        margin=dict(l=20, r=20, t=20, b=20)
                    )
                    st.plotly_chart(fig_evol, use_container_width=True)
                else:
                    st.warning("No se encontraron registros mensuales para este colaborador en el año seleccionado.")
            else:
                st.info("👈 Selecciona un colaborador del listado para ver su evolución mensual.")

    # --- RESTO DE PÁGINAS (Mantener intactas) ---
    elif "Desempeño Gral." in st.session_state.pagina:
        # (Aquí va el código de la Matriz 9-Box y el Scatter estético que ya tenemos...)
        st.write("Panel de Desempeño General Activo")
        # [Se mantiene el código anterior de esta sección...]
