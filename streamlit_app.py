import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Cenoa V46.0", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS PREMIUM (Sidebar Bloques + Diseño Tabla) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238 !important; min-width: 320px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 12px 20px !important; background-color: transparent !important; border-radius: 10px !important; margin-bottom: 8px !important; position: relative; }
    [data-testid="stRadio"] label p { color: #cfd8dc !important; font-size: 1.05rem !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }

    /* Inyección de Títulos de Bloque */
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1) { margin-top: 40px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1)::before { content: "GESTIÓN RRHH"; position: absolute; top: -35px; left: 10px; color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5) { margin-top: 60px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5)::before { content: "GESTIÓN COMERCIAL"; position: absolute; top: -35px; left: 10px; color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; border-top: 1px solid rgba(144, 164, 174, 0.2); padding-top: 15px; width: 100%; }

    .kpi-card { background-color: #ffffff; border-radius: 15px; padding: 15px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; height: 75px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS (Mapeo exacto de columnas C a AI) ---
@st.cache_data(ttl=60)
def load_data_v46():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        def read_s(n):
            p = urllib.parse.quote(n)
            d = pd.read_csv(f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={p}")
            d.columns = [str(c).strip() for c in d.columns]
            return d

        df_des = read_s("DESEMPEÑO")
        df_p25 = read_s("PERFO COMERCIAL 2025")
        df_p26 = read_s("PERFO COMERCIAL 2026")
        
        # Mapeo RRHH
        m = {'nombre': df_des.columns[1], 'empresa': df_des.columns[2], 'localidad': df_des.columns[3],
             'area': df_des.columns[4], 'puesto': df_des.columns[5],
             'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS', 'tablero': '% ACUMULADO TABLERO', 'final': 'DESEMPEÑO'}
        
        # Limpieza de nombres en todas las bases (Col index 2 en Perfo, Col index 1 en Desempeño)
        df_des[m['nombre']] = df_des[m['nombre']].astype(str).str.upper().str.strip()
        df_p25.iloc[:, 2] = df_p25.iloc[:, 2].astype(str).str.upper().str.strip()
        df_p26.iloc[:, 2] = df_p26.iloc[:, 2].astype(str).str.upper().str.strip()
        
        # Limpieza numérica RRHH
        for k in ['comp', 'tablero', 'final']:
            df_des[m[k]] = pd.to_numeric(df_des[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        df_des['Inic'] = df_des[m['nombre']].apply(lambda x: (x.split()[0][0] + (x.split()[1][0] if len(x.split())>1 else "")).upper() if len(x)>5 else "")
        
        return df_des, df_p25, df_p26, m
    except: return None, None, None, None

df_raw, df_25, df_26, m = load_data_v46()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard 2026 | V46.0")
    menu = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "🥇 Ranking Comercial", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    idx_p = menu.index(st.session_state.pagina) if st.session_state.pagina in menu else 0
    st.session_state.pagina = st.radio("Navigation", menu, index=idx_p, label_visibility="collapsed")

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # FILTROS
    if "Ranking Comercial" in st.session_state.pagina:
        f1, f2, f3, f4, f5 = st.columns([1, 1, 2, 2, 2.5])
        with f1: f_anio = st.selectbox("AÑO", ["2026", "2025"])
        meses_ops = ["TOTAL", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        with f2: f_mes = st.selectbox("MES", meses_ops)
        df_c_base = df_26 if f_anio == "2026" else df_25
        # Col 5 es Empresa, Col 6 Localidad, Col 7 Canal
        with f3: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_c_base.iloc[:, 5].dropna().unique().tolist()))
        with f4: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_c_base.iloc[:, 6].dropna().unique().tolist()))
        with f5: f_vendedor = st.text_input("BUSCAR VENDEDOR...", placeholder="Nombre...")
    else:
        # Filtros RRHH Estándar
        cf1, cf2, cf3, cf4, ckpi = st.columns([1.5, 1.5, 1.5, 2.5, 1])
        with cf1: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw[m['empresa']].dropna().unique().tolist()))
        with cf2: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw[m['localidad']].dropna().unique().tolist()))
        with cf3: f_are = st.selectbox("ÁREA", ["Todas"] + sorted(df_raw[m['area']].dropna().unique().tolist()))
        df_f = df_raw.copy()
        if f_emp != "Todas": df_f = df_f[df_f[m['empresa']] == f_emp]
        if f_loc != "Todas": df_f = df_f[df_f[m['localidad']] == f_loc]
        if f_are != "Todas": df_f = df_f[df_f[m['area']] == f_are]
        with cf4: f_nom = st.selectbox("COLABORADOR", ["Todos"] + sorted(df_f[m['nombre']].unique().tolist()))
        df_final = df_f if f_nom == "Todos" else df_f[df_f[m['nombre']] == f_nom]
        with ckpi: st.markdown(f'<div class="kpi-card"><span style="font-size:0.6rem;font-weight:bold;">DOTACIÓN</span><br><b>{len(df_final)}</b></div>', unsafe_allow_html=True)

    st.divider()

    # --- DIMENSIÓN: RANKING COMERCIAL ---
    if st.session_state.pagina == "🥇 Ranking Comercial":
        df_r = df_c_base.copy()
        
        # Mapeo según tus columnas: J, L, N, P, R, T, V, X, Z, AB, AD, AF (Indices: 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31)
        # AH = TOTAL (33), AI = PROMEDIO (34)
        mes_idx_map = {"Ene":9,"Feb":11,"Mar":13,"Abr":15,"May":17,"Jun":19,"Jul":21,"Ago":23,"Sep":25,"Oct":27,"Nov":29,"Dic":31,"TOTAL":33}
        target_idx = mes_idx_map[f_mes]
        
        df_r['Ops'] = pd.to_numeric(df_r.iloc[:, target_idx].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)
        df_r['Prom_Mes'] = pd.to_numeric(df_r.iloc[:, 34].astype(str).str.replace('-', '0'), errors='coerce').fillna(0) # Col AI
        df_r['Seniority'] = df_r.iloc[:, 4] # Col E
        
        # Filtros Comerciales
        if f_emp != "Todas": df_r = df_r[df_r.iloc[:, 5] == f_emp]
        if f_loc != "Todas": df_r = df_r[df_r.iloc[:, 6] == f_loc]
        if f_vendedor: df_r = df_r[df_r.iloc[:, 2].str.contains(f_vendedor.upper())]
        
        # Merge con Score de Competencias de la solapa DESEMPEÑO
        df_merge = pd.merge(df_r, df_raw[[m['nombre'], m['comp']]], left_on=df_r.columns[2], right_on=m['nombre'], how='left')
        
        top_10 = df_merge.sort_values(by='Ops', ascending=False).head(10)
        
        if not top_10.empty:
            # GRÁFICO RANKING (Inspo image_b67648)
            fig_rank = go.Figure()
            fig_rank.add_trace(go.Bar(x=top_10[m['nombre']], y=top_10['Ops'], name="Cantidad de Operaciones", marker_color='#3498db', yaxis='y1'))
            fig_rank.add_trace(go.Scatter(x=top_10[m['nombre']], y=top_10[m['comp']], name="Score Competencias %", line=dict(color='#e91e63', width=3), mode='lines+markers', yaxis='y2'))
            
            fig_rank.update_layout(
                title=f"Top 10 Vendedores - {f_mes} {f_anio}", template="plotly_white", height=500,
                yaxis=dict(title="Ventas (Operaciones)"),
                yaxis2=dict(title="Competencias %", overlaying="y", side="right", range=[0, 110]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_rank, use_container_width=True)
            
            # TABLA DETALLE OPERATIVO
            st.subheader("Detalle Operativo")
            table_view = top_10[[m['nombre'], top_10.columns[5], top_10.columns[6], 'Ops', 'Prom_Mes', m['comp']]]
            table_view.columns = ["Vendedor", "Empresa", "Localidad", "Total Ops", "Promedio/Mes", "Score Comp %"]
            st.dataframe(table_view.style.highlight_max(axis=0, color='#e3f2fd'), use_container_width=True)
        else:
            st.warning("Sin datos para los filtros seleccionados.")

    # --- PÁGINA: DESEMPEÑO GRAL (RESTAURADA) ---
    elif "Desempeño Gral." in st.session_state.pagina:
        cats = {"ESTRELLA": df_final[df_final[m['final']]>=90], "PROFESIONAL": df_final[(df_final[m['final']]>=80)&(df_final[m['final']]<90)], "CLAVE": df_final[(df_final[m['final']]>=70)&(df_final[m['final']]<80)], "ENIGMA": df_final[(df_final[m['final']]>=60)&(df_final[m['final']]<70)], "RIESGO": df_final[df_final[m['final']]<60]}
        cb = st.columns(5)
        for i, (k, v) in enumerate(cats.items()):
            if cb[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k
        if st.session_state.det_sel in cats:
            st.dataframe(cats[st.session_state.det_sel][[m['nombre'], m['puesto'], m['final']]], use_container_width=True)
            if st.button("Cerrar"): st.session_state.det_sel = None; st.rerun()
        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio: <b>{df_final[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        fig_p = px.scatter(df_final.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
        fig_p.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
        st.plotly_chart(fig_p, use_container_width=True)

    # --- EVOLUCIÓN (RESTAURADA) ---
    elif "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            c_data = df_final.iloc[0]
            meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            # En DESEMPEÑO, meses son Col P a AA (Indices 15 a 26)
            vals = [float(str(c_data.iloc[i]).replace('%','').replace(',','.')) if str(c_data.iloc[i]) not in ['-','nan',''] else np.nan for i in range(15,27)]
            h1, h2 = st.columns([3, 1])
            with h1: st.title(f_nom); st.subheader(f"{c_data[m['puesto']]} | {c_data[m['empresa']]}")
            with h2: st.markdown(f'<div class="kpi-card"><h2 style="color:#27ae60;">{np.nanmean(vals):.1f}%</h2>PROM. ANUAL</div>', unsafe_allow_html=True)
            fig_e = go.Figure(go.Scatter(x=meses, y=vals, mode='lines+markers+text', line=dict(color='#3498db', width=4), text=[f"{v:.0f}%" if not np.isnan(v) else "" for v in vals], textposition="top center"))
            fig_e.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="green", width=2, dash="dash"))
            st.plotly_chart(fig_e.update_layout(height=500, template="plotly_white", yaxis=dict(range=[0, 165])), use_container_width=True)
        else: st.info("👈 Seleccione un colaborador.")

else: st.error("Error al conectar con la base de datos.")
