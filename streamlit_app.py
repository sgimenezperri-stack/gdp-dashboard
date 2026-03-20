import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Grupo Cenoa V48.0", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS PREMIUM (Sidebar + UX) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #263238 !important; min-width: 320px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label { padding: 10px 20px !important; background-color: transparent !important; border-radius: 10px !important; margin-bottom: 8px !important; position: relative; }
    [data-testid="stRadio"] label p { color: #cfd8dc !important; font-size: 1.05rem !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: #3498db !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }

    /* Títulos de Bloque */
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1) { margin-top: 40px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1)::before { content: "GESTIÓN RRHH"; position: absolute; top: -35px; left: 10px; color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5) { margin-top: 60px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5)::before { content: "GESTIÓN COMERCIAL"; position: absolute; top: -35px; left: 10px; color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; border-top: 1px solid rgba(144, 164, 174, 0.2); padding-top: 15px; width: 100%; }

    .kpi-card { background-color: #ffffff; border-radius: 15px; padding: 15px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; height: 70px; }
    .btn-audit button { border: 1px dashed #e74c3c !important; color: #e74c3c !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS (CON RANGO FORZADO A1:AI1000) ---
@st.cache_data(ttl=60)
def load_all_data_master():
    URL_BASE = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        def read_sheet(name):
            p = urllib.parse.quote(name)
            # Agregamos tq=select%20* para forzar lectura de todas las columnas disponibles
            csv_url = f"{URL_BASE.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={p}&tq=select%20*"
            d = pd.read_csv(csv_url)
            d.columns = [str(c).strip() for c in d.columns]
            return d

        df_des = read_sheet("DESEMPEÑO")
        df_p25 = read_sheet("PERFO COMERCIAL 2025")
        df_p26 = read_sheet("PERFO COMERCIAL 2026")

        # Mapeo RRHH
        m = {'nombre': df_des.columns[1], 'empresa': df_des.columns[2], 'localidad': df_des.columns[3],
             'area': df_des.columns[4], 'puesto': df_des.columns[5],
             'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS', 'tablero': '% ACUMULADO TABLERO', 'final': 'DESEMPEÑO'}
        
        df_des[m['nombre']] = df_des[m['nombre']].astype(str).str.upper().str.strip()
        for k in ['comp', 'tablero', 'final']:
            df_des[m[k]] = pd.to_numeric(df_des[m[k]].astype(str).str.replace('-','').str.replace('%','').str.replace(',','.').str.strip(), errors='coerce')
        
        df_des['Inic'] = df_des[m['nombre']].apply(lambda x: (x.split()[0][0] + (x.split()[1][0] if len(x.split())>1 else "")).upper() if len(x)>5 else "")

        # Mapeo Comercial Resiliente (C=2, E=4, F=5, G=6, H=7, I=8, AH=33, AI=34)
        def process_com(df):
            if df.shape[1] >= 35:
                df.rename(columns={df.columns[2]:'VENDEDOR', df.columns[4]:'ANTIGUEDAD', 
                                   df.columns[5]:'EMPRESA', df.columns[6]:'LOCALIDAD',
                                   df.columns[7]:'CANAL', df.columns[8]:'OBJETIVO',
                                   df.columns[33]:'TOTAL_OPS', df.columns[34]:'PROM_MES'}, inplace=True)
                df['VENDEDOR'] = df['VENDEDOR'].astype(str).str.upper().str.strip()
            return df

        return df_des, process_com(df_p25), process_com(df_p26), m
    except Exception as e:
        st.error(f"Error crítico de carga: {e}")
        return None, None, None, None

df_raw, df_25, df_26, m = load_all_data_master()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard 2026 | V48.0")
    menu = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "🥇 Ranking Comercial", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    st.session_state.pagina = st.radio("Nav", menu, index=menu.index(st.session_state.pagina), label_visibility="collapsed")

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # Filtros Dinámicos
    es_com = "Ranking" in st.session_state.pagina
    if es_com:
        f1, f2, f3, f4 = st.columns([1, 1, 2, 3])
        with f1: f_anio = st.selectbox("AÑO", ["2026", "2025"])
        with f2: f_mes = st.selectbox("MES", ["TOTAL", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"])
        df_c_base = df_26 if f_anio == "2026" else df_25
        with f3: f_emp_c = st.selectbox("EMPRESA", ["Todas"] + sorted(df_c_base['EMPRESA'].unique().tolist()) if 'EMPRESA' in df_c_base.columns else ["Todas"])
        with f4: f_vend = st.text_input("BUSCAR VENDEDOR...", placeholder="Nombre...")
    else:
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

    # --- PÁGINA: RANKING COMERCIAL (CORREGIDA) ---
    if st.session_state.pagina == "🥇 Ranking Comercial":
        if 'VENDEDOR' not in df_c_base.columns:
            st.error("La solapa comercial no tiene suficientes columnas o el formato es incorrecto.")
        else:
            df_r = df_c_base.copy()
            # Mapeo de meses (J=9, L=11... AH=33)
            m_idx = {"Ene":9,"Feb":11,"Mar":13,"Abr":15,"May":17,"Jun":19,"Jul":21,"Ago":23,"Sep":25,"Oct":27,"Nov":29,"Dic":31,"TOTAL":33}
            col_t = m_idx[f_mes]
            
            df_r['Ops'] = pd.to_numeric(df_r.iloc[:, col_t].astype(str).str.replace('-','0').str.replace(',','.'), errors='coerce').fillna(0)
            df_r['Prom_Mes_Val'] = pd.to_numeric(df_r['PROM_MES'].astype(str).str.replace('-','0'), errors='coerce').fillna(0)
            
            if f_emp_c != "Todas": df_r = df_r[df_r['EMPRESA'] == f_emp_c]
            if f_vend: df_r = df_r[df_r['VENDEDOR'].str.contains(f_vend.upper())]
            
            df_join = pd.merge(df_r, df_raw[[m['nombre'], m['comp']]], left_on='VENDEDOR', right_on=m['nombre'], how='left')
            top_10 = df_join.sort_values(by='Ops', ascending=False).head(10)
            
            if not top_10.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=top_10['VENDEDOR'], y=top_10['Ops'], name="Operaciones", marker_color='#3498db', yaxis='y1'))
                fig.add_trace(go.Scatter(x=top_10['VENDEDOR'], y=top_10[m['comp']], name="Score Comp.", line=dict(color='#e91e63', width=3), mode='lines+markers', yaxis='y2'))
                fig.update_layout(template="plotly_white", yaxis=dict(title="Ops"), yaxis2=dict(overlaying="y", side="right", range=[0,110]), legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig, use_container_width=True)
                st.write("### Detalle Operativo")
                st.dataframe(top_10[['VENDEDOR', 'EMPRESA', 'ANTIGUEDAD', 'Ops', 'Prom_Mes_Val', m['comp']]], use_container_width=True)
            else: st.warning("Sin datos.")

    # --- PÁGINAS RRHH ---
    elif "Desempeño Gral." in st.session_state.pagina:
        cats = {"ESTRELLA": df_final[df_final[m['final']]>=90], "PROFESIONAL": df_final[(df_final[m['final']]>=80)&(df_final[m['final']]<90)], "CLAVE": df_final[(df_final[m['final']]>=70)&(df_final[m['final']]<80)], "ENIGMA": df_final[(df_final[m['final']]>=60)&(df_final[m['final']]<70)], "RIESGO": df_final[df_final[m['final']]<60]}
        cb = st.columns(5)
        for i, (k, v) in enumerate(cats.items()):
            if cb[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k
        if st.session_state.det_sel in cats:
            st.dataframe(cats[st.session_state.det_sel][[m['nombre'], m['puesto'], m['final']]], use_container_width=True)
        fig_p = px.scatter(df_final.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
        fig_p.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
        st.plotly_chart(fig_p, use_container_width=True)

    elif st.session_state.pagina in ["🧠 Competencias", "📑 Tableros"]:
        is_c = "Competencias" in st.session_state.pagina
        col_d = m['comp'] if is_c else m['tablero']
        q = st.columns(4)
        evals = df_final[col_d].notna().sum(); no_evals = df_final[col_d].isna().sum()
        q[0].markdown(f'<div class="kpi-card"><b>TOTAL</b><br><h3>{len(df_final)}</h3></div>', unsafe_allow_html=True)
        q[1].markdown(f'<div class="kpi-card"><b>CON DATO</b><br><h3 style="color:#3498db;">{evals}</h3></div>', unsafe_allow_html=True)
        with q[2]:
            st.markdown('<div class="btn-audit">', unsafe_allow_html=True)
            if st.button(f"SIN DATO\n({no_evals})"): st.session_state.det_sel = "AUDIT"
            st.markdown('</div>', unsafe_allow_html=True)
        q[3].markdown(f'<div class="kpi-card"><b>PROMEDIO %</b><br><h3>{df_final[col_d].mean():.1f}%</h3></div>', unsafe_allow_html=True)
        if st.session_state.det_sel == "AUDIT":
            st.dataframe(df_final[df_final[col_d].isna()][[m['nombre'], m['empresa'], m['area']]], use_container_width=True)
        st.plotly_chart(px.strip(df_final.dropna(subset=[col_d]), x=m['empresa'], y=col_d, color=m['empresa'], hover_name=m['nombre'], height=500, template="plotly_white"), use_container_width=True)

    elif "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            c_data = df_final.iloc[0]
            vals = [float(str(c_data.iloc[i]).replace('%','').replace(',','.')) if str(c_data.iloc[i]) not in ['-','nan',''] else np.nan for i in range(15,27)]
            h1, h2 = st.columns([3, 1])
            with h1: st.title(f_nom); st.subheader(f"{c_data[m['puesto']]} | {c_data[m['empresa']]}")
            with h2: st.markdown(f'<div class="kpi-card"><h2 style="color:#27ae60;">{np.nanmean(vals):.1f}%</h2>PROM. ANUAL</div>', unsafe_allow_html=True)
            fig_e = go.Figure(go.Scatter(x=["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"], y=vals, mode='lines+markers+text', line=dict(color='#3498db', width=4), textposition="top center"))
            fig_e.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="green", width=2, dash="dash"))
            st.plotly_chart(fig_e.update_layout(height=500, template="plotly_white", yaxis=dict(range=[0, 165])), use_container_width=True)
        else: st.info("👈 Seleccione un colaborador.")

else:
    st.error("Error al conectar con la base de datos.")
