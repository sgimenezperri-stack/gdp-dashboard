import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Cenoa Analytics V52.0", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."

# --- 2. CSS PREMIUM (Sidebar + Tablas + KPIs) ---
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

    .kpi-card { background-color: #ffffff; border-radius: 15px; padding: 20px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MOTOR DE CARGA RESILIENTE (A1:AI1000) ---
@st.cache_data(ttl=60)
def load_data_v52():
    URL_BASE = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        def fetch(sheet):
            p = urllib.parse.quote(sheet)
            # Forzamos el rango A1:AI para asegurar que AH y AI se descarguen
            csv_url = f"{URL_BASE.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={p}&range=A1:AJ1000"
            df = pd.read_csv(csv_url)
            df.columns = [str(c).strip() for c in df.columns]
            return df

        df_des = fetch("DESEMPEÑO")
        df_25 = fetch("PERFO COMERCIAL 2025")
        df_26 = fetch("PERFO COMERCIAL 2026")

        # Mapeo Comercial (C=2, E=4, F=5, G=6, H=7, I=8, AH=33, AI=34)
        def map_com(df):
            if df.shape[1] >= 35:
                df.rename(columns={
                    df.columns[2]: 'VENDEDOR', df.columns[4]: 'ANTIGÜEDAD',
                    df.columns[5]: 'EMPRESA', df.columns[6]: 'LOCALIDAD',
                    df.columns[7]: 'CANAL', df.columns[8]: 'OBJETIVO',
                    df.columns[33]: 'TOTAL_OPS', df.columns[34]: 'PROM_VENTAS'
                }, inplace=True)
                df['VENDEDOR'] = df['VENDEDOR'].astype(str).str.upper().str.strip()
            return df

        return df_des, map_com(df_25), map_com(df_26)
    except Exception as e:
        st.error(f"Error de conexión con Sheets: {e}")
        return None, None, None

df_rrhh_raw, df_p25, df_p26 = load_data_v52()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    menu = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "🥇 Ranking Comercial", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    st.session_state.pagina = st.radio("Nav", menu, index=menu.index(st.session_state.pagina), label_visibility="collapsed")

# --- 5. PANEL PRINCIPAL ---
if df_p26 is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # --- PÁGINA: RANKING COMERCIAL ---
    if st.session_state.pagina == "🥇 Ranking Comercial":
        # FILTROS ANALYTICS
        f1, f2, f3, f4, f5 = st.columns([1, 1.2, 1.5, 1.5, 1.5])
        with f1: f_anio = st.selectbox("AÑO FISCAL", ["2026", "2025"])
        # Mapeo de columnas de Ops (J=9, L=11, N=13... AF=31, AH=33)
        meses_ops = {"TOTAL": 33, "Ene": 9, "Feb": 11, "Mar": 13, "Abr": 15, "May": 17, "Jun": 19, "Jul": 21, "Ago": 23, "Sep": 25, "Oct": 27, "Nov": 29, "Dic": 31}
        with f2: f_mes = st.selectbox("MES", list(meses_ops.keys()))
        
        df_base = df_p26 if f_anio == "2026" else df_p25
        
        with f3: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_base['EMPRESA'].dropna().unique().tolist()))
        with f4: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_base['LOCALIDAD'].dropna().unique().tolist()))
        with f5: f_can = st.selectbox("CANAL DE VENTA", ["Todos"] + sorted(df_base['CANAL'].dropna().unique().tolist()))

        # Procesamiento Dinámico
        df_f = df_base.copy()
        if f_emp != "Todas": df_f = df_f[df_f['EMPRESA'] == f_emp]
        if f_loc != "Todas": df_f = df_f[df_f['LOCALIDAD'] == f_loc]
        if f_can != "Todos": df_f = df_f[df_f['CANAL'] == f_can]

        idx_target = meses_ops[f_mes]
        df_f['Ops_Mes'] = pd.to_numeric(df_f.iloc[:, idx_target].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)
        df_f['Obj'] = pd.to_numeric(df_f['OBJETIVO'].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)
        df_f['Promedio'] = pd.to_numeric(df_f['PROM_VENTAS'].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)

        # KPI CARDS
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div class="kpi-card"><b>Vendedores</b><br><h3>{len(df_f)}</h3></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-card"><b>Ops {f_mes}</b><br><h3>{int(df_f["Ops_Mes"].sum())}</h3></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-card"><b>Venta Promedio</b><br><h3>{df_f["Ops_Mes"].mean():.1f}</h3></div>', unsafe_allow_html=True)
        cumplimiento = (df_f['Ops_Mes'].sum() / df_f['Obj'].sum() * 100) if df_f['Obj'].sum() > 0 else 0
        k4.markdown(f'<div class="kpi-card"><b>% Cumplimiento Cuota</b><br><h3 style="color:#27ae60;">{cumplimiento:.1f}%</h3></div>', unsafe_allow_html=True)

        st.divider()

        # PEOPLE ANALYTICS: Ranking Top 10
        st.subheader(f"🏆 Top 10 Vendedores - Desempeño Operativo ({f_mes} {f_anio})")
        top_10 = df_f.sort_values(by='Ops_Mes', ascending=False).head(10)
        
        fig_r = px.bar(top_10, x='Ops_Mes', y='VENDEDOR', orientation='h', text='Ops_Mes',
                       color='Ops_Mes', color_continuous_scale='Blues',
                       hover_data=['ANTIGÜEDAD', 'CANAL', 'EMPRESA'])
        fig_r.update_layout(yaxis={'categoryorder':'total ascending'}, height=500, template="plotly_white", showlegend=False)
        st.plotly_chart(fig_r, use_container_width=True)

        # DETALLE OPERATIVO (Basado en Columnas C a AI)
        st.subheader("📋 Auditoría Operativa por Vendedor")
        df_auditoria = df_f[['VENDEDOR', 'ANTIGÜEDAD', 'EMPRESA', 'LOCALIDAD', 'CANAL', 'OBJETIVO', 'Ops_Mes', 'PROM_VENTAS']]
        df_auditoria.columns = ["Vendedor", "Antigüedad", "Empresa", "Localidad", "Canal", "Objetivo", f"Ventas {f_mes}", "Promedio Hist."]
        
        st.dataframe(df_auditoria.sort_values(by=f"Ventas {f_mes}", ascending=False).style.background_gradient(subset=[f"Ventas {f_mes}"], cmap="Greens"), use_container_width=True)

    # --- BLOQUE RRHH (Mantenimiento de Datos Blindados) ---
    elif st.session_state.pagina == "👤 Desempeño Gral.":
        st.info("Visualizando datos de la solapa DESEMPEÑO.")
        # Aquí continúa la lógica ya blindada anteriormente de Desempeño Gral.

else:
    st.error("Error al cargar la información. Verifique que las solapas PERFO COMERCIAL existan en el Google Sheets.")
