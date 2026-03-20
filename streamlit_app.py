import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Grupo Cenoa V45.0", layout="wide")

# Inicialización de estados
if 'pagina' not in st.session_state: st.session_state.pagina = "👤 Desempeño Gral."
if 'det_sel' not in st.session_state: st.session_state.det_sel = None

# --- 2. CSS PREMIUM (Sidebar por Bloques + KPIs + Botones) ---
st.markdown("""
    <style>
    /* Sidebar fondo y ancho */
    [data-testid="stSidebar"] { background-color: #263238 !important; min-width: 320px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    
    /* Estilo de los botones del menú lateral */
    [data-testid="stRadio"] div[role="radiogroup"] label {
        padding: 12px 20px !important; background-color: transparent !important;
        border-radius: 10px !important; margin-bottom: 8px !important;
        transition: all 0.3s ease; position: relative;
    }
    [data-testid="stRadio"] label p { color: #cfd8dc !important; font-size: 1.05rem !important; font-weight: 500 !important; }
    [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] {
        background-color: #3498db !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    [data-testid="stRadio"] label[data-baseweb="radio"] p { color: white !important; font-weight: bold !important; }

    /* INYECCIÓN DE TÍTULOS DE BLOQUE */
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1) { margin-top: 40px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1)::before {
        content: "GESTIÓN RRHH"; position: absolute; top: -35px; left: 10px;
        color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px;
    }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5) { margin-top: 60px !important; }
    [data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(5)::before {
        content: "GESTIÓN COMERCIAL"; position: absolute; top: -35px; left: 10px;
        color: #90a4ae; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px;
        border-top: 1px solid rgba(144, 164, 174, 0.2); padding-top: 15px; width: 100%;
    }

    /* Componentes Generales */
    .kpi-card { background-color: #ffffff; border-radius: 15px; padding: 15px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .analista-box { background-color: #f8f9fa; border-left: 5px solid #6f42c1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    div.stButton > button { width: 100%; border-radius: 10px; font-weight: bold; background-color: white; height: 70px; }
    .btn-audit button { border: 1px dashed #e74c3c !important; color: #e74c3c !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS MULTI-SOLAPA ---
@st.cache_data(ttl=60)
def load_all_data_v45():
    URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"
    try:
        def read_s(n):
            p = urllib.parse.quote(n)
            d = pd.read_csv(f"{URL.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={p}")
            d.columns = d.columns.str.strip()
            return d

        df_des = read_s("DESEMPEÑO")
        df_25 = read_s("PERFO COMERCIAL 2025")
        df_26 = read_s("PERFO COMERCIAL 2026")
        
        m = {
            'nombre': df_des.columns[1], 'empresa': df_des.columns[2], 'localidad': df_des.columns[3],
            'area': df_des.columns[4], 'puesto': df_des.columns[5],
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS', 
            'tablero': '% ACUMULADO TABLERO', 
            'final': 'DESEMPEÑO'
        }
        
        # Limpieza General
        df_des[m['nombre']] = df_des[m['nombre']].astype(str).str.upper().str.strip()
        for k in ['comp', 'tablero', 'final']:
            df_des[m[k]] = pd.to_numeric(df_des[m[k]].astype(str).str.replace('-', '').str.replace('%', '').str.replace(',', '.').str.strip(), errors='coerce')
        
        def get_sem(v):
            if pd.isna(v): return "Sin Dato"
            return "Verde (>90%)" if v >= 90 else "Amarillo (80-90%)" if v >= 80 else "Rojo (<80%)"
        df_des['Sem_Comp'] = df_des[m['comp']].apply(get_sem)
        df_des['Sem_Tab'] = df_des[m['tablero']].apply(get_sem)
        df_des['Inic'] = df_des[m['nombre']].apply(lambda x: (x.split()[0][0] + (x.split()[1][0] if len(x.split())>1 else "")).upper() if len(x)>3 else "")
        
        return df_des, df_25, df_26, m
    except: return None, None, None, None

df_raw, df_25, df_26, m = load_all_data_v45()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Grupo Cenoa")
    st.caption("Dashboard 2026 | V45.0")
    menu_completo = ["👤 Desempeño Gral.", "🧠 Competencias", "📑 Tableros", "📈 Evolución", "🥇 Ranking Comercial", "📊 Perf. Comercial", "🔳 Matriz 9-Box"]
    idx_act = menu_completo.index(st.session_state.pagina) if st.session_state.pagina in menu_completo else 0
    seleccion = st.radio("Navigation", menu_completo, index=idx_act, label_visibility="collapsed")
    
    if st.session_state.pagina != seleccion:
        st.session_state.pagina = seleccion
        st.session_state.det_sel = None
        st.rerun()

# --- 5. PANEL PRINCIPAL ---
if df_raw is not None:
    st.header(st.session_state.pagina.split(" ", 1)[1])

    # FILTROS GLOBALES
    es_com = st.session_state.pagina in ["🥇 Ranking Comercial", "📊 Perf. Comercial"]
    if es_com:
        cf1, cf2, cf3, cf4 = st.columns([1, 1, 2, 2.5])
        with cf1: f_anio = st.selectbox("AÑO", ["2026", "2025"])
        meses_ops = ["TOTAL", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        with cf2: f_mes = st.selectbox("MES", meses_ops)
        df_com_base = df_26 if f_anio == "2026" else df_25
        with cf3: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_com_base.iloc[:, 2].dropna().unique().tolist()))
        with cf4: f_nom_com = st.text_input("BUSCAR VENDEDOR...", placeholder="Escribe nombre...")
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
    cmap = {"Verde (>90%)": "#27ae60", "Amarillo (80-90%)": "#f1c40f", "Rojo (<80%)": "#c0392b", "Sin Dato": "#bdc3c7"}

    # --- DIMENSIÓN: DESEMPEÑO GRAL ---
    if "Desempeño Gral." in st.session_state.pagina:
        cats_g = {"ESTRELLA": df_final[df_final[m['final']] >= 90], "PROFESIONAL": df_final[(df_final[m['final']] >= 80) & (df_final[m['final']] < 90)], "CLAVE": df_final[(df_final[m['final']] >= 70) & (df_final[m['final']] < 80)], "ENIGMA": df_final[(df_final[m['final']] >= 60) & (df_final[m['final']] < 70)], "RIESGO": df_final[df_final[m['final']] < 60]}
        c_btns = st.columns(5)
        for i, (k, v) in enumerate(cats_g.items()):
            if c_btns[i].button(f"{k}\n({len(v)})"): st.session_state.det_sel = k
        if st.session_state.det_sel in cats_g:
            st.dataframe(cats_g[st.session_state.det_sel][[m['nombre'], m['puesto'], m['final']]], use_container_width=True)
            if st.button("Cerrar"): st.session_state.det_sel = None; st.rerun()
        st.markdown(f'<div class="analista-box"><strong>📝 Analista Virtual:</strong> Promedio General: <b>{df_final[m["final"]].mean():.1f}%</b></div>', unsafe_allow_html=True)
        fig_p = px.scatter(df_final.dropna(subset=[m['comp'], m['tablero']]), x=m['tablero'], y=m['comp'], color=m['area'], text='Inic', hover_name=m['nombre'], height=600, template="plotly_white")
        fig_p.update_traces(textposition='middle center', textfont=dict(size=10, color='white', family="Arial Black"), marker=dict(size=35, opacity=0.8, line=dict(width=1, color='white')))
        st.plotly_chart(fig_p, use_container_width=True)

    # --- DIMENSIONES COMPETENCIAS / TABLEROS ---
    elif st.session_state.pagina in ["🧠 Competencias", "📑 Tableros"]:
        is_comp = "Competencias" in st.session_state.pagina
        col_d = m['comp'] if is_comp else m['tablero']
        sem_d = 'Sem_Comp' if is_comp else 'Sem_Tab'
        
        evals = df_final[col_d].notna().sum(); no_evals = df_final[col_d].isna().sum()
        q1, q2, q3, q4 = st.columns(4)
        q1.markdown(f'<div class="kpi-card"><b>TOTAL</b><br><h3>{len(df_final)}</h3></div>', unsafe_allow_html=True)
        q2.markdown(f'<div class="kpi-card"><b>CON DATO</b><br><h3 style="color:#3498db;">{evals}</h3></div>', unsafe_allow_html=True)
        with q3:
            st.markdown('<div class="btn-audit">', unsafe_allow_html=True)
            if st.button(f"SIN DATO\n({no_evals})"): st.session_state.det_sel = "AUDIT"
            st.markdown('</div>', unsafe_allow_html=True)
        q4.markdown(f'<div class="kpi-card"><b>PROMEDIO %</b><br><h3>{df_final[col_d].mean():.1f}%</h3></div>', unsafe_allow_html=True)

        if st.session_state.det_sel == "AUDIT":
            st.error(f"Pendientes de Carga ({no_evals})")
            st.dataframe(df_final[df_final[col_d].isna()][[m['nombre'], m['empresa'], m['area']]], use_container_width=True)
            if st.button("✖️ Cerrar Auditoría"): st.session_state.det_sel = None; st.rerun()

        st.plotly_chart(px.strip(df_final.dropna(subset=[col_d]), x=m['empresa'], y=col_d, color=sem_d, color_discrete_map=cmap, hover_name=m['nombre'], height=500, template="plotly_white"), use_container_width=True)

    # --- EVOLUCIÓN ---
    elif "Evolución" in st.session_state.pagina:
        if f_nom != "Todos":
            c_data = df_final.iloc[0]
            meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            vals = [float(str(c_data.iloc[i]).replace('%','').replace(',','.')) if str(c_data.iloc[i]) not in ['-','nan',''] else np.nan for i in range(15,27)]
            h1, h2 = st.columns([3, 1])
            with h1: st.title(f_nom); st.subheader(f"{c_data[m['puesto']]} | {c_data[m['empresa']]}")
            with h2: st.markdown(f'<div class="kpi-card"><h2 style="color:#27ae60;">{np.nanmean(vals):.1f}%</h2>PROM. ANUAL</div>', unsafe_allow_html=True)
            fig_e = go.Figure(go.Scatter(x=meses, y=vals, mode='lines+markers+text', line=dict(color='#3498db', width=4), text=[f"{v:.0f}%" if not np.isnan(v) else "" for v in vals], textposition="top center"))
            fig_e.add_shape(type="line", x0=0, y0=100, x1=11, y1=100, line=dict(color="green", width=2, dash="dash"))
            st.plotly_chart(fig_e.update_layout(height=500, template="plotly_white", yaxis=dict(range=[0, 165])), use_container_width=True)
        else: st.info("👈 Seleccione un colaborador para ver resultados.")

    # --- RANKING COMERCIAL (CORREGIDO) ---
    elif "Ranking Comercial" in st.session_state.pagina:
        df_r = df_com_base.copy()
        # Mapeo de meses seguro (P a AA son indices 15 a 26)
        m_map = {"Ene":15,"Feb":16,"Mar":17,"Abr":18,"May":19,"Jun":20,"Jul":21,"Ago":22,"Sep":23,"Oct":24,"Nov":25,"Dic":26,"TOTAL":27}
        c_idx = m_map[f_mes]
        
        df_r['Ops'] = pd.to_numeric(df_r.iloc[:, c_idx].astype(str).str.replace('-','0'), errors='coerce').fillna(0)
        df_r['Prom_Mes'] = pd.to_numeric(df_r.iloc[:, 34].astype(str).str.replace('-','0'), errors='coerce').fillna(0) # Col AI
        
        # Merge con Score Competencias
        df_join = pd.merge(df_r, df_raw[[m['nombre'], m['comp']]], left_on=df_r.columns[1], right_on=m['nombre'], how='left')
        
        # Filtros
        if f_emp != "Todas": df_join = df_join[df_join.iloc[:, 2] == f_emp]
        if f_nom_com: df_join = df_join[df_join.iloc[:, 1].str.contains(f_nom_com.upper())]
        
        top_10 = df_join.sort_values(by='Ops', ascending=False).head(10)
        
        if not top_10.empty:
            fig_c = go.Figure()
            fig_c.add_trace(go.Bar(x=top_10[m['nombre']], y=top_10['Ops'], name="Operaciones", marker_color='#3498db', yaxis='y1'))
            fig_c.add_trace(go.Scatter(x=top_10[m['nombre']], y=top_10[m['comp']], name="Score Comp.", line=dict(color='#e91e63', width=3), mode='lines+markers', yaxis='y2'))
            fig_c.update_layout(title=f"Top 10 - {f_mes} {f_anio}", template="plotly_white", yaxis=dict(title="Ops"), yaxis2=dict(title="Comp %", overlaying="y", side="right", range=[0,110]), legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_c, use_container_width=True)
            
            st.write("### Detalle Operativo")
            st.dataframe(top_10[[m['nombre'], df_r.columns[2], 'Ops', 'Prom_Mes', m['comp']]].rename(columns={m['nombre']:"Vendedor", 'Ops':"Total Ops", m['comp']:"Score %"}), use_container_width=True)
        else: st.warning("Sin datos.")

else: st.error("Error al conectar con la base de datos.")
