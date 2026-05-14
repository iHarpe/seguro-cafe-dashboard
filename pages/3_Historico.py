import streamlit as st
import pandas as pd
import io
from components.sidebar import render_sidebar
from utils.defaults import DEFAULT_DEPARTMENT, TRIGGER_THRESHOLD, DETECTOR_THRESHOLD
from utils.formatters import fmt_pct, fmt_pp, level_from_score
from utils.api_client import get_history
from components.charts import plot_historical_dual
from components.metric_card import render_kpi_card
from components.disclaimer import render_disclaimer

render_sidebar()

st.markdown('<div class="page-title">Análisis Histórico 2007–2024</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Backtesting del seguro: cuándo habría pagado el mecanismo de trigger y cuál fue el basis risk promedio.</div>',
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

records = history_result.get("data", {}).get("registros", [])

if not records:
    st.warning("No hay datos históricos disponibles para este departamento.")
    st.stop()

df = pd.DataFrame(records)

# ─── Summary metrics ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Resumen actuarial</div>', unsafe_allow_html=True)

total = len(df)
real_events = int((df["perdida_real_pct"] <= TRIGGER_THRESHOLD).sum()) if "perdida_real_pct" in df.columns else 0
triggered = int((df["score_anual"] <= TRIGGER_THRESHOLD).sum()) if "score_anual" in df.columns else 0

if "perdida_real_pct" in df.columns and "score_anual" in df.columns:
    basis_vals = (df["perdida_real_pct"] - df["score_anual"]).abs()
    basis_avg = float(basis_vals.mean())
else:
    basis_avg = None

freq_real = real_events / total if total else 0
recall = triggered / real_events if real_events else 0

m1, m2, m3, m4 = st.columns(4)
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
            label="Trigger activado",
            value=f"{triggered}/{total}",
            context=f"recall: {recall:.0%}",
            level="caution" if triggered > 0 else "normal",
            tooltip="Años en que el modelo habría activado el pago del seguro",
        ),
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        render_kpi_card(
            label="Basis risk promedio",
            value=fmt_pp(basis_avg) if basis_avg is not None else "—",
            context="diferencia absoluta real vs modelo",
            level="neutral",
            tooltip="Basis risk promedio = |pérdida real − predicción|. Mide el error de cobertura.",
        ),
        unsafe_allow_html=True,
    )
with m4:
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

show_only_events = st.toggle("Mostrar solo años con evento real o trigger activado", value=False)

display_df = df.copy()
if "perdida_real_pct" in display_df.columns:
    display_df["Pérdida real"] = display_df["perdida_real_pct"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
if "score_anual" in display_df.columns:
    display_df["Predicción modelo"] = display_df["score_anual"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
    display_df["Trigger activado"] = display_df["score_anual"].apply(
        lambda x: "Sí" if pd.notna(x) and x <= TRIGGER_THRESHOLD else "No"
    )
if "perdida_real_pct" in df.columns and "score_anual" in df.columns:
    display_df["Basis risk"] = (df["perdida_real_pct"] - df["score_anual"]).apply(
        lambda x: fmt_pp(x) if pd.notna(x) else "—"
    )

cols_to_show = ["anio", "Pérdida real", "Predicción modelo", "Trigger activado", "Basis risk"]
cols_available = [c for c in cols_to_show if c in display_df.columns]
display_df = display_df[cols_available].rename(columns={"anio": "Año"})

if show_only_events and "Trigger activado" in display_df.columns:
    mask = display_df["Trigger activado"] == "Sí"
    if "Pérdida real" in display_df.columns:
        mask |= display_df["Pérdida real"].str.startswith("-1") | display_df["Pérdida real"].str.startswith("-2")
    display_df = display_df[mask]

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

st.markdown(render_disclaimer("full"), unsafe_allow_html=True)
