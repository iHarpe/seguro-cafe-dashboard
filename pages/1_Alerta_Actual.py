import streamlit as st

st.set_page_config(
    page_title="Evaluación de Riesgo Anual — Seguro Cafetero",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

from datetime import datetime

from components.sidebar import render_sidebar
from utils.defaults import (
    VARIABLE_RANGES, TECHNICAL_VARIABLE_RANGES,
    DEFAULT_DEPARTMENT, DEFAULT_YEAR,
    DETECTOR_THRESHOLD, TRIGGER_THRESHOLD, MODEL_MAE_ANNUAL,
    MODEL_MAE_MONTHLY_ANNUALIZED,
)
from utils.formatters import fmt_pct, fmt_pp, level_from_api, level_from_score, freshness_level
from utils.validators import validate_annual_payload
from utils.api_client import predict_annual, get_health_full, get_monthly_history
from components.semaphore import render_semaphore
from components.metric_card import render_kpi_card, render_trigger_card

# ─── Sidebar (navigation + config + CSS) ─────────────────────────────────────
render_sidebar()
st.markdown("""<style>:root {
  --page-accent: #1E40AF;
  --page-accent-light: #EFF6FF;
  --page-accent-border: #93C5FD;
}</style>""", unsafe_allow_html=True)

# ─── Page header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <div class="page-accent-bar"></div>
  <div class="page-title">Evaluación de Riesgo Anual</div>
</div>
""", unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Ingresa las variables climáticas del año a evaluar '
    'y consulta el nivel de riesgo estimado por el modelo.</div>',
    unsafe_allow_html=True,
)

department = st.session_state.get("department", DEFAULT_DEPARTMENT)

# ─── Page-level controls: year & mode ────────────────────────────────────────
ctrl_yr, ctrl_mode, _ = st.columns([1, 1, 3])
with ctrl_yr:
    year = st.slider(
        "Año de análisis",
        min_value=2007, max_value=2024,
        step=1, key="year",
        help="Año para la evaluación anual de riesgo",
    )
with ctrl_mode:
    mode = st.radio(
        "Modo de análisis",
        options=["Básico", "Técnico"],
        key="mode",
        horizontal=True,
        help="Básico: 10 variables climáticas. Técnico: +7 satelitales (MODIS/TerraClimate).",
    )

# ─── Layout ───────────────────────────────────────────────────────────────────
hero_col, inputs_col = st.columns([1, 2], gap="large")

# ─── Hero column: semaphore + KPIs ───────────────────────────────────────────
with hero_col:
    result = st.session_state.get("last_result")

    if result and result.get("ok") and "data" in result:
        data  = result["data"]
        score = data.get("perdida_estimada_pct")          # correct API field
        nivel = data.get("nivel_alerta", "UNKNOWN")
        level = level_from_api(nivel)
        trigger_on  = data.get("trigger_activado", False)
        detector_on = data.get("evento_detectado", False)
        basis       = data.get("basis_risk_estimado_pp")
    else:
        score = None; level = "unknown"
        trigger_on = False; detector_on = False; basis = None

    st.markdown(render_semaphore(level), unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    kpi1, kpi2 = st.columns(2)
    with kpi1:
        st.markdown(
            render_kpi_card(
                label="Pérdida estimada",
                value=fmt_pct(score) if score is not None else "—",
                context=f"MAE modelo: {MODEL_MAE_ANNUAL} pp",
                level=level if score is not None else "neutral",
                tooltip=f"Estimación XGBoost. MAE = {MODEL_MAE_ANNUAL} pp en test.",
            ),
            unsafe_allow_html=True,
        )
    with kpi2:
        st.markdown(render_trigger_card(trigger_on, score), unsafe_allow_html=True)

    if score is not None:
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            score_m3 = data.get("perdida_estimada_pct") if result and result.get("ok") else None
            st.markdown(
                render_kpi_card(
                    label="Score M3 (continuo)",
                    value=fmt_pct(score_m3) if score_m3 is not None else "---",
                    context="senal continua del detector HGB",
                    level=level_from_api(data.get("nivel_alerta", "")) if result and result.get("ok") else "neutral",
                    tooltip="Score del modelo HGB Set A. Basis risk real: consultar seccion Historico.",
                ),
                unsafe_allow_html=True,
            )
        with col_b2:
            det_label = "Detector activo" if detector_on else "Sin deteccion"
            det_level = "caution" if detector_on else "normal"
            st.markdown(
                render_kpi_card(
                    label="Detector (-2.8%)",
                    value=det_label,
                    context=f"umbral: {DETECTOR_THRESHOLD}%",
                    level=det_level,
                    tooltip="Senal temprana: la prediccion supera -2.8%. Es una alerta previa al trigger.",
                ),
                unsafe_allow_html=True,
            )

    # Harvest season badge
    current_month = datetime.now().month
    if current_month in {4, 5, 6, 10, 11, 12}:
        st.info("Temporada de cosecha activa -- M4 (modelo mensual) en alta confianza.")

    # Monthly M4 score for current context
    current_year = datetime.now().year
    if year >= current_year - 1:
        hist_m4 = get_monthly_history(department)
        if hist_m4["ok"] and hist_m4["data"]:
            import pandas as _pd
            _mdf = _pd.DataFrame(hist_m4["data"])
            _mdf = _mdf.dropna(subset=["score_m4"])
            if not _mdf.empty:
                _mdf = _mdf.sort_values(["anio", "mes"])
                _latest = _mdf.iloc[-1]
                _score = _latest["score_m4"]
                _mes_names = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                              7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
                _mes_label = _mes_names.get(int(_latest["mes"]), "?")
                _trend_ctx = ""
                if len(_mdf) >= 2:
                    _prev = _mdf.iloc[-2]["score_m4"]
                    _delta = _score - _prev
                    _trend_ctx = f" | tendencia: {_delta:+.1f} pp vs mes anterior"
                st.markdown(
                    render_kpi_card(
                        label=f"Score M4 — {_mes_label} {int(_latest['anio'])}",
                        value=fmt_pct(_score),
                        context=f"MAE anualizado: {MODEL_MAE_MONTHLY_ANNUALIZED} pp{_trend_ctx}",
                        level=level_from_score(_score),
                        tooltip="Ultimo score mensual disponible del modelo M4 (HGB lags cosecha)",
                    ),
                    unsafe_allow_html=True,
                )

    # Data freshness indicator
    health_data = get_health_full()
    if health_data["ok"]:
        days = health_data["data"].get("data_freshness_days")
        fl = freshness_level(days)
        fresh_color = {"normal": "#16A34A", "caution": "#D97706", "alert": "#DC2626"}.get(fl, "#94A3B8")
        st.markdown(
            f'<div style="font-size:12px;color:{fresh_color};margin-top:8px;">'
            f'Datos actualizados hace {days} dias</div>',
            unsafe_allow_html=True,
        )

    # AUC disclaimer
    st.caption(
        "Senal limitada: AUC-ROC del clasificador = 0.32 "
        "(limitado por muestra de 36 obs anuales y 7 eventos historicos)."
    )


# ─── Inputs column ────────────────────────────────────────────────────────────
with inputs_col:
    st.markdown(
        '<div class="section-label">Variables climáticas anuales</div>',
        unsafe_allow_html=True,
    )

    input_values: dict[str, float] = {}

    def _number(key: str, ranges: dict) -> float:
        r = ranges[key]
        label = f"{r['label']} ({r['unit']})" if r.get("unit") else r["label"]
        floor = r.get("floor")
        return st.number_input(
            label=label,
            min_value=float(floor) if floor is not None else None,
            max_value=None,
            value=float(r["default"]),
            step=float(r["step"]),
            key=f"inp_{key}",
            help=r.get("tooltip", ""),
            format="%.1f" if r["step"] < 1 else "%.0f",
        )

    # Basic vars in 2 columns
    basic_keys = list(VARIABLE_RANGES.keys())
    half = (len(basic_keys) + 1) // 2
    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        for key in basic_keys[:half]:
            input_values[key] = _number(key, VARIABLE_RANGES)
    with col_b:
        for key in basic_keys[half:]:
            input_values[key] = _number(key, VARIABLE_RANGES)

    # Technical vars — visible when Modo Técnico, hidden otherwise
    tech_keys = list(TECHNICAL_VARIABLE_RANGES.keys())
    if mode == "Técnico":
        st.markdown(
            '<div class="section-label" style="margin-top:16px;">'
            'Variables satelitales adicionales (Set A)</div>',
            unsafe_allow_html=True,
        )
        t_col_a, t_col_b = st.columns(2, gap="medium")
        t_half = (len(tech_keys) + 1) // 2
        with t_col_a:
            for key in tech_keys[:t_half]:
                input_values[key] = _number(key, TECHNICAL_VARIABLE_RANGES)
        with t_col_b:
            for key in tech_keys[t_half:]:
                input_values[key] = _number(key, TECHNICAL_VARIABLE_RANGES)
    else:
        with st.expander("Variables satelitales adicionales — Modo Técnico", expanded=False):
            st.caption(
                "Activa **Modo Técnico** (selector arriba) para editar "
                "estas 7 variables de MODIS y TerraClimate. "
                "En modo básico se usan los valores por defecto, que son suficientes para la evaluación estándar."
            )
            # Show them read-only so the user can see defaults
            t2_col_a, t2_col_b = st.columns(2, gap="medium")
            t_half = (len(tech_keys) + 1) // 2
            with t2_col_a:
                for key in tech_keys[:t_half]:
                    r = TECHNICAL_VARIABLE_RANGES[key]
                    st.text_input(
                        f"{r['label']} ({r.get('unit','')})",
                        value=str(r["default"]),
                        disabled=True,
                        key=f"ro_{key}",
                        help=r.get("tooltip", ""),
                    )
            with t2_col_b:
                for key in tech_keys[t_half:]:
                    r = TECHNICAL_VARIABLE_RANGES[key]
                    st.text_input(
                        f"{r['label']} ({r.get('unit','')})",
                        value=str(r["default"]),
                        disabled=True,
                        key=f"ro_{key}",
                        help=r.get("tooltip", ""),
                    )

    # Always fill tech vars with defaults if not edited by user
    for key in tech_keys:
        if key not in input_values:
            input_values[key] = float(TECHNICAL_VARIABLE_RANGES[key]["default"])

    # ─── Calculate button ─────────────────────────────────────────────────────
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    calculate = st.button("Calcular riesgo", use_container_width=True, type="primary")

    if calculate:
        payload = {
            "departamento": department,
            "anio": int(year),
            **{k: float(v) for k, v in input_values.items()},
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
