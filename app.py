import streamlit as st
from conciliador import procesar_conciliacion_completa

st.set_page_config(page_title="Conciliador SAT-Bancos", layout="wide")
st.title("🤖 Conciliación completa: Ingresos, Egresos y Complementos")

archivo = st.file_uploader("📂 Subir archivo Excel con 5 hojas", type=["xlsx"])

if archivo and st.button("🚀 Ejecutar conciliación"):
    with st.spinner("Procesando conciliación robusta..."):
        archivo_resultado = procesar_conciliacion_completa(archivo)
    st.success("✅ Conciliación finalizada.")
    st.download_button("📥 Descargar resultado", archivo_resultado, file_name="conciliacion_final.xlsx")
