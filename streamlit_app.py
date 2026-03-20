import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Cenoa Commercial Analytics V50.0", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."

# --- 2. CSS PREMIUM (Sidebar Bloques + Diseño de Datos) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238 !important; min-width: 320px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 12px 20px !important; background-color: transparent !important; border-radius: 10px !important; margin-bottom: 8px !important; position: relative; }
    [data-testid="stRadio"] label p { color: #cfd8dc !important; font-size: 1.05rem !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }

    /* Separadores de Bloques */
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1) { margin-top: 40px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1)::before { content: "GESTIÓN RRHH"; position: absolute; top: -35px; left: 10px; color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5) { margin-top: 60px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5)::before { content: "GESTIÓN COMERCIAL"; position: absolute; top: -35px; left: 10px; color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; border-top: 1px solid rgba(144, 164, 174, 0.2); padding-top: 15px; width: 100%; }

    .kpi-card { background-color: #ffffff; border-radius: 15px; padding: 15px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .commercial-box { background-color: #f0f7ff; border-left: 5px solid #3498db; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS (AISLAMIENTO TOTAL POR BLOQUE) ---
@st.cache_data(ttl=60)
def load_data_exclusive():
    URL_BASE = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        def get_csv(sheet):
            p = urllib.parse.quote(sheet)
            return pd.read_csv(f"{URL_BASE.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={p}")

        df_des = get_csv("DESEMPEÑO")
        df_c25 = get_csv("PERFO COMERCIAL 2025")
        df_c26 = get_csv("PERFO COMERCIAL 2026")

        # Limpieza RRHH
        m_rrhh = {'nombre': df_des.columns[1], 'empresa': df_des.columns[2], 'localidad': df_des.columns[3],
                  'area': df_des.columns[4], 'puesto': df_des.columns[5],
                  'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS', 'tablero': '% ACUMULADO TABLERO', 'final': 'DESEMPEÑO'}

        # Limpieza y Estandarización Comercial (Mapeo C a AI)
        def clean_com(df):
            # C=2, E=4, F=5, G=6, H=7, I=8, AH=33, AI=34
            cols = {
                df.columns[2]: 'VENDEDOR',
                df.columns[4]: 'ANTIGÜEDAD',
                df.columns[5]: 'EMPRESA',
                df.columns[6]: 'LOCALIDAD',
                df.columns[7]: 'CANAL',
                df.columns[8]: 'OBJETIVO',
                df.columns[33]: 'TOTAL_ANUAL',
                df.columns[34]: 'PROMEDIO_VENTAS'
            }
            df.rename(columns=cols, inplace=True)
            df['VENDEDOR'] = df['VENDEDOR'].astype(str).str.upper().str.strip()
            return df

        return df_des, clean_com(df_c25), clean_com(df_c26), m_rrhh
    except Exception as e:
        st.error(f"Falla en carga: {e}")
        return None, None, None, None

df_rrhh_raw, df_2025, df_2026, m_rrhh = load_data_exclusive()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    menu = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "🥇 Ranking Comercial", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    st.session_state.pagina = st.radio("Nav", menu, index=menu.index(st.session_state.pagina), label_visibility="collapsed")

# --- 5. PANEL PRINCIPAL ---
if df_rrhh_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # --- LÓGICA: RANKING COMERCIAL (BLOQUE EXCLUSIVO) ---
    if st.session_state.pagina == "🥇 Ranking Comercial":
        # Filtros de Negocio
        f1, f2, f3, f4, f5 = st.columns([1, 1.2, 1.5, 1.5, 1.5])
        with f1: f_anio = st.selectbox("AÑO", ["2026", "2025"])
        meses_map = {"TOTAL":33, "Ene":9, "Feb":11, "Mar":13, "Abr":15, "May":17, "Jun":19, "Jul":21, "Ago":23, "Sep":25, "Oct":27, "Nov":29, "Dic":31}
        with f2: f_mes = st.selectbox("MES A ANALIZAR", list(meses_map.keys()))
        
        df_c = df_2026 if f_anio == "2026" else df_2025
        
        with f3: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_c['EMPRESA'].dropna().unique().tolist()))
        with f4: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_c['LOCALIDAD'].dropna().unique().tolist()))
        with f5: f_can = st.selectbox("CANAL DE VENTA", ["Todos"] + sorted(df_c['CANAL'].dropna().unique().tolist()))

        # Procesamiento de Datos
        df_f = df_c.copy()
        if f_emp != "Todas": df_f = df_f[df_f['EMPRESA'] == f_emp]
        if f_loc != "Todas": df_f = df_f[df_f['LOCALIDAD'] == f_loc]
        if f_can != "Todos": df_f = df_f[df_f['CANAL'] == f_can]

        # Extraer operaciones del mes seleccionado (Posición dinámica)
        col_idx = meses_map[f_mes]
        df_f['Ops_Mes'] = pd.to_numeric(df_f.iloc[:, col_idx].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)
        df_f['Promedio'] = pd.to_numeric(df_f['PROMEDIO_VENTAS'].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)
        df_f['Obj'] = pd.to_numeric(df_f['OBJETIVO'].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)
        
        # KPIs Analytics
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div class="kpi-card"><b>Vendedores Activos</b><br><h3>{len(df_f)}</h3></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-card"><b>Total Ops {f_mes}</b><br><h3>{int(df_f["Ops_Mes"].sum())}</h3></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-card"><b>Promedio por Vendedor</b><br><h3>{df_f["Ops_Mes"].mean():.1f}</h3></div>', unsafe_allow_html=True)
        # Cumplimiento vs Objetivo (si el objetivo es > 0)
        cumplimiento = (df_f['Ops_Mes'].sum() / df_f['Obj'].sum() * 100) if df_f['Obj'].sum() > 0 else 0
        k4.markdown(f'<div class="kpi-card"><b>Cumplimiento Cuota</b><br><h3 style="color:#27ae60;">{cumplimiento:.1f}%</h3></div>', unsafe_allow_html=True)

        st.divider()

        # Visualización de People Analytics: Ops vs Antigüedad
        st.subheader(f"🥇 Ranking Top 10 Vendedores - {f_mes} {f_anio}")
        top_10 = df_f.sort_values(by='Ops_Mes', ascending=False).head(10)
        
        fig_rank = px.bar(top_10, x='Ops_Mes', y='VENDEDOR', orientation='h', 
                          text='Ops_Mes', color='Ops_Mes', color_continuous_scale='Blues',
                          hover_data=['ANTIGÜEDAD', 'CANAL', 'OBJETIVO'])
        fig_rank.update_layout(yaxis={'categoryorder':'total ascending'}, height=500, template="plotly_white", showlegend=False)
        st.plotly_chart(fig_rank, use_container_width=True)

        st.subheader("📋 Detalle Operativo Completo")
        # Tabla formateada con People Analytics
        df_display = df_f[['VENDEDOR', 'ANTIGÜEDAD', 'EMPRESA', 'LOCALIDAD', 'CANAL', 'OBJETIVO', 'Ops_Mes', 'PROMEDIO_VENTAS']]
        df_display.columns = ["Vendedor", "Antigüedad", "Empresa", "Localidad", "Canal", "Objetivo", f"Ops {f_mes}", "Prom. Histórico"]
        
        st.dataframe(df_display.sort_values(by=f"Ops {f_mes}", ascending=False).style.background_gradient(subset=[f"Ops {f_mes}"], cmap="Greens"), use_container_width=True)

    # --- MANTENIMIENTO BLOQUE RRHH (BLINDADO) ---
    elif st.session_state.pagina == "👤 Desempeño Gral.":
        # Filtros RRHH
        c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.5, 2.5])
        with c1: fr_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_rrhh_raw[m_rrhh['empresa']].dropna().unique().tolist()))
        # ... resto de lógica RRHH ya construida ...
        st.info("Pestaña de RRHH cargada con datos de la solapa DESEMPEÑO.")

else:
    st.error("Error al conectar con las solapas comerciales.")
