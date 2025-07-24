import streamlit as st
import pandas as pd
from pyathena import connect
import seaborn as sns
import matplotlib.pyplot as plt


st.title("Análisis de Consumo y Comercio en Chile")
st.markdown("Conectado a AWS Athena – datos desde S3")

# Conexión a Athena
@st.cache_data
def run_query(query):
    conn = connect(
        aws_access_key_id=st.secrets["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws_secret_access_key"],
        s3_staging_dir=st.secrets["s3_staging_dir"],
        region_name=st.secrets["aws_region"]
    )
    cursor = conn.cursor()
    cursor.execute(query)
    df = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    return df

# Consulta de ejemplo (ajústala a tu tabla real)
query = """
SELECT *
FROM retail_chile.iac_completo
"""

query_sii_tramos = """
SELECT *
FROM retail_chile.empresas_tramos_clean
"""

# Carga de datos
df = run_query(query)
df_sii_tramos = run_query(query_sii_tramos)

#Limpieza 
df["venta_total"] = pd.to_numeric(df["venta_total"], errors="coerce")
df.dropna(subset=["venta_total"], inplace=True)
df["mes"] = df["mes"].astype(int)
df["anio"] = df["anio"].astype(int)
df["periodo"] = df["anio"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)

# Sidebar
st.sidebar.title("Filtros")
años = sorted(df["anio"].unique())
año_seleccionado = st.sidebar.selectbox("Selecciona año", años)

meses = df[df["anio"] == año_seleccionado]["mes"].unique()
mes_seleccionado = st.sidebar.selectbox("Selecciona mes", sorted(meses))

df_filtrado = df[(df["anio"] == año_seleccionado) & (df["mes"] == mes_seleccionado)]

# --- KPI principales ---
st.title("📊 Dashboard Retail Chile")
col1, col2 = st.columns(2)
col1.metric("Ventas Totales", f"${df_filtrado['venta_total'].sum():,.0f}")
col2.metric("Transacciones", f"{len(df_filtrado)} registros")

# --- Gráfico línea: evolución mensual ---
st.subheader("Evolución de ventas por mes")
ventas_mensuales = (
    df.groupby(["anio", "mes"])["venta_total"].sum().reset_index()
)
ventas_mensuales["periodo"] = ventas_mensuales["anio"].astype(str) + "-" + ventas_mensuales["mes"].astype(str).str.zfill(2)
st.line_chart(ventas_mensuales.set_index("periodo")["venta_total"])

# --- Gráfico barras: categorías ---
st.subheader("Distribución de ventas por categoría")
categorias = [
    "combustible", "alimentos", "bebida_tabaco", "farmacia_costetico_higiene",
    "vestuario_calzados_acc", "electronicos_hogar_tecno", "materiales_constru",
    "bienes_consumo_diverso", "repuestos_auto"
]

df_categorias = df_filtrado[categorias].sum().sort_values(ascending=False)
st.bar_chart(df_categorias)

# --- Muestra tabla final ---
st.subheader("Vista de datos filtrados")
st.dataframe(df_filtrado)

st.title("📊 Dashboard de Ventas y Empleo - SII por Región")
# Filtros
anios = sorted(df_sii_tramos['anio_comercial'].unique())
regiones = df_sii_tramos['id_region'].unique()

anio_seleccionado = st.selectbox("Selecciona Año Comercial", anios)
region_seleccionada = st.selectbox("Selecciona Región", regiones)

# Filtrar DataFrame
df_sii_tramos_filtrado = df_sii_tramos[
    (df_sii_tramos["anio_comercial"] == anio_seleccionado) &
    (df_sii_tramos["id_region"] == region_seleccionada)
]

st.subheader(f"Resumen {region_seleccionada} - {anio_seleccionado}")

col1, col2, col3 = st.columns(3)
col1.metric("Empresas", int(df_sii_tramos_filtrado["num_empresas"].sum()))
col2.metric("Trabajadores", int(df_sii_tramos_filtrado["num_trabajadores_dependientes"].sum()))
col3.metric("Ventas (UF)", round(df_sii_tramos_filtrado["ventas_uf"].sum(), 2))

# Gráfico: Trabajadores por Tramo
st.subheader("📈 Trabajadores por Tramo")
fig, ax = plt.subplots()
sns.barplot(data=df_sii_tramos_filtrado, x="id_tramo", y="num_trabajadores_dependientes", ax=ax)
plt.xticks(rotation=45)
st.pyplot(fig)