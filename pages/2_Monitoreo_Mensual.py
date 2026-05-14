import streamlit as st

st.set_page_config(
    page_title="Monitoreo Mensual — Seguro Cafetero",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
from components.sidebar import render_sidebar
from utils.defaults import (
    DEFAULT_DEPARTMENT, DEFAULT_YEAR,
    DETECTOR_THRESHOLD, TRIGGER_THRESHOLD, MODEL_MAE_MONTHLY_ANNUALIZED,
)
from utils.formatters import fmt_pct, level_from_score, color_for_level
from utils.api_client import predict_monthly
from components.charts import plot_monthly_scores
from components.disclaimer import render_disclaimer
from components.metric_card import render_kpi_card

HARVEST_MONTHS = {4: "Abril", 5: "Mayo", 6: "Junio", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
ALL_MONTHS = {
    1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
    7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre",
}

render_sidebar()

st.markdown('<div class="page-title">Monitoreo Mensual de Cosecha</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Seguimiento durante la cosecha. Ingresa datos mensuales para anticipar el nivel de riesgo antes del cierre del ciclo.</div>',
    unsafe_allow_html=True,
)

department = st.session_state.get("department", DEFAULT_DEPARTMENT)
year       = st.session_state.get("year", DEFAULT_YEAR)

# ─── Monthly records input ────────────────────────────────────────────────────
st.markdown('<div class="section-label">Registros mensuales (solo meses de cosecha)</div>', unsafe_allow_html=True)

st.info(
    "Este modelo solo predice meses de cosecha: **Abr–Jun** (cosecha grande) y **Oct–Dic** (mitaca). "
    "Ingresa los datos disponibles y presiona **Calcular**.",
    icon="ℹ️",
)

monthly_records = st.session_state.get("monthly_records", [])

with st.form("monthly_input_form"):
    selected_months = st.multiselect(
        "Meses a ingresar",
        options=list(HARVEST_MONTHS.keys()),
        format_func=lambda m: HARVEST_MONTHS[m],
        default=[4, 5, 6],
        help="Selecciona los meses para los que tienes datos disponibles",
    )

    records = []
    if selected_months:
        cols = st.columns(min(len(selected_months), 3))
        for i, month in enumerate(sorted(selected_months)):
            with cols[i % 3]:
                st.markdown(f"**{HARVEST_MONTHS[month]}**")
                precip = st.number_input(f"Precipitación (mm)", min_value=0.0, max_value=600.0, value=150.0, step=1.0, key=f"m_precip_{month}")
                temp   = st.number_input(f"Temperatura (°C)", min_value=14.0, max_value=22.0, value=17.0, step=0.1, key=f"m_temp_{month}")
                ndvi   = st.number_input(f"Anomalía NDVI (%)", min_value=-20.0, max_value=20.0, value=0.0, step=0.5, key=f"m_ndvi_{month}")
                deficit= st.number_input(f"Déficit hídrico (mm)", min_value=0.0, max_value=100.0, value=10.0, step=1.0, key=f"m_def_{month}")

                records.append({
                    "departamento": department,
                    "anio": year,
                    "mes": month,
                    "es_cosecha": True,
                    "es_risaralda": department == "Risaralda",
                    "precipitation_monthly_sum": precip,
                    "temp_aire_C_monthly_mean": temp,
                    "NDVI_anomalia_pct_monthly_mean": ndvi,
                    "def_monthly_mean": deficit,
                })

    submitted = st.form_submit_button("Calcular scores mensuales", use_container_width=True, type="primary")

if submitted and records:
    with st.spinner("Consultando modelo mensual..."):
        result = predict_monthly(records)
    st.session_state["monthly_records"] = records
    st.session_state["monthly_result"] = result
    if not result["ok"]:
        st.error(f"Error al consultar la API: {result['error']}")
    else:
        st.rerun()

# ─── Results ──────────────────────────────────────────────────────────────────
monthly_result = st.session_state.get("monthly_result")

if monthly_result and monthly_result.get("ok"):
    data = monthly_result["data"]
    predictions = data.get("predictions", [])

    if predictions:
        scores = [p.get("score_mensual", 0) for p in predictions]
        avg_score = sum(scores) / len(scores)
        any_alert = any(s <= DETECTOR_THRESHOLD for s in scores)

        st.markdown('<div class="section-label">Resumen</div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                render_kpi_card(
                    label="Score anualizado promedio",
                    value=fmt_pct(avg_score),
                    context=f"MAE modelo: {MODEL_MAE_MONTHLY_ANNUALIZED} pp",
                    level=level_from_score(avg_score),
                    tooltip="Promedio de los scores mensuales ingresados",
                ),
                unsafe_allow_html=True,
            )
        with m2:
            alert_txt = "Sí" if any_alert else "No"
            alert_lvl = "caution" if any_alert else "normal"
            st.markdown(
                render_kpi_card(
                    label="Alerta activa",
                    value=alert_txt,
                    context="algún mes supera el detector −2.8%",
                    level=alert_lvl,
                ),
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                render_kpi_card(
                    label="Meses ingresados",
                    value=f"{len(predictions)} / 6",
                    context="de 6 meses de cosecha posibles",
                    level="info",
                ),
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-label" style="margin-top:16px;">Evolución mensual</div>', unsafe_allow_html=True)
        chart_records = [{"mes": p["mes"], "score": p["score_mensual"]} for p in predictions]
        fig = plot_monthly_scores(chart_records)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="section-label">Detalle por mes</div>', unsafe_allow_html=True)
        df_display = pd.DataFrame([
            {
                "Mes": ALL_MONTHS.get(p["mes"], p["mes"]),
                "Score": f"{p['score_mensual']:+.1f}%",
                "Alerta": "Sí" if p["score_mensual"] <= DETECTOR_THRESHOLD else "No",
                "Trigger": "Activado" if p["score_mensual"] <= TRIGGER_THRESHOLD else "No",
            }
            for p in predictions
        ])
        st.dataframe(df_display, use_container_width=True, hide_index=True)

st.markdown(render_disclaimer("full"), unsafe_allow_html=True)
