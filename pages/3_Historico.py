import streamlit as st

st.set_page_config(
    page_title="Analisis Historico -- Seguro Cafetero",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

import io
import pandas as pd
from components.sidebar import render_sidebar
from utils.defaults import DEFAULT_DEPARTMENT, TRIGGER_THRESHOLD
from utils.formatters import fmt_pct, fmt_pp, fmt_recall_pct
from utils.api_client import get_history, get_backtest, get_calibration
from components.charts import plot_historical_dual, plot_historical_triple
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
  <div class="page-title">Analisis Historico 2007-2024</div>
</div>
""", unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Backtesting del seguro parametrico: comparacion de pagos del modelo vs perdidas reales de Agronet.</div>',
    unsafe_allow_html=True,
)
st.caption("Granularidad: departamental (no municipal). Los datos satelitales se agregan por media zonal a nivel de departamento. Ver Metodologia > Limitaciones.")

department = st.session_state.get("department", DEFAULT_DEPARTMENT)

# --- Threshold selector ---
threshold = st.slider(
    "Umbral de trigger (%)",
    min_value=-25, max_value=5, value=int(TRIGGER_THRESHOLD), step=1,
    help="Umbral a partir del cual el seguro activa el pago",
)


@st.cache_data(ttl=3600)
def load_backtest_data(dept: str, umbral: float):
    return get_backtest(dept, umbral)


@st.cache_data(ttl=3600)
def load_history_data(dept: str):
    return get_history(dept)


@st.cache_data(ttl=3600)
def load_calibration():
    return get_calibration()


# --- Load data ---
with st.spinner(f"Cargando backtest de {department}..."):
    bt_result = load_backtest_data(department, threshold)
    hist_result = load_history_data(department)
    cal_result = load_calibration()

if not bt_result["ok"]:
    st.error(f"No se pudo cargar el backtest: {bt_result['error']}")
    st.stop()

bt_df = pd.DataFrame(bt_result["data"])
if bt_df.empty:
    st.warning("No hay datos de backtest disponibles.")
    st.stop()

# --- Summary KPIs ---
st.markdown('<div class="section-label">Resumen actuarial</div>', unsafe_allow_html=True)

n_events = int(bt_df["evento_real"].sum())
n_triggered = int(bt_df["trigger_activado"].sum())
tp = int((bt_df["evento_real"] & bt_df["trigger_activado"]).sum())
recall = tp / n_events if n_events > 0 else 0
active = bt_df["evento_real"] | bt_df["trigger_activado"]
br_pp = bt_df.loc[active, "basis_risk_pp"].abs().mean() if active.sum() > 0 else 0
br_usd = bt_df.loc[active, "basis_risk_usd_k"].abs().mean() if active.sum() > 0 else 0

avg_event_loss = bt_df.loc[bt_df["evento_real"], "perdida_real_pct"].abs().mean() if n_events > 0 else 0
reduction = (avg_event_loss - br_pp) / avg_event_loss * 100 if avg_event_loss > 0 else 0

m1, m2, m3, m4 = st.columns(4)
with m1:
    br_level = "normal" if br_pp <= 8 else "caution" if br_pp <= 12 else "alert"
    st.markdown(render_kpi_card(
        label="Basis risk promedio",
        value=f"{br_pp:.1f} pp",
        context=f"sobre {active.sum()} años activos",
        level=br_level,
        tooltip="Diferencia media absoluta entre pago del seguro y perdida real",
    ), unsafe_allow_html=True)
with m2:
    st.markdown(render_kpi_card(
        label="Basis risk (USD)",
        value=f"USD {br_usd:.1f}k",
        context="promedio por departamento-año",
        level=br_level,
    ), unsafe_allow_html=True)
with m3:
    st.markdown(render_kpi_card(
        label="Reduccion vs sin seguro",
        value=f"{reduction:.0f}%",
        context=f"severidad media eventos: {avg_event_loss:.1f} pp",
        level="normal" if reduction > 50 else "caution",
    ), unsafe_allow_html=True)
with m4:
    recall_level = "normal" if recall >= 0.70 else "caution" if recall >= 0.50 else "alert"
    st.markdown(render_kpi_card(
        label="Recall de eventos",
        value=fmt_recall_pct(recall),
        context=f"{tp}/{n_events} eventos detectados",
        level=recall_level,
        tooltip="Fraccion de eventos reales donde el trigger se activo correctamente",
    ), unsafe_allow_html=True)

# --- Chart: Real vs Prediction ---
st.markdown('<div class="section-label" style="margin-top:16px;">Perdida real vs prediccion del modelo</div>', unsafe_allow_html=True)

if hist_result["ok"]:
    hist_records = hist_result.get("data", [])
    hist_df = pd.DataFrame(hist_records)
    if "perdida_rendimiento_anual_pct" in hist_df.columns:
        hist_df = hist_df.rename(columns={"perdida_rendimiento_anual_pct": "perdida_real_pct"})
    fig_dual = plot_historical_dual(hist_df)
    st.plotly_chart(fig_dual, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

# --- Chart: 3-series comparison ---
st.markdown('<div class="section-label" style="margin-top:16px;">Pago del seguro vs perdida real</div>', unsafe_allow_html=True)
fig_triple = plot_historical_triple(bt_df)
st.plotly_chart(fig_triple, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

# --- Calibration table ---
if cal_result["ok"]:
    with st.expander("Tabla comparativa de configuraciones del trigger"):
        cal_df = pd.DataFrame(cal_result["data"])
        highlight = [int(TRIGGER_THRESHOLD), -15, -11, -3, 0]
        key_configs = cal_df[cal_df["threshold_pct"].isin(highlight)].copy()
        if key_configs.empty:
            key_configs = cal_df.head(10)
        display_cal = key_configs[["threshold_pct", "recall", "precision", "f1",
                                    "basis_risk_medio_pp", "n_actual_events",
                                    "n_predicted_events"]].copy()
        display_cal.columns = ["Umbral (%)", "Recall", "Precision", "F1",
                               "BR medio (pp)", "Eventos reales", "Eventos predichos"]
        st.dataframe(display_cal, use_container_width=True, hide_index=True)

# --- Event table ---
st.markdown('<div class="section-label">Tabla de eventos historicos</div>', unsafe_allow_html=True)
show_only_events = st.toggle("Mostrar solo años con evento real o trigger activo", value=False)

display_df = bt_df.copy()
display_df["Perdida real"] = display_df["perdida_real_pct"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "---")
display_df["Prediccion M3"] = display_df["prediccion_m3_pct"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "---")
display_df["Pago (pp)"] = display_df["pago_pp"].apply(lambda x: f"{x:.1f}" if x > 0 else "---")
display_df["Basis risk"] = display_df["basis_risk_pp"].apply(lambda x: f"{x:+.1f} pp" if pd.notna(x) else "---")
display_df["Evento"] = display_df["evento_real"].map({True: "Si", False: "No"})
display_df["Trigger"] = display_df["trigger_activado"].map({True: "Activado", False: "---"})
display_df["Split"] = display_df["split"]

cols_show = ["anio", "Perdida real", "Prediccion M3", "Evento", "Trigger", "Pago (pp)", "Basis risk", "Split"]
table_df = display_df[cols_show].rename(columns={"anio": "Año"})

if show_only_events:
    mask = bt_df["evento_real"] | bt_df["trigger_activado"]
    table_df = table_df[mask.values]

st.dataframe(table_df, use_container_width=True, hide_index=True)

# --- CSV download (extended schema) ---
csv_buf = io.BytesIO()
export_cols = ["anio", "departamento", "umbral_pct", "perdida_real_pct",
               "prediccion_m1_pct", "prediccion_m3_pct", "evento_real",
               "trigger_activado", "pago_pp", "basis_risk_pp",
               "pago_usd_k", "basis_risk_usd_k", "split"]
export_df = bt_df[[c for c in export_cols if c in bt_df.columns]]
export_df.to_csv(csv_buf, index=False, encoding="utf-8-sig")
st.download_button(
    label="Descargar CSV backtest completo",
    data=csv_buf.getvalue(),
    file_name=f"backtest_{department.lower()}_umbral{threshold}pct.csv",
    mime="text/csv",
    help="Dataset de backtest con 12 columnas (R12)",
)

# --- Methodology note ---
with st.expander("Nota metodologica"):
    st.markdown(f"""
**Umbral seleccionado:** {threshold}% | **Departamento:** {department}

**Area azul (2007-2020):** periodo de entrenamiento. Las predicciones en este rango son in-sample.

**Area naranja (2021-2024):** periodo de prueba out-of-sample.

**Recall del trigger:** de los {n_events} eventos reales, el modelo activo el pago correctamente en {tp} ({recall:.0%}).

**Basis risk:** diferencia entre pago del seguro y perdida real. Un valor negativo indica que el seguro pago menos que la perdida (sub-cobertura).
""")
