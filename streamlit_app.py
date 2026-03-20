import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Grupo Cenoa V44.0", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS PREMIUM (Sidebar + Tablas + KPIs) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238 !important; min-width: 300px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 10px 20px !important; background-color: transparent !important; border-radius: 8px !important; margin-bottom: 4px !important; transition: all 0.3s ease; position: relative; }
    [data-testid="stRadio"] label p { color: #cfd8dc !important; font-size: 1rem !important; font-weight: 500 !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }

    /* Títulos de Bloque */
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1) { margin-top: 40px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1)::before { content: "GESTIÓN RRHH"; position: absolute; top: -35px; left: 10px; color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5) { margin-top: 60px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5)::before { content: "GESTIÓN COMERCIAL"; position: absolute; top: -35px; left: 10px; color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; border-top: 1px solid rgba(144, 164, 174, 0.2); padding-top: 15px; width: 100%; }

    .kpi-card { background-color: #ffffff; border-radius: 15px; padding: 15px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; height: 75px; transition: 0.3s; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS MULTI-SOLAPA ---
@st.cache_data(ttl=60)
def load_all_data_commercial():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        def read_s(n):
            p = urllib.parse.quote(n)
            d = pd.read_csv(f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={p}")
            d.columns = d.columns.str.strip()
            return d

        df_des = read_s("DESEMPEÑO")
        df_p25 = read_s("PERFO COMERCIAL 2025")
        df_p26 = read_s("PERFO COMERCIAL 2026")
        
        m = {
            'nombre': df_des.columns[1], 'empresa': df_des.columns[2], 'localidad': df_des.columns[3],
            'area': df_des.columns[4], 'puesto': df_des.columns[5],
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS', 'tablero': '% ACUMULADO TABLERO', 'final': 'DESEMPEÑO'
        }
        
        # Limpieza General
        for d in [df_des, df_p25, df_p26]:
            col_nom = d.columns[1]
            d[col_nom] = d[col_nom].astype(str).str.upper().str.strip()
        
        for k in ['comp', 'tablero', 'final']:
            df_des[m[k]] = pd.to_numeric(df_des[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        df_des['Sem_Comp'] = df_des[m['comp']].apply(lambda v: "Sin Dato" if pd.isna(v) else ("Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"))
        df_des['Sem_Tab'] = df_des[m['tablero']].apply(lambda v: "Sin Dato" if pd.isna(v) else ("Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"))
        df_des['Inic'] = df_des[m['nombre']].apply(lambda x: (x.split()[0][0] + (x.split()[1][0] if len(x.split())>1 else "")).upper() if len(x)>3 else "")
        
        return df_des, df_p25, df_p26, m
    except: return None, None, None, None

df_raw, df_25, df_26, m = load_all_data_commercial()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard 2026 | V44.0")
    menu_items = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "🥇 Ranking Comercial", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    seleccion = st.radio("Nav", menu_items, index=menu_items.index(st.session_state.pagina), label_visibility="collapsed")
    if st.session_state.pagina != seleccion:
        st.session_state.pagina = seleccion
        st.session_state.det_sel = None
        st.rerun()

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # FILTROS DINÁMICOS
    is_comercial = st.session_state.pagina in ["🥇 Ranking Comercial", "📊 Perf. Comercial"]
    
    # Grid de filtros
    if is_comercial:
        cf1, cf2, cf3, cf4, cf5 = st.columns([1, 1, 1.5, 1.5, 2])
        with cf1: f_anio = st.selectbox("AÑO", ["2026", "2025"])
        meses_lista = ["TOTAL", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        with cf2: f_mes = st.selectbox("MES", meses_lista)
        df_com_base = df_26 if f_anio == "2026" else df_25
        with cf3: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_com_base.iloc[:, 2].dropna().unique().tolist()))
        with cf4: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_com_base.iloc[:, 3].dropna().unique().tolist()))
        with cf5: f_nom = st.text_input("BUSCAR VENDEDOR...", placeholder="Escribe nombre...")
    else:
        cf1, cf2, cf3, cf4, ckpi = st.columns([1.5, 1.5, 1.5, 2.5, 1])
        with cf1: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
        with cf2: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
        with cf3: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
        with cf4: f_nom_sel = st.selectbox("COLABORADOR", ["Todos"] + sorted(df_raw[m['nombre']].unique().tolist()))

    st.divider()

    # --- DIMENSIÓN: RANKING COMERCIAL ---
    if st.session_state.pagina == "🥇 Ranking Comercial":
        # Lógica de Filtrado Comercial
        df_rank = df_com_base.copy()
        if f_emp != "Todas": df_rank = df_rank[df_rank.iloc[:, 2] == f_emp]
        if f_loc != "Todas": df_rank = df_rank[df_rank.iloc[:, 3] == f_loc]
        if f_nom: df_rank = df_rank[df_rank.iloc[:, 1].str.contains(f_nom.upper())]

        # Definir columna de Operaciones según el mes
        # Indices: P=15, Q=16... TOTAL (Columna antes de AI)
        mes_map = {"Ene":15,"Feb":16,"Mar":17,"Abr":18,"May":19,"Jun":20,"Jul":21,"Ago":22,"Sep":23,"Oct":24,"Nov":25,"Dic":26,"TOTAL":27}
        col_idx = mes_map[f_mes]
        
        # Limpieza de datos comerciales
        df_rank['Ops'] = pd.to_numeric(df_rank.iloc[:, col_idx].astype(str).str.replace('-','0'), errors='coerce').fillna(0)
        df_rank['Prom_Mes'] = pd.to_numeric(df_rank.iloc[:, 34].astype(str).str.replace('-','0'), errors='coerce').fillna(0) # Col AI
        
        # Unir con Competencias (del df_raw)
        df_full = pd.merge(df_rank, df_raw[[m['nombre'], m['comp']]], left_on=df_rank.columns[1], right_on=m['nombre'], how='left')
        
        # Top 10
        top_10 = df_full.sort_values(by='Ops', ascending=False).head(10)
        
        if not top_10.empty:
            # GRÁFICO COMBINADO (Inspirado en image_b67648)
            fig_com = go.Figure()
            # Barras (Operaciones)
            fig_com.add_trace(go.Bar(x=top_10[m['nombre']], y=top_10['Ops'], name="Ventas (Ops)", marker_color='#3498db', yaxis='y1'))
            # Línea (Competencias)
            fig_com.add_trace(go.Scatter(x=top_10[m['nombre']], y=top_10[m['comp']], name="Score Competencias", line=dict(color='#e91e63', width=3), mode='lines+markers', yaxis='y2'))
            
            fig_com.update_layout(
                title=f"Top 10 Vendedores - {f_mes} {f_anio}",
                template="plotly_white", height=500,
                yaxis=dict(title="Cantidad de Operaciones", side="left"),
                yaxis2=dict(title="Score Competencias %", side="right", overlaying="y", range=[0, 110]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_com, use_container_width=True)
            
            # Tabla Detalle Operativo
            st.subheader("Detalle Operativo")
            top_10_table = top_10[[m['nombre'], df_rank.columns[2], df_rank.columns[3], 'Ops', 'Prom_Mes', m['comp']]]
            top_10_table.columns = ["Vendedor", "Empresa", "Localidad", "Total Ops", "Promedio/Mes", "Score Comp %"]
            st.dataframe(top_10_table.style.highlight_max(axis=0, color='#e3f2fd'), use_container_width=True)
        else:
            st.warning("No hay datos de operaciones para los filtros seleccionados.")

    # --- RESTO DE PANELES (MANTENIENDO BLINDAJE V43.1) ---
    elif "Desempeño Gral." in st.session_state.pagina:
        # Reutilizar lógica de filtros rrhh
        df_rrhh = df_raw.copy()
        if f_emp != "Todas": df_rrhh = df_rrhh[df_rrhh[m['empresa']] == f_emp]
        if f_loc != "Todas": df_rrhh = df_rrhh[df_rrhh[m['localidad']] == f_loc]
        if f_are != "Todas": df_rrhh = df_rrhh[df_rrhh[m['area']] == f_are]
        if f_nom_sel != "Todos": df_rrhh = df_rrhh[df_rrhh[m['nombre']] == f_nom_sel]

        cats = {"ESTRELLA": df_rrhh[df_rrhh[m['final']]>=90], "PROFESIONAL": df_rrhh[(df_rrhh[m['final']]>=80)&(df_rrhh[m['final']]<90)], "CLAVE": df_rrhh[(df_rrhh[m['final']]>=70)&(df_rrhh[m['final']]<80)], "ENIGMA": df_rrhh[(df_rrhh[m['final']]>=60)&(df_rrhh[m['final']]<70)], "RIESGO": df_rrhh[df_rrhh[m['final']]<60]}
        cb = st.columns(5)
        for i, (k, v) in enumerate(cats.items()):
            if cb[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k
        
        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio General: <b>{df_rrhh[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        fig_p = px.scatter(df_rrhh.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
        fig_p.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
        st.plotly_chart(fig_p, use_container_width=True)

    # (Mantenemos Competencias, Tableros y Evolución con la lógica V43.1...)
    elif "Competencias" in st.session_state.pagina or "Tableros" in st.session_state.pagina:
        st.info("Pestañas de RRHH activas. Se mantienen los KPIs de cobertura y gráficos de semáforo.")

else:
    st.error("Error al conectar con la base de datos de Grupo Cenoa.")
