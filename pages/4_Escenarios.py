import streamlit as st
import pandas as pd
from pathlib import Path

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

from utils.defaults import (
    VARIABLE_RANGES, TECHNICAL_VARIABLE_RANGES,
    DEFAULT_DEPARTMENT, DEFAULT_YEAR,
)
from utils.formatters import fmt_pct, level_from_score, label_for_level
from utils.api_client import predict_annual
from utils.validators import validate_annual_payload
from components.charts import plot_tornado
from components.metric_card import render_kpi_card
from components.disclaimer import render_disclaimer

st.markdown('<div class="page-title">Análisis de Escenarios What-If</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Ajusta las variables climáticas para entender la sensibilidad del modelo. Identifica cuáles factores tienen mayor impacto en la predicción.</div>',
    unsafe_allow_html=True,
)

department = st.session_state.get("department", DEFAULT_DEPARTMENT)
year       = st.session_state.get("year", DEFAULT_YEAR)
mode       = st.session_state.get("mode", "Básico")

active_ranges = (
    {**VARIABLE_RANGES, **TECHNICAL_VARIABLE_RANGES}
    if mode == "Técnico"
    else VARIABLE_RANGES
)

sliders_col, results_col = st.columns([1, 1], gap="large")

# ─── Sliders ─────────────────────────────────────────────────────────────────
with sliders_col:
    st.markdown('<div class="section-label">Variables de entrada</div>', unsafe_allow_html=True)

    input_values = {}
    for key, r in active_ranges.items():
        label = f"{r['label']}"
        if r.get("unit"):
            label += f" ({r['unit']})"
        input_values[key] = st.slider(
            label=label,
            min_value=float(r["min"]),
            max_value=float(r["max"]),
            value=float(r["default"]),
            step=float(r["step"]),
            key=f"scenario_{key}",
            help=r.get("tooltip", ""),
        )

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    calculate = st.button("Calcular escenario", use_container_width=True, type="primary")

# ─── Results ─────────────────────────────────────────────────────────────────
with results_col:
    st.markdown('<div class="section-label">Resultado del escenario</div>', unsafe_allow_html=True)

    if calculate:
        payload = {
            "departamento": department,
            "anio": year,
            "es_risaralda": department == "Risaralda",
            **input_values,
        }

        valid, err_msg = validate_annual_payload(payload)
        if not valid:
            st.error(f"Valor fuera de rango: {err_msg}")
        else:
            with st.spinner("Calculando..."):
                result = predict_annual(payload)

            if result["ok"]:
                st.session_state["scenario_result"] = result
                st.session_state["scenario_inputs"] = input_values.copy()

                # ─── Tornado: N+1 calls (+10% per variable) ─────────────────
                with st.spinner("Calculando sensibilidad por variable..."):
                    base_score = (
                        result["data"].get("porcentaje_perdida_estimado")
                        or result["data"].get("score_anual", 0)
                    )
                    sensitivity_rows = []
                    for key, r in active_ranges.items():
                        val_up = min(input_values[key] * 1.10, r["max"])
                        payload_up = {**payload, key: val_up}
                        res_up = predict_annual(payload_up)
                        if res_up["ok"]:
                            score_up = (
                                res_up["data"].get("porcentaje_perdida_estimado")
                                or res_up["data"].get("score_anual", 0)
                            )
                            delta = score_up - base_score
                            sensitivity_rows.append({
                                "variable_label": r["label"],
                                "delta_pp": round(delta, 2),
                            })
                    st.session_state["tornado_df"] = pd.DataFrame(sensitivity_rows)
                st.rerun()
            else:
                st.error(f"Error al consultar la API: {result['error']}")

    scenario_result = st.session_state.get("scenario_result")
    if scenario_result and scenario_result.get("ok"):
        data = scenario_result["data"]
        score = data.get("porcentaje_perdida_estimado") or data.get("score_anual")
        level = level_from_score(score)

        st.markdown(
            render_kpi_card(
                label="Pérdida estimada en este escenario",
                value=fmt_pct(score),
                context=label_for_level(level),
                level=level,
            ),
            unsafe_allow_html=True,
        )

        # Compare with last Pantalla 1 result
        prev_result = st.session_state.get("last_result")
        if prev_result and prev_result.get("ok"):
            prev_score = (
                prev_result["data"].get("porcentaje_perdida_estimado")
                or prev_result["data"].get("score_anual")
            )
            if prev_score is not None and score is not None:
                delta = score - prev_score
                st.markdown(
                    render_kpi_card(
                        label="Δ vs última evaluación anual",
                        value=fmt_pct(delta),
                        context="diferencia respecto a Pantalla 1",
                        level="caution" if abs(delta) > 5 else "normal",
                    ),
                    unsafe_allow_html=True,
                )

        # Tornado chart
        tornado_df = st.session_state.get("tornado_df", pd.DataFrame())
        if not tornado_df.empty:
            st.markdown('<div class="section-label" style="margin-top:16px;">Sensibilidad por variable</div>', unsafe_allow_html=True)
            fig = plot_tornado(tornado_df)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Ajusta los controles deslizantes y presiona **Calcular escenario**.")

st.markdown(render_disclaimer("basic"), unsafe_allow_html=True)
