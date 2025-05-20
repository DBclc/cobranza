import streamlit as st
from conciliador import ejecutar_conciliacion_completa

st.set_page_config(page_title="Conciliador XML vs Bancos", layout="wide")
st.title("📊 Conciliación de Ingresos y Egresos en dos fases")

archivo = st.file_uploader("📂 Subir archivo Excel con hojas: Bancos, Ingresos XML, Egresos XML, Complementos", type=["xlsx"])

if archivo and st.button("🚀 Ejecutar conciliación por fases"):
    with st.spinner("Procesando conciliación en dos fases..."):
        archivo_resultado = ejecutar_conciliacion_completa(archivo)
    st.success("✅ Conciliación finalizada.")
    st.download_button("📥 Descargar conciliación final", archivo_resultado, file_name="conciliacion_final.xlsx")
