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
from components.metric_card import render_kpi_card

HARVEST_MONTHS = {4: "Abril", 5: "Mayo", 6: "Junio", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
ALL_MONTHS = {
    1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
    7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre",
}

# Terrain defaults per department derived from dataset means
DEPT_TERRAIN = {
    "Risaralda":    {"elevacion_media_m": 1750.0, "pendiente_media": 22.0},
    "Cundinamarca": {"elevacion_media_m": 1850.0, "pendiente_media": 25.0},
}

render_sidebar()
st.markdown("""<style>:root {
  --page-accent: #16A34A;
  --page-accent-light: #F0FDF4;
  --page-accent-border: #86EFAC;
}</style>""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
  <div class="page-accent-bar"></div>
  <div class="page-title">Monitoreo Mensual de Cosecha</div>
</div>
""", unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Seguimiento durante la cosecha. Ingresa datos mensuales para anticipar el nivel de riesgo antes del cierre del ciclo.</div>',
    unsafe_allow_html=True,
)

department = st.session_state.get("department", DEFAULT_DEPARTMENT)
year       = st.session_state.get("year", DEFAULT_YEAR)

terrain = DEPT_TERRAIN.get(department, DEPT_TERRAIN["Risaralda"])

# ─── Zone & market parameters (outside form so they update freely) ────────────
with st.expander("Parámetros de zona y mercado", expanded=False):
    pc1, pc2, pc3, pc4 = st.columns(4)
    with pc1:
        precio_ico = st.number_input(
            "Precio ICO (USD/t)", min_value=0.0, max_value=None,
            value=3200.0, step=50.0,
            help="Precio internacional del café colombiano (ICO)",
        )
    with pc2:
        precio_prod = st.number_input(
            "Precio productor (USD/t)", min_value=0.0, max_value=None,
            value=2200.0, step=50.0,
            help="Precio recibido por el productor en finca",
        )
    with pc3:
        elevacion = st.number_input(
            "Elevación media (m)", min_value=0.0, max_value=None,
            value=terrain["elevacion_media_m"], step=10.0,
            help="Elevación media de la zona productora (SRTM)",
        )
    with pc4:
        pendiente = st.number_input(
            "Pendiente media (°)", min_value=0.0, max_value=None,
            value=terrain["pendiente_media"], step=0.5,
            help="Pendiente media del terreno",
        )

# ─── Monthly records input ────────────────────────────────────────────────────
st.markdown('<div class="section-label">Registros mensuales (meses de cosecha)</div>', unsafe_allow_html=True)
st.info(
    "El modelo requiere **mínimo 3 meses**. Meses de cosecha: "
    "**Abr–Jun** (cosecha grande) y **Oct–Dic** (mitaca).",
    icon="ℹ️",
)

with st.form("monthly_input_form"):
    selected_months = st.multiselect(
        "Meses a ingresar",
        options=list(HARVEST_MONTHS.keys()),
        format_func=lambda m: HARVEST_MONTHS[m],
        default=[4, 5, 6],
        help="Selecciona al menos 3 meses de cosecha",
    )

    records = []
    if selected_months:
        cols = st.columns(min(len(selected_months), 3))
        for i, month in enumerate(sorted(selected_months)):
            with cols[i % 3]:
                st.markdown(f"**{HARVEST_MONTHS[month]}**")
                precip = st.number_input(
                    "Precipitación (mm)", min_value=0.0, max_value=None,
                    value=150.0, step=1.0, key=f"m_precip_{month}",
                )
                temp = st.number_input(
                    "Temperatura (°C)", min_value=None, max_value=None,
                    value=17.0, step=0.1, key=f"m_temp_{month}",
                )
                ndvi_a = st.number_input(
                    "Anomalía NDVI (%)", min_value=None, max_value=None,
                    value=0.0, step=0.5, key=f"m_ndvi_{month}",
                )
                deficit = st.number_input(
                    "Déficit hídrico (mm)", min_value=0.0, max_value=None,
                    value=10.0, step=1.0, key=f"m_def_{month}",
                )

                records.append({
                    "departamento": department,
                    "anio": year,
                    "mes": month,
                    "es_mes_cosecha": 1,
                    "factor_mensual": 1.0,
                    "precio_ico_usd_ton": precio_ico,
                    "precio_productor_usd_ton": precio_prod,
                    "elevacion_media_m": elevacion,
                    "pendiente_media": pendiente,
                    "precipitation": precip,
                    "temp_aire_C": temp,
                    "def": deficit,
                    "GDD_cafe": 7.8,
                    "NDVI": 0.65,
                    "EVI": 0.55,
                    "Gpp": 1.8,
                    "NDVI_anomalia_pct": ndvi_a,
                    "EVI_anomalia_pct": 0.0,
                    "Gpp_anomalia_pct": 0.0,
                })

    submitted = st.form_submit_button(
        "Calcular scores mensuales", use_container_width=True, type="primary"
    )

if submitted:
    if len(records) < 3:
        st.warning("Se necesitan **al menos 3 meses** para ejecutar el modelo mensual. Selecciona más meses.")
    else:
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
    predictions = data.get("scores_por_mes", [])

    if predictions:
        scores = [
            p.get("score", 0)
            for p in predictions
            if p.get("score") is not None
        ]
        avg_score = sum(scores) / len(scores) if scores else 0
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

        st.markdown(
            '<div class="section-label" style="margin-top:16px;">Evolución mensual</div>',
            unsafe_allow_html=True,
        )
        chart_records = [
            {"mes": p["mes"], "score": p.get("score", 0)}
            for p in predictions
        ]
        fig = plot_monthly_scores(chart_records)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="section-label">Detalle por mes</div>', unsafe_allow_html=True)
        df_display = pd.DataFrame([
            {
                "Mes": ALL_MONTHS.get(p["mes"], p["mes"]),
                "Score": f"{p['score']:+.1f}%" if p.get("score") is not None else "—",
                "Alerta": "Sí" if (p.get("score") or 0) <= DETECTOR_THRESHOLD else "No",
                "Trigger": "Activado" if (p.get("score") or 0) <= TRIGGER_THRESHOLD else "No",
            }
            for p in predictions
        ])
        st.dataframe(df_display, use_container_width=True, hide_index=True)
