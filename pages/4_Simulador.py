import streamlit as st

st.set_page_config(
    page_title="Simulador Actuarial -- Seguro Cafetero",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
import numpy as np
from components.sidebar import render_sidebar
from utils.defaults import DEFAULT_DEPARTMENT, TRIGGER_THRESHOLD, DETECTOR_THRESHOLD
from utils.formatters import fmt_pct, fmt_pp
from utils.api_client import get_backtest, get_calibration
from components.charts import plot_calibration_curves, plot_tradeoff_scatter
from components.metric_card import render_kpi_card

render_sidebar()
st.markdown("""<style>:root {
  --page-accent: #7C3AED;
  --page-accent-light: #F5F3FF;
  --page-accent-border: #C4B5FD;
}</style>""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
  <div class="page-accent-bar"></div>
  <div class="page-title">Simulador Actuarial</div>
</div>
""", unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Configura los parametros del seguro y evalua el trade-off entre cobertura, costo y riesgo residual.</div>',
    unsafe_allow_html=True,
)

LOSS_THRESHOLD = -15.0


# --- Data loading (cached) ---
@st.cache_data(ttl=3600)
def load_backtest_all():
    return get_backtest()


@st.cache_data(ttl=3600)
def load_calibration_data():
    return get_calibration()


bt_result = load_backtest_all()
cal_result = load_calibration_data()

if not bt_result["ok"]:
    st.error(f"No se pudo cargar el backtest: {bt_result['error']}")
    st.stop()
if not cal_result["ok"]:
    st.error(f"No se pudo cargar la calibracion: {cal_result['error']}")
    st.stop()

bt_all = pd.DataFrame(bt_result["data"])
cal_all = cal_result["data"]

# --- Controls ---
controls_col, results_col = st.columns([1, 2], gap="large")

with controls_col:
    st.markdown('<div class="section-label">Parametros del seguro</div>', unsafe_allow_html=True)

    threshold = st.slider(
        "Umbral de trigger (%)",
        min_value=-25, max_value=5, value=int(TRIGGER_THRESHOLD), step=1,
        help="Perdida predicha a partir de la cual el seguro paga",
    )
    coverage = st.slider(
        "Cobertura (%)",
        min_value=30, max_value=100, value=70, step=5,
        help="Porcentaje de la perdida predicha que el seguro cubre",
    )
    loading_factor = st.slider(
        "Factor de carga (loading)",
        min_value=0.10, max_value=0.50, value=0.30, step=0.05,
        format="%.2f",
        help="Recargo sobre la prima pura para gastos administrativos y utilidad",
    )
    depto_option = st.selectbox(
        "Departamento",
        options=["Promedio", "Risaralda", "Cundinamarca"],
        index=0,
    )

# --- Compute metrics ---
bt = bt_all[bt_all["umbral_pct"] == threshold].copy()
if depto_option != "Promedio":
    bt = bt[bt["departamento"] == depto_option]

if bt.empty:
    with results_col:
        st.warning("No hay datos para esta configuracion.")
    st.stop()

# Apply coverage to payouts
coverage_frac = coverage / 100.0
bt["pago_adj_pp"] = bt["pago_pp"] * coverage_frac
bt["basis_risk_adj_pp"] = bt["pago_adj_pp"] + bt["perdida_real_pct"]

# Recall/precision from events (coverage doesn't affect trigger logic)
n_events = int(bt["evento_real"].sum())
n_triggered = int(bt["trigger_activado"].sum())
tp = int((bt["evento_real"] & bt["trigger_activado"]).sum())
recall = tp / n_events if n_events > 0 else None
precision = tp / n_triggered if n_triggered > 0 else None
f1 = None
if recall is not None and precision is not None and (recall + precision) > 0:
    f1 = 2 * recall * precision / (recall + precision)

active = bt["evento_real"] | bt["trigger_activado"]
br_pp = bt.loc[active, "basis_risk_adj_pp"].abs().mean() if active.sum() > 0 else 0

# Premium calculation
pure_premium_pp = bt["pago_adj_pp"].mean()
commercial_premium_pp = pure_premium_pp * (1 + loading_factor)

# USD/ha conversion (using dataset averages)
avg_yield = bt["rendimiento_t_ha"].mean()
avg_price = bt["precio_ico_usd_ton"].mean()
premium_usd_ha = commercial_premium_pp / 100 * avg_yield * avg_price if avg_yield > 0 else 0
gross_income_usd_ha = avg_yield * avg_price
premium_pct_income = (premium_usd_ha / gross_income_usd_ha * 100) if gross_income_usd_ha > 0 else 0

# --- Display KPIs ---
with results_col:
    st.markdown('<div class="section-label">Indicadores del seguro</div>', unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)
    with k1:
        br_level = "normal" if br_pp <= 8 else "caution" if br_pp <= 12 else "alert"
        st.markdown(render_kpi_card(
            label="Basis risk promedio",
            value=f"{br_pp:.1f} pp",
            context=f"cobertura {coverage}%",
            level=br_level,
        ), unsafe_allow_html=True)
    with k2:
        r_level = "normal" if (recall or 0) >= 0.70 else "caution" if (recall or 0) >= 0.50 else "alert"
        st.markdown(render_kpi_card(
            label="Recall de eventos",
            value=f"{recall*100:.0f}%" if recall is not None else "---",
            context=f"{tp}/{n_events} detectados",
            level=r_level,
        ), unsafe_allow_html=True)
    with k3:
        p_level = "normal" if (precision or 0) >= 0.70 else "caution" if (precision or 0) >= 0.50 else "alert"
        st.markdown(render_kpi_card(
            label="Precision",
            value=f"{precision*100:.0f}%" if precision is not None else "---",
            context=f"{tp}/{n_triggered} correctos",
            level=p_level,
        ), unsafe_allow_html=True)

    k4, k5, k6 = st.columns(3)
    with k4:
        prem_level = "normal" if 30 <= premium_usd_ha <= 80 else "caution" if premium_usd_ha <= 120 else "alert"
        st.markdown(render_kpi_card(
            label="Prima estimada",
            value=f"USD {premium_usd_ha:.0f}/ha/año",
            context=f"pura: {pure_premium_pp:.2f} pp + loading {loading_factor:.0%}",
            level=prem_level,
        ), unsafe_allow_html=True)
    with k5:
        pct_level = "normal" if premium_pct_income <= 5 else "caution" if premium_pct_income <= 8 else "alert"
        st.markdown(render_kpi_card(
            label="Prima / ingreso bruto",
            value=f"{premium_pct_income:.1f}%",
            context=f"ingreso ref: USD {gross_income_usd_ha:.0f}/ha",
            level=pct_level,
        ), unsafe_allow_html=True)
    with k6:
        st.markdown(render_kpi_card(
            label="F1-Score",
            value=f"{f1:.2f}" if f1 is not None else "---",
            context="balance recall-precision",
            level="normal" if (f1 or 0) >= 0.70 else "caution",
        ), unsafe_allow_html=True)

    # --- Charts ---
    st.markdown('<div class="section-label" style="margin-top:16px;">Analisis de sensibilidad</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Sensibilidad por umbral", "Trade-off recall vs basis risk"])

    with tab1:
        fig_cal = plot_calibration_curves(cal_all)
        fig_cal.add_vline(x=threshold, line_dash="dot", line_color="#7C3AED", line_width=2,
                          annotation_text=f"Actual: {threshold}%",
                          annotation_font_color="#7C3AED")
        st.plotly_chart(fig_cal, use_container_width=True, config={"displayModeBar": False})

    with tab2:
        fig_trade = plot_tradeoff_scatter(cal_all, current_thr=float(threshold))
        st.plotly_chart(fig_trade, use_container_width=True, config={"displayModeBar": False})

    # --- Robustness table ---
    with st.expander("Tabla de robustez"):
        st.markdown("Variacion de prima y basis risk ante cambios en parametros:")
        robustness_rows = []
        for thr_delta in [-2, -1, 0, 1, 2]:
            for load_delta in [-0.10, 0, 0.10]:
                t = threshold + thr_delta
                l = loading_factor + load_delta
                if t < -25 or t > 5 or l < 0.05:
                    continue
                bt_r = bt_all[bt_all["umbral_pct"] == t].copy()
                if depto_option != "Promedio":
                    bt_r = bt_r[bt_r["departamento"] == depto_option]
                if bt_r.empty:
                    continue
                bt_r["pago_adj"] = bt_r["pago_pp"] * coverage_frac
                pp = bt_r["pago_adj"].mean() * (1 + l)
                act = bt_r["evento_real"] | bt_r["trigger_activado"]
                br_r = (bt_r.loc[act, "basis_risk_pp"].abs().mean() * coverage_frac) if act.sum() > 0 else 0
                robustness_rows.append({
                    "Umbral (%)": t,
                    "Loading": f"{l:.2f}",
                    "Prima (pp)": f"{pp:.2f}",
                    "BR (pp)": f"{br_r:.1f}",
                })
        if robustness_rows:
            st.dataframe(pd.DataFrame(robustness_rows), use_container_width=True, hide_index=True)

    # --- Summary text ---
    st.markdown(f"""
    > **Resumen:** Umbral **{threshold}%**, cobertura **{coverage}%**, loading **{loading_factor:.0%}**
    > — recall **{recall*100:.0f}%** {"" if recall is None else ""}, basis risk **{br_pp:.1f} pp**,
    > prima **USD {premium_usd_ha:.0f}/ha** ({premium_pct_income:.1f}% del ingreso bruto).
    """)

    # --- Apply & Compare buttons ---
    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button("Aplicar como configuracion operativa", type="primary", use_container_width=True):
            st.session_state["prev_config"] = {
                "Umbral (%)": st.session_state.get("trigger_threshold", int(TRIGGER_THRESHOLD)),
                "Cobertura (%)": st.session_state.get("sim_coverage", 70),
                "Loading": st.session_state.get("sim_loading", 0.30),
            }
            st.session_state["trigger_threshold"] = threshold
            st.session_state["sim_coverage"] = coverage
            st.session_state["sim_loading"] = loading_factor
            st.success(f"Umbral operativo actualizado a {threshold}%")

    with btn2:
        compare_clicked = st.button("Comparar configuraciones", use_container_width=True)

    if compare_clicked:
        prev = st.session_state.get("prev_config")
        if prev is None:
            st.info("Aplica primero una configuracion para poder comparar con la siguiente.")
        else:
            curr = {
                "Umbral (%)": threshold,
                "Cobertura (%)": coverage,
                "Loading": loading_factor,
            }
            curr["Recall"] = f"{recall*100:.0f}%" if recall is not None else "---"
            curr["BR (pp)"] = f"{br_pp:.1f}"
            curr["Prima (USD/ha)"] = f"{premium_usd_ha:.0f}"
            curr["Prima/ingreso"] = f"{premium_pct_income:.1f}%"

            prev_thr = prev["Umbral (%)"]
            prev_cov = prev["Cobertura (%)"]
            prev_load = prev["Loading"]
            bt_prev = bt_all[bt_all["umbral_pct"] == prev_thr].copy()
            if depto_option != "Promedio":
                bt_prev = bt_prev[bt_prev["departamento"] == depto_option]
            if not bt_prev.empty:
                cov_p = prev_cov / 100.0
                bt_prev["pago_adj_pp"] = bt_prev["pago_pp"] * cov_p
                bt_prev["br_adj"] = bt_prev["pago_adj_pp"] + bt_prev["perdida_real_pct"]
                p_n_ev = int(bt_prev["evento_real"].sum())
                p_tp = int((bt_prev["evento_real"] & bt_prev["trigger_activado"]).sum())
                p_recall = p_tp / p_n_ev if p_n_ev > 0 else 0
                p_active = bt_prev["evento_real"] | bt_prev["trigger_activado"]
                p_br = bt_prev.loc[p_active, "br_adj"].abs().mean() if p_active.sum() > 0 else 0
                p_pp = bt_prev["pago_adj_pp"].mean() * (1 + prev_load)
                p_yield = bt_prev["rendimiento_t_ha"].mean()
                p_price = bt_prev["precio_ico_usd_ton"].mean()
                p_usd = p_pp / 100 * p_yield * p_price if p_yield > 0 else 0
                p_gross = p_yield * p_price
                p_pct = (p_usd / p_gross * 100) if p_gross > 0 else 0
                prev["Recall"] = f"{p_recall*100:.0f}%"
                prev["BR (pp)"] = f"{p_br:.1f}"
                prev["Prima (USD/ha)"] = f"{p_usd:.0f}"
                prev["Prima/ingreso"] = f"{p_pct:.1f}%"
            else:
                prev["Recall"] = "---"
                prev["BR (pp)"] = "---"
                prev["Prima (USD/ha)"] = "---"
                prev["Prima/ingreso"] = "---"

            cmp_df = pd.DataFrame({"Metrica": list(curr.keys()), "Anterior": [prev.get(k, "---") for k in curr], "Actual": list(curr.values())})
            st.markdown('<div class="section-label" style="margin-top:12px;">Comparacion de configuraciones</div>', unsafe_allow_html=True)
            st.dataframe(cmp_df, use_container_width=True, hide_index=True)
