import pandas as pd
import streamlit as st

st.title("Dashboard RRHH - Grupo Cenoa")

data = pd.DataFrame({
    "Mes": ["Ene", "Feb", "Mar"],
    "Rotación": [5, 7, 6]
})

st.line_chart(data.set_index("Mes"))
