import streamlit as st

st.set_page_config(
    page_title="Análisis Histórico — Seguro Cafetero",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
import io
from components.sidebar import render_sidebar
from utils.defaults import DEFAULT_DEPARTMENT, TRIGGER_THRESHOLD
from utils.formatters import fmt_pct
from utils.api_client import get_history
from components.charts import plot_historical_dual
from components.metric_card import render_kpi_card

render_sidebar()
st.markdown("""<style>:root {
  --page-accent: #D97706;
  --page-accent-light: #FFF7ED;
  --page-accent-border: #FCD34D;
}</style>""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
  <div class="page-accent-bar"></div>
  <div class="page-title">Análisis Histórico 2007–2024</div>
</div>
""", unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Backtesting del seguro: años en que la pérdida real de Agronet superó el umbral de trigger (−14%).</div>',
    unsafe_allow_html=True,
)

department = st.session_state.get("department", DEFAULT_DEPARTMENT)

# ─── Load historical data (cached) ───────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_history(dept: str) -> dict:
    return get_history(dept)


with st.spinner(f"Cargando histórico de {department}..."):
    history_result = load_history(department)

if not history_result["ok"]:
    st.error(
        f"No se pudo cargar el histórico: {history_result['error']}  \n"
        "Verifica que la API esté corriendo en `localhost:8000`."
    )
    st.stop()

records = history_result.get("data", [])
if isinstance(records, dict):
    records = records.get("registros", [])

if not records:
    st.warning("No hay datos históricos disponibles para este departamento.")
    st.stop()

df = pd.DataFrame(records)

# Normalise column names to what the rest of this page expects
if "perdida_rendimiento_anual_pct" in df.columns and "perdida_real_pct" not in df.columns:
    df = df.rename(columns={"perdida_rendimiento_anual_pct": "perdida_real_pct"})

# ─── Summary metrics ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Resumen actuarial</div>', unsafe_allow_html=True)

total = len(df)
real_events = int((df["perdida_real_pct"] <= TRIGGER_THRESHOLD).sum()) if "perdida_real_pct" in df.columns else 0
freq_real = real_events / total if total else 0

m1, m2 = st.columns(2)
with m1:
    st.markdown(
        render_kpi_card(
            label="Eventos reales",
            value=f"{real_events}/{total}",
            context=f"frecuencia: {freq_real:.1%}",
            level="alert" if real_events > 0 else "normal",
            tooltip="Años en que la pérdida real de Agronet superó el umbral de trigger (−14%)",
        ),
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        render_kpi_card(
            label="Período analizado",
            value="2007–2024",
            context=f"{total} años · {department}",
            level="info",
        ),
        unsafe_allow_html=True,
    )

# ─── Chart ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label" style="margin-top:16px;">Pérdida real vs predicción del modelo</div>', unsafe_allow_html=True)
fig = plot_historical_dual(df)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

# ─── Event table ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Tabla de eventos históricos</div>', unsafe_allow_html=True)

show_only_events = st.toggle("Mostrar solo años con evento real (pérdida ≤ −14%)", value=False)

display_df = df.copy()
if "perdida_real_pct" in display_df.columns:
    display_df["Pérdida real"] = display_df["perdida_real_pct"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
if "rendimiento_t_ha" in display_df.columns:
    display_df["Rendimiento (t/ha)"] = display_df["rendimiento_t_ha"].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "—")

cols_to_show = ["anio", "Pérdida real", "Rendimiento (t/ha)"]
cols_available = [c for c in cols_to_show if c in display_df.columns]
display_df = display_df[cols_available].rename(columns={"anio": "Año"})

if show_only_events and "perdida_real_pct" in df.columns:
    display_df = display_df[df["perdida_real_pct"] <= TRIGGER_THRESHOLD]

st.dataframe(display_df, use_container_width=True, hide_index=True)

# ─── Download button (R12) ────────────────────────────────────────────────────
csv_buf = io.BytesIO()
df.to_csv(csv_buf, index=False, encoding="utf-8-sig")
st.download_button(
    label="Descargar CSV histórico",
    data=csv_buf.getvalue(),
    file_name=f"historico_{department.lower()}_{2007}_{2024}.csv",
    mime="text/csv",
    help="Descarga el dataset histórico completo en formato CSV (R12)",
)

# ─── Methodology note ────────────────────────────────────────────────────────
with st.expander("Nota metodológica: períodos de entrenamiento y prueba"):
    st.markdown("""
**Área azul (2007–2020):** período de entrenamiento del modelo. Los parámetros del XGBoost y del HGB fueron ajustados con estos datos.

**Área naranja (2021–2024):** período de prueba *out-of-sample*. El modelo no vio estos años durante el entrenamiento. Las predicciones en este período reflejan la capacidad real de generalización.

**Recall del trigger:** de los eventos reales (pérdida ≥ −14%), el modelo activó el pago correctamente en ~71% de los casos.

**Basis risk:** diferencia entre la pérdida real y la predicción del modelo. Un basis risk alto significa que el seguro puede pagar en años sin pérdida real (falso positivo) o no pagar en años con pérdida (falso negativo).
""")
