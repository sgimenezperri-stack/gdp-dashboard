import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Talent Mapping Dashboard", layout="wide")

# 1. Generación de datos sintéticos (Simulando tu base de datos)
@st.cache_data
def load_data():
    data = {
        'Colaborador': [f'Empleado {i}' for i in range(1, 51)],
        'Area': np.random.choice(['Ventas', 'Postventa', 'Administración', 'IT', 'Finanzas'], 50),
        'Localidad': np.random.choice(['Salta', 'Jujuy', 'Tucumán'], 50),
        'Puesto': np.random.choice(['Asesor Comercial', 'Técnico', 'Analista', 'Gerente'], 50),
        'Desempeño': np.random.randint(1, 4, 50),  # 1: Bajo, 2: Medio, 3: Alto
        'Potencial': np.random.randint(1, 4, 50),   # 1: Bajo, 2: Medio, 3: Alto
        'Antigüedad': np.random.randint(1, 10, 50),
        'KPI_Cumplimiento': np.random.uniform(70, 110, 50)
    }
    df = pd.DataFrame(data)
    
    # Definir categorías 9-Box
    mapping = {
        (1, 1): "Talento a Observar", (1, 2): "Dilema", (1, 3): "Enigma",
        (2, 1): "Profesional Eficaz", (2, 2): "Talento Clave", (2, 3): "Estrella Emergente",
        (3, 1): "Experto/Pilar", (3, 2): "Líder en Potencia", (3, 3): "Top Talent (Estrella)"
    }
    df['Categoria'] = df.apply(lambda x: mapping[(x['Desempeño'], x['Potencial'])], axis=1)
    return df

df = load_data()

# --- SIDEBAR: Filtros ---
st.sidebar.header("Filtros de Análisis")
area_filter = st.sidebar.multiselect("Seleccionar Área", options=df['Area'].unique(), default=df['Area'].unique())
loc_filter = st.sidebar.multiselect("Localidad", options=df['Localidad'].unique(), default=df['Localidad'].unique())

df_filtered = df[(df['Area'].isin(area_filter)) & (df['Localidad'].isin(loc_filter))]

# --- HEADER: KPIs Principales ---
st.title("📊 Dashboard de Desempeño y Mapeo de Talento")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Dotación Analizada", len(df_filtered))
col2.metric("Promedio KPI %", f"{df_filtered['KPI_Cumplimiento'].mean():.1f}%")
col3.metric("Top Talentos", len(df_filtered[df_filtered['Categoria'] == 'Top Talent (Estrella)']))
col4.metric("Dilemas/Bajo Desempeño", len(df_filtered[df_filtered['Desempeño'] == 1]))

st.divider()

# --- MATRIZ 9-BOX ---
st.subheader("📍 Matriz de Talento (9-Box Grid)")

# Agregar un poco de 'jitter' para que los puntos no se encimen exactamente
df_filtered['Des_Jitter'] = df_filtered['Desempeño'] + np.random.uniform(-0.2, 0.2, len(df_filtered))
df_filtered['Pot_Jitter'] = df_filtered['Potencial'] + np.random.uniform(-0.2, 0.2, len(df_filtered))

fig = px.scatter(
    df_filtered, 
    x='Des_Jitter', 
    y='Pot_Jitter',
    color='Categoria',
    hover_name='Colaborador',
    hover_data=['Puesto', 'Area', 'KPI_Cumplimiento'],
    labels={'Des_Jitter': 'Desempeño (Bajo -> Alto)', 'Pot_Jitter': 'Potencial (Bajo -> Alto)'},
    color_discrete_sequence=px.colors.qualitative.Safe
)

# Dibujar las líneas de la cuadrícula 9-box
fig.add_vline(x=1.5, line_width=1, line_dash="dash", line_color="gray")
fig.add_vline(x=2.5, line_width=1, line_dash="dash", line_color="gray")
fig.add_hline(y=1.5, line_width=1, line_dash="dash", line_color="gray")
fig.add_hline(y=2.5, line_width=1, line_dash="dash", line_color="gray")

fig.update_layout(height=600, showlegend=True)
st.plotly_chart(fig, use_container_width=True)

# --- TABLA DE DETALLE Y ACCIÓN ---
st.subheader("🔍 Detalle de Colaboradores para Toma de Decisiones")

# Selector para ver categorías específicas (Ej: ver solo los que necesitan plan de mejora)
cat_interest = st.selectbox("Filtrar por Categoría de Talento", ["Todos"] + list(df['Categoria'].unique()))

if cat_interest != "Todos":
    display_df = df_filtered[df_filtered['Categoria'] == cat_interest]
else:
    display_df = df_filtered

st.dataframe(display_df[['Colaborador', 'Puesto', 'Area', 'KPI_Cumplimiento', 'Categoria']], use_container_width=True)

# --- RECOMENDACIONES ESTRATÉGICAS ---
with st.expander("💡 Guía de Toma de Decisiones (Acciones Recomendadas)"):
    st.markdown("""
    * **Top Talent (Estrella):** Preparar para roles de liderazgo. Asignar proyectos críticos.
    * **Líder en Potencia / Estrella Emergente:** Mentoring y capacitación técnica avanzada.
    * **Experto / Profesional Eficaz:** Mantener motivados, son el motor de la operación.
    * **Dilema / Talento a Observar:** Aplicar modelo **DMAIC** para identificar causas raíz de bajo desempeño y establecer compromisos de mejora.
    """)
