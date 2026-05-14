import streamlit as st
from pathlib import Path

# ─── CSS (inyectado en cada página individualmente) ───────────────────────────
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

from utils.defaults import (
    VARIABLE_RANGES, TECHNICAL_VARIABLE_RANGES,
    DEPARTMENTS, DEFAULT_DEPARTMENT, DEFAULT_YEAR,
    DETECTOR_THRESHOLD, TRIGGER_THRESHOLD,
    MODEL_MAE_ANNUAL,
)
from utils.formatters import fmt_pct, fmt_pp, level_from_score, color_for_level
from utils.validators import validate_annual_payload
from utils.api_client import predict_annual
from components.semaphore import render_semaphore
from components.metric_card import render_kpi_card, render_trigger_card
from components.disclaimer import render_disclaimer

# ─── Page header ─────────────────────────────────────────────────────────────
st.markdown(
    '<div class="page-title">Evaluación de Riesgo Anual</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="page-subtitle">Ingresa las variables climáticas del año a evaluar y consulta el nivel de riesgo estimado por el modelo.</div>',
    unsafe_allow_html=True,
)

# ─── Read shared state ────────────────────────────────────────────────────────
department = st.session_state.get("department", DEFAULT_DEPARTMENT)
year       = st.session_state.get("year", DEFAULT_YEAR)
mode       = st.session_state.get("mode", "Básico")

# ─── Layout: hero left | inputs right ────────────────────────────────────────
hero_col, inputs_col = st.columns([1, 2], gap="large")

with hero_col:
    # Semaphore
    result = st.session_state.get("last_result")
    if result and result.get("ok") and "data" in result:
        data   = result["data"]
        score  = data.get("porcentaje_perdida_estimado") or data.get("score_anual")
        level  = level_from_score(score)
    else:
        score = None
        level = "unknown"

    st.markdown(render_semaphore(level), unsafe_allow_html=True)

    # ─── KPI cards ──────────────────────────────────────────────────────────
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    kpi1, kpi2 = st.columns(2)
    with kpi1:
        loss_val  = fmt_pct(score) if score is not None else "—"
        loss_ctx  = f"MAE modelo: {MODEL_MAE_ANNUAL} pp"
        loss_lvl  = level if score is not None else "neutral"
        st.markdown(
            render_kpi_card(
                label="Pérdida estimada",
                value=loss_val,
                context=loss_ctx,
                level=loss_lvl,
                tooltip=f"Estimación XGBoost. MAE = {MODEL_MAE_ANNUAL} pp en test.",
            ),
            unsafe_allow_html=True,
        )

    with kpi2:
        activated = score is not None and score <= TRIGGER_THRESHOLD
        st.markdown(render_trigger_card(activated, score), unsafe_allow_html=True)

    # Basis risk card (solo si hay resultado con dato real)
    if result and result.get("ok") and "data" in result:
        data = result["data"]
        basis = data.get("basis_risk_pp")
        detector_flag = data.get("detector_activado", False)

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        basis_val = fmt_pp(basis) if basis is not None else "—"
        det_label = "Detector activado" if detector_flag else "Detector no activado"
        det_level = "caution" if detector_flag else "normal"

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown(
                render_kpi_card(
                    label="Basis Risk",
                    value=basis_val,
                    context="diferencia real vs predicción",
                    level="neutral",
                    tooltip="Basis risk = pérdida real − predicción modelo (solo disponible en años históricos con dato Agronet)",
                ),
                unsafe_allow_html=True,
            )
        with col_b2:
            st.markdown(
                render_kpi_card(
                    label="Detector (−2.8%)",
                    value=det_label,
                    context=f"umbral: {DETECTOR_THRESHOLD}%",
                    level=det_level,
                    tooltip="El detector se activa cuando la predicción supera −2.8%. Es una señal temprana antes del trigger.",
                ),
                unsafe_allow_html=True,
            )

    # Disclaimer always visible, below KPIs
    st.markdown(render_disclaimer("full"), unsafe_allow_html=True)


with inputs_col:
    st.markdown('<div class="section-label">Variables climáticas anuales</div>', unsafe_allow_html=True)

    # Basic variables — always visible
    basic_vars   = list(VARIABLE_RANGES.keys())
    tech_vars    = list(TECHNICAL_VARIABLE_RANGES.keys())
    input_values = {}

    def _slider(key: str, ranges: dict, col=None) -> float:
        r = ranges[key]
        widget_key = f"inp_{key}"
        val = st.number_input(
            label=f"{r['label']} ({r['unit']})" if r['unit'] else r['label'],
            min_value=float(r["min"]),
            max_value=float(r["max"]),
            value=float(r["default"]),
            step=float(r["step"]),
            key=widget_key,
            help=r.get("tooltip", ""),
            format="%.1f" if r["step"] < 1 else "%.0f",
        )
        return val

    # Split basic vars into two columns
    n = len(basic_vars)
    half = (n + 1) // 2
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        for key in basic_vars[:half]:
            input_values[key] = _slider(key, VARIABLE_RANGES)

    with col_b:
        for key in basic_vars[half:]:
            input_values[key] = _slider(key, VARIABLE_RANGES)

    # Technical variables — collapsible
    if mode == "Técnico":
        st.markdown('<div class="section-label" style="margin-top:16px;">Variables satelitales adicionales (Set A)</div>', unsafe_allow_html=True)
        t_col_a, t_col_b = st.columns(2, gap="medium")
        t_half = (len(tech_vars) + 1) // 2
        with t_col_a:
            for key in tech_vars[:t_half]:
                input_values[key] = _slider(key, TECHNICAL_VARIABLE_RANGES)
        with t_col_b:
            for key in tech_vars[t_half:]:
                input_values[key] = _slider(key, TECHNICAL_VARIABLE_RANGES)
    else:
        with st.expander("Variables satelitales adicionales (Modo Técnico)", expanded=False):
            st.caption(
                "Activa el modo Técnico en la barra lateral para ingresar estas 7 variables "
                "de MODIS/TerraClimate. Son opcionales pero mejoran la precisión cuando están disponibles."
            )

    # ─── Calculate button ────────────────────────────────────────────────────
    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    btn_disabled = False
    calculate = st.button(
        "Calcular riesgo",
        disabled=btn_disabled,
        use_container_width=True,
        type="primary",
    )

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
            with st.spinner("Consultando modelo..."):
                result = predict_annual(payload)

            st.session_state["last_result"] = result

            if result["ok"]:
                st.rerun()
            else:
                st.error(
                    f"No se pudo obtener la predicción: {result['error']}  \n"
                    "Verifica que la API esté corriendo en `localhost:8000`."
                )

# ─── Error state from previous run ──────────────────────────────────────────
stored = st.session_state.get("last_result")
if stored and not stored.get("ok") and "error" in stored:
    pass  # already shown above after click
