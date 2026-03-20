import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse

st.set_page_config(page_title="People Analytics | Grupo Cenoa", layout="wide")

# --- FUNCIÓN DE CARGA ---
def get_data_from_sheet(url, sheet_name):
    base_url = url.split('/edit')[0]
    sheet_name_parsed = urllib.parse.quote(sheet_name)
    csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name_parsed}"
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

# --- CONEXIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit"

@st.cache_data(ttl=60)
def load_and_clean_data():
    try:
        df = get_data_from_sheet(SHEET_URL, "DESEMPEÑO")
        
        # Mapeo de columnas
        def get_col_name(preferred_name, index):
            if preferred_name in df.columns: return preferred_name
            return df.columns[index] if len(df.columns) > index else None

        m = {
            'nombre': get_col_name('APELLIDO Y NOMBRE', 0),
            'empresa': get_col_name('EMPRESA', 2),
            'localidad': get_col_name('LOCALIDAD', 3),
            'area': get_col_name('AREA', 4),
            'puesto': get_col_name('PUESTO', 5),
            'comp': '%PUNT.EC.1°INSTANCIA COMPETENCIAS',
            'tablero': '% ACUMULADO TABLERO',
            'final': 'DESEMPEÑO'
        }
        
        # --- TRATAMIENTO DE "-" COMO DATO AUSENTE ---
        cols_a_limpiar = ['comp', 'tablero', 'final']
        for col_key in cols_a_limpiar:
            col_name = m[col_key]
            if col_name in df.columns:
                # 1. Convertimos a string para manipular
                df[col_name] = df[col_name].astype(str)
                # 2. Reemplazamos el guion "-" por un nulo real de Python (None)
                df[col_name] = df[col_name].replace('-', None)
                # 3. Limpiamos símbolos y convertimos a número
                df[col_name] = pd.to_numeric(
                    df[col_name].str.replace('%', '').str.replace(',', '.').str.strip(), 
                    errors='coerce' # Esto convierte automáticamente cualquier texto restante en NaN
                )
        
        return df, m
    except Exception as e:
        st.error(f"Error en limpieza de datos: {e}")
        return None, None

df_raw, m = load_and_clean_data()

if df_raw is not None:
    # --- SIDEBAR FILTROS ---
    st.sidebar.header("Filtros de Selección")
    
    f_empresa = st.sidebar.multiselect("Empresa", options=sorted(df_raw[m['empresa']].dropna().unique()))
    f_area = st.sidebar.multiselect("Área", options=sorted(df_raw[m['area']].dropna().unique()))
    f_puesto = st.sidebar.multiselect("Puesto", options=sorted(df_raw[m['puesto']].dropna().unique()))

    # Aplicar Filtros
    df = df_raw.copy()
    if f_empresa: df = df[df[m['empresa']].isin(f_empresa)]
    if f_area: df = df[df[m['area']].isin(f_area)]
    if f_puesto: df = df[df[m['puesto']].isin(f_puesto)]

    # --- DASHBOARD ---
    st.title("🚀 Gestión de Talento - Grupo Cenoa")
    st.info("💡 Los valores marcados como '-' en el Excel no afectan el promedio (se tratan como datos ausentes).")
    
    if not df.empty:
        # MÉTRICAS
        c1, c2, c3 = st.columns(3)
        c1.metric("Colaboradores", len(df))
        
        # El método .mean() de Pandas ignora los NaNs por defecto (no los cuenta en el divisor)
        prom_comp = df[m['comp']].mean()
        c2.metric("Prom. Competencias", f"{prom_comp:.1f}%" if pd.notnull(prom_comp) else "N/A")
        
        prom_tab = df[m['tablero']].mean()
        c3.metric("Prom. Tablero", f"{prom_tab:.1f}%" if pd.notnull(prom_tab) else "N/A")

        st.divider()

        # --- MATRIZ DE DESEMPEÑO ---
        st.subheader("Visualización Estratégica")
        
        # Solo graficamos los que tengan AMBAS notas (Competencias y Tablero)
        df_plot = df.dropna(subset=[m['comp'], m['tablero']])
        
        if not df_plot.empty:
            fig = px.scatter(
                df_plot, x=m['comp'], y=m['tablero'],
                color=m['area'], hover_name=m['nombre'],
                size=df_plot[m['final']].fillna(df_plot[m['final']].mean()), # Tamaño basado en desempeño
                labels={m['comp']: "Competencias %", m['tablero']: "Tablero %"},
                title="Distribución de Talento (Ignorando datos ausentes)"
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red")
            fig.add_vline(x=70, line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay suficientes datos completos para generar el gráfico de dispersión.")

        # --- TABLA CON FORMATO ---
        st.subheader("Listado de Colaboradores")
        # Mostramos los datos, pero los nulos aparecerán como NaN o vacíos
        st.dataframe(
            df[[m['nombre'], m['area'], m['puesto'], m['final']]]
            .sort_values(by=m['final'], ascending=False),
            use_container_width=True
        )
    else:
        st.info("Selecciona criterios en los filtros para analizar la dotación.")
