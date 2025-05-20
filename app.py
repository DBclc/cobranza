import streamlit as st
import pandas as pd
from conciliador import procesar_conciliacion_completa

st.set_page_config(page_title="Conciliador SAT-Bancos", layout="wide")
st.title("🤖 Agente de Conciliación de Ingresos, Egresos y Bancos")

with st.expander("📂 Subir archivos requeridos"):
    bancos_file = st.file_uploader("🧾 Estado de cuenta bancario (Excel)", type=["xlsx"], key="bancos")
    ingresos_file = st.file_uploader("📥 XMLs de ingresos SAT (ZIP)", type=["zip"], key="ingresos")
    egresos_file = st.file_uploader("📤 XMLs de egresos SAT (ZIP)", type=["zip"], key="egresos")
    complementos_file = st.file_uploader("📄 Complementos de pago (Excel)", type=["xlsx"], key="complementos")

if st.button("🚀 Iniciar proceso completo de conciliación"):
    if bancos_file and ingresos_file and egresos_file and complementos_file:
        with st.spinner("Procesando conciliación completa..."):
            output = procesar_conciliacion_completa(
                bancos_file=bancos_file,
                ingresos_zip=ingresos_file,
                egresos_zip=egresos_file,
                complementos_file=complementos_file,
                anio="2024"
            )
        st.success("✅ Conciliación completada.")
        st.download_button(
            label="📥 Descargar archivo conciliado",
            data=output,
            file_name="conciliacion_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("🔺 Por favor, sube todos los archivos requeridos.")