import streamlit as st

st.set_page_config(
    page_title="Score Mensual -- Seguro Cafetero",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
from components.sidebar import render_sidebar
from utils.defaults import (
    DEFAULT_DEPARTMENT, DETECTOR_THRESHOLD, TRIGGER_THRESHOLD,
    MODEL_MAE_MONTHLY_ANNUALIZED,
)
from utils.formatters import fmt_pct, level_from_score
from utils.api_client import get_monthly_history, get_history
from components.charts import plot_monthly_history_full
from components.metric_card import render_kpi_card

MONTH_NAMES = {
    1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
    7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic",
}

render_sidebar()
st.markdown("""<style>:root {
  --page-accent: #BE185D;
  --page-accent-light: #FDF2F8;
  --page-accent-border: #F9A8D4;
}</style>""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
  <div class="page-accent-bar"></div>
  <div class="page-title">Score Mensual (M4)</div>
</div>
""", unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Trayectoria historica del modelo mensual de alerta temprana. Compara la senal M4 con la perdida anual real.</div>',
    unsafe_allow_html=True,
)

department = st.session_state.get("department", DEFAULT_DEPARTMENT)


@st.cache_data(ttl=3600)
def load_monthly(dept: str):
    return get_monthly_history(dept)


@st.cache_data(ttl=3600)
def load_annual(dept: str):
    return get_history(dept)


# ─── Load data ───────────────────────────────────────────────────────────────
monthly_result = load_monthly(department)
annual_result = load_annual(department)

if not monthly_result["ok"]:
    st.error(f"No se pudo cargar el historial mensual: {monthly_result['error']}")
    st.stop()

monthly_df = pd.DataFrame(monthly_result["data"])
if monthly_df.empty or "score_m4" not in monthly_df.columns:
    st.warning("Sin datos de score mensual disponibles.")
    st.stop()

dept_df = monthly_df[monthly_df["departamento"] == department].copy()
if dept_df.empty:
    dept_df = monthly_df.copy()

# ─── KPIs ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Resumen</div>', unsafe_allow_html=True)

valid_df = dept_df.dropna(subset=["score_m4"]).sort_values(["anio", "mes"])

PERIOD_OPTIONS = {"Últimos 12 meses": 12, "Últimos 24 meses": 24, "Últimos 36 meses": 36, "Todo el historial": 0}
col_period, _ = st.columns([2, 4])
with col_period:
    period_label = st.selectbox("Periodo para promedio", list(PERIOD_OPTIONS.keys()), index=0, label_visibility="collapsed")
n_period = PERIOD_OPTIONS[period_label]
window_df = valid_df.tail(n_period) if n_period > 0 else valid_df
avg_score = window_df["score_m4"].mean() if not window_df.empty else None

min_score = valid_df["score_m4"].min() if not valid_df.empty else None
min_row = valid_df.loc[valid_df["score_m4"].idxmin()] if not valid_df.empty else None
n_alerts = int((valid_df["score_m4"] <= DETECTOR_THRESHOLD).sum())
n_total = len(valid_df)

k1, k2, k3, k4 = st.columns(4)
with k1:
    n_actual = len(window_df)
    st.markdown(render_kpi_card(
        label=f"Score promedio ({period_label.lower()})",
        value=fmt_pct(avg_score),
        context=f"{n_actual} meses con dato · MAE: {MODEL_MAE_MONTHLY_ANNUALIZED} pp",
        level=level_from_score(avg_score),
    ), unsafe_allow_html=True)
with k2:
    min_context = (
        f"{MONTH_NAMES.get(int(min_row['mes']), '?')} {int(min_row['anio'])}"
        if min_row is not None else "—"
    )
    st.markdown(render_kpi_card(
        label="Score minimo historico",
        value=fmt_pct(min_score),
        context=min_context,
        level=level_from_score(min_score),
    ), unsafe_allow_html=True)
with k3:
    alert_pct = n_alerts / n_total * 100 if n_total > 0 else 0
    st.markdown(render_kpi_card(
        label="Meses con alerta",
        value=f"{n_alerts}",
        context=f"{alert_pct:.0f}% de {n_total} meses",
        level="caution" if alert_pct > 10 else "normal",
    ), unsafe_allow_html=True)
with k4:
    st.markdown(render_kpi_card(
        label="Departamento",
        value=department,
        context=f"{dept_df['anio'].min()}-{dept_df['anio'].max()}",
        level="info",
    ), unsafe_allow_html=True)

# ─── M4 trajectory chart ────────────────────────────────────────────────────
st.markdown('<div class="section-label" style="margin-top:16px;">Trayectoria M4</div>', unsafe_allow_html=True)

fig = plot_monthly_history_full(monthly_df)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

# ─── Last 12 months table ───────────────────────────────────────────────────
st.markdown('<div class="section-label" style="margin-top:16px;">Ultimos 12 meses con dato</div>', unsafe_allow_html=True)

last_12 = valid_df.tail(12)
display_12 = last_12.copy()
display_12["Mes"] = display_12["mes"].map(MONTH_NAMES)
display_12["Ano"] = display_12["anio"].astype(int)
display_12["Score M4"] = display_12["score_m4"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "---")
display_12["Alerta"] = display_12["score_m4"].apply(
    lambda x: "Si" if x <= DETECTOR_THRESHOLD else "No"
)
display_12["Trigger"] = display_12["score_m4"].apply(
    lambda x: "Activado" if x <= TRIGGER_THRESHOLD else "---"
)
st.dataframe(
    display_12[["Ano", "Mes", "Score M4", "Alerta", "Trigger"]],
    use_container_width=True, hide_index=True,
)

# ─── M4 vs M1 comparison ────────────────────────────────────────────────────
st.markdown('<div class="section-label" style="margin-top:16px;">Comparacion M4 (mensual) vs M1 (anual)</div>', unsafe_allow_html=True)

annual_avg = valid_df.groupby("anio")["score_m4"].mean().reset_index()
annual_avg.columns = ["anio", "m4_promedio_anual"]

if annual_result["ok"]:
    annual_records = annual_result.get("data", [])
    annual_df = pd.DataFrame(annual_records)
    if "perdida_rendimiento_anual_pct" in annual_df.columns:
        annual_df = annual_df.rename(columns={"perdida_rendimiento_anual_pct": "perdida_real_pct"})

    pred_col = next((c for c in ("prediccion_m1_pct", "score_anual") if c in annual_df.columns), None)

    if pred_col:
        merged = annual_avg.merge(
            annual_df[["anio", pred_col, "perdida_real_pct"]],
            on="anio", how="inner",
        )
        if not merged.empty:
            merged["M4 promedio"] = merged["m4_promedio_anual"].apply(lambda x: f"{x:+.1f}%")
            merged[f"M1 prediccion"] = merged[pred_col].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "---")
            merged["Perdida real"] = merged["perdida_real_pct"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "---")
            merged["Ano"] = merged["anio"].astype(int)
            st.dataframe(
                merged[["Ano", "M4 promedio", "M1 prediccion", "Perdida real"]],
                use_container_width=True, hide_index=True,
            )

            st.caption(
                "M4 promedio: media aritmetica de los scores mensuales del ano. "
                "M1: prediccion anual del modelo XGBoost. "
                "Perdida real: variacion de rendimiento reportada por Agronet."
            )
        else:
            st.info("No hay datos anuales para comparar.")
    else:
        st.info("No se encontro la columna de prediccion M1 en los datos anuales.")
else:
    st.warning(f"No se pudo cargar el historial anual: {annual_result['error']}")
