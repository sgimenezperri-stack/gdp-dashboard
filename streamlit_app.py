import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Cenoa Analytics 2025 | V53.0", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."

# --- 2. CSS PREMIUM (Sidebar + Tablas) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238 !important; min-width: 320px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 12px 20px !important; background-color: transparent !important; border-radius: 10px !important; margin-bottom: 8px !important; position: relative; }
    [data-testid="stRadio"] label p { color: #cfd8dc !important; font-size: 1.05rem !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }

    /* Separadores de Bloques Sidebar */
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1) { margin-top: 40px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1)::before { content: "GESTIÓN RRHH"; position: absolute; top: -35px; left: 10px; color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5) { margin-top: 60px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5)::before { content: "GESTIÓN COMERCIAL"; position: absolute; top: -35px; left: 10px; color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; border-top: 1px solid rgba(144, 164, 174, 0.2); padding-top: 15px; width: 100%; }

    .kpi-card { background-color: #ffffff; border-radius: 15px; padding: 20px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MOTOR DE CARGA (SOLO 2025 PARA COMERCIAL) ---
@st.cache_data(ttl=60)
def load_data_v53():
    URL_BASE = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        def fetch(sheet):
            p = urllib.parse.quote(sheet)
            # Forzamos lectura amplia para capturar AH (33) y AI (34)
            csv_url = f"{URL_BASE.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={p}&range=A1:AJ2000"
            df = pd.read_csv(csv_url)
            df.columns = [str(c).strip() for c in df.columns]
            return df

        # Carga RRHH
        df_des = fetch("DESEMPEÑO")
        m_rrhh = {'nombre': df_des.columns[1], 'empresa': df_des.columns[2], 'localidad': df_des.columns[3],
                  'area': df_des.columns[4], 'puesto': df_des.columns[5],
                  'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS', 'tablero': '% ACUMULADO TABLERO', 'final': 'DESEMPEÑO'}

        # Carga Comercial SOLO 2025
        df_2025 = fetch("PERFO COMERCIAL 2025")
        
        # Mapeo Seguro basado en tus especificaciones (C=2, E=4, F=5, G=6, H=7, I=8, AH=33, AI=34)
        if df_2025.shape[1] >= 35:
            df_2025.rename(columns={
                df_2025.columns[2]: 'VENDEDOR', 
                df_2025.columns[4]: 'ANTIGÜEDAD',
                df_2025.columns[5]: 'EMPRESA', 
                df_2025.columns[6]: 'LOCALIDAD',
                df_2025.columns[7]: 'CANAL', 
                df_2025.columns[8]: 'OBJETIVO',
                df_2025.columns[33]: 'TOTAL_OPS', 
                df_2025.columns[34]: 'PROM_VENTAS'
            }, inplace=True)
            df_2025['VENDEDOR'] = df_2025['VENDEDOR'].astype(str).str.upper().str.strip()
        
        return df_des, df_2025, m_rrhh
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return None, None, None

df_rrhh, df_p25, m_rrhh = load_data_v53()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    menu = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "🥇 Ranking Comercial", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    st.session_state.pagina = st.radio("Nav", menu, index=menu.index(st.session_state.pagina), label_visibility="collapsed")

# --- 5. PANEL PRINCIPAL ---
if df_p25 is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # --- PÁGINA: RANKING COMERCIAL (EXCLUSIVO 2025) ---
    if st.session_state.pagina == "🥇 Ranking Comercial":
        # Verificamos si las columnas existen tras el mapeo
        if 'LOCALIDAD' not in df_p25.columns:
            st.error("No se detectó la columna LOCALIDAD en la solapa 2025. Verifique el formato del Excel.")
        else:
            # Filtros Analytics
            f1, f2, f3, f4 = st.columns([1, 1.5, 1.5, 2])
            with f1: f_mes = st.selectbox("MES", ["TOTAL", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"])
            with f2: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_p25['EMPRESA'].dropna().unique().tolist()))
            with f3: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_p25['LOCALIDAD'].dropna().unique().tolist()))
            with f4: f_can = st.selectbox("CANAL DE VENTA", ["Todos"] + sorted(df_p25['CANAL'].dropna().unique().tolist()))

            # Procesamiento de Datos
            df_f = df_p25.copy()
            if f_emp != "Todas": df_f = df_f[df_f['EMPRESA'] == f_emp]
            if f_loc != "Todas": df_f = df_f[df_f[m_rrhh['localidad']] == f_loc] # Usamos el mapeo para mayor seguridad
            if f_can != "Todos": df_f = df_f[df_f['CANAL'] == f_can]

            # Mapeo de columnas de operaciones (J, L, N, P...)
            meses_map = {"TOTAL": 33, "Ene": 9, "Feb": 11, "Mar": 13, "Abr": 15, "May": 17, "Jun": 19, "Jul": 21, "Ago": 23, "Sep": 25, "Oct": 27, "Nov": 29, "Dic": 31}
            idx_target = meses_map[f_mes]
            
            df_f['Ops_Mes'] = pd.to_numeric(df_f.iloc[:, idx_target].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)
            df_f['Obj'] = pd.to_numeric(df_f['OBJETIVO'].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)

            # KPI CARDS
            k1, k2, k3 = st.columns(3)
            k1.markdown(f'<div class="kpi-card"><b>Vendedores</b><br><h3>{len(df_f)}</h3></div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="kpi-card"><b>Total Ops {f_mes}</b><br><h3>{int(df_f["Ops_Mes"].sum())}</h3></div>', unsafe_allow_html=True)
            cumplimiento = (df_f['Ops_Mes'].sum() / df_f['Obj'].sum() * 100) if df_f['Obj'].sum() > 0 else 0
            k3.markdown(f'<div class="kpi-card"><b>% Cumplimiento</b><br><h3 style="color:#27ae60;">{cumplimiento:.1f}%</h3></div>', unsafe_allow_html=True)

            st.divider()

            # RANKING TOP 10
            st.subheader(f"🏆 Top 10 Vendedores - Perfo 2025 ({f_mes})")
            top_10 = df_f.sort_values(by='Ops_Mes', ascending=False).head(10)
            
            fig = px.bar(top_10, x='Ops_Mes', y='VENDEDOR', orientation='h', text='Ops_Mes',
                         color='Ops_Mes', color_continuous_scale='Greens')
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=450, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

            # DETALLE OPERATIVO
            st.subheader("📋 Detalle Auditoría - People Analytics")
            df_det = df_f[['VENDEDOR', 'ANTIGÜEDAD', 'EMPRESA', 'LOCALIDAD', 'CANAL', 'Ops_Mes', 'PROM_VENTAS']]
            df_det.columns = ["Vendedor", "Antigüedad", "Empresa", "Localidad", "Canal", f"Ventas {f_mes}", "Promedio Hist."]
            st.dataframe(df_det.sort_values(by=f"Ventas {f_mes}", ascending=False), use_container_width=True)

    # --- RESTO DE PÁGINAS (RRHH) ---
    elif st.session_state.pagina == "👤 Desempeño Gral.":
        st.info("Pestaña de RRHH activa. Cargando datos de solapa DESEMPEÑO...")
        # Aquí continúa tu lógica ya blindada anteriormente

else:
    st.error("No se pudo cargar la solapa PERFO COMERCIAL 2025. Por favor, verifica que el nombre sea exacto en el Google Sheets.")
