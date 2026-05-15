import streamlit as st

st.set_page_config(
    page_title="Metodologia -- Seguro Cafetero",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
from components.sidebar import render_sidebar
from utils.api_client import get_correlations, get_oof, get_health_full
from utils.defaults import (
    MODEL_MAE_ANNUAL, MODEL_MAE_MONTHLY_ANNUALIZED,
    MODEL_N_OBS, MODEL_RECALL,
    DETECTOR_THRESHOLD, TRIGGER_THRESHOLD,
)

render_sidebar()
st.markdown("""<style>:root {
  --page-accent: #0891B2;
  --page-accent-light: #ECFEFF;
  --page-accent-border: #67E8F9;
}</style>""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
  <div class="page-accent-bar"></div>
  <div class="page-title">Metodologia</div>
</div>
""", unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Documentacion tecnica del sistema: arquitectura, modelos, fuentes de datos y limitaciones conocidas.</div>',
    unsafe_allow_html=True,
)

tab_arch, tab_corr, tab_perf, tab_data, tab_lim, tab_pipe = st.tabs([
    "Arquitectura", "Correlaciones", "Desempeno", "Fuentes de datos", "Limitaciones", "Pipeline",
])

# ─── Tab 1: Architecture ─────────────────────────────────────────────────────
with tab_arch:
    st.markdown('<div class="section-label">Diagrama del sistema</div>', unsafe_allow_html=True)

    st.markdown("""
```
                        +──────────────────────+
                        │   Google Earth Engine │
                        │   CHIRPS, ERA5, MODIS │
                        │   TerraClimate, SRTM  │
                        +──────────┬───────────+
                                   │
                                   ▼
                        +──────────────────────+
                        │    PROYECTO_V2        │
                        │  (notebooks + datos)  │
                        │  dataset_anual.csv    │
                        │  dataset_mensual.csv  │
                        +──────────┬───────────+
                                   │
                                   ▼
+──────────────────────────────────────────────────────────+
│                  seguro-cafe-api (FastAPI)                │
│                                                          │
│  Modelos entrenados (.pkl):                              │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────┐   │
│  │ M1: XGBoost │ │ M2/M3: HGB  │ │ M4: HGB mensual  │   │
│  │ Magnitud    │ │ Detector +  │ │ Lags cosecha     │   │
│  │ 10 vars     │ │ Trigger 18v │ │ ~50 vars         │   │
│  └─────────────┘ └─────────────┘ └──────────────────┘   │
│                                                          │
│  Endpoints:                                              │
│  POST /predict/annual    POST /predict/monthly           │
│  GET  /data/backtest     GET  /data/monthly-history      │
│  GET  /data/history      GET  /data/oof                  │
│  GET  /data/correlations GET  /calibrate/trigger         │
│  GET  /health                                            │
+────────────────────────┬─────────────────────────────────+
                         │
                         ▼
+──────────────────────────────────────────────────────────+
│              seguro-cafe-dashboard (Streamlit)            │
│                                                          │
│  P1: Evaluacion Anual     P2: Monitoreo Mensual          │
│  P3: Analisis Historico   P4: Simulador Actuarial        │
│  P5: Metodologia          P6: Score Mensual              │
+──────────────────────────────────────────────────────────+
```
""")

    st.markdown("""
**Modelos:**

| ID | Nombre | Algoritmo | Features | Uso |
|---|---|---|---|---|
| M1 | Magnitud | XGBoost | `baseline_parsimonioso` (10 vars) | Estima % perdida continua |
| M2 | Detector | HGB Set A | 18 vars | Clasificador binario: evento > {det}% |
| M3 | Trigger | HGB Set A | 18 vars | Clasificador binario: evento > {trig}% |
| M4 | Mensual | HGB lags cosecha | ~50 vars | Alerta temprana durante cosecha |
""".format(det=DETECTOR_THRESHOLD, trig=TRIGGER_THRESHOLD))

# ─── Tab 2: Correlations ─────────────────────────────────────────────────────
with tab_corr:
    st.markdown('<div class="section-label">Importancia de variables (correlacion con perdida)</div>', unsafe_allow_html=True)

    corr_result = get_correlations()
    if corr_result["ok"]:
        corr_data = corr_result["data"]
        if corr_data:
            corr_df = pd.DataFrame(corr_data)
            if "variable" in corr_df.columns and "pearson_r" in corr_df.columns:
                corr_df = corr_df.sort_values("pearson_r", key=abs, ascending=False)
                display_cols = [c for c in ["variable", "label", "pearson_r", "p_value", "significant"] if c in corr_df.columns]
                st.dataframe(
                    corr_df[display_cols].style.format({"pearson_r": "{:.3f}", "p_value": "{:.4f}"}).bar(
                        subset=["pearson_r"], color=["#DC2626", "#16A34A"], align="zero"
                    ),
                    use_container_width=True, hide_index=True,
                )
            else:
                st.dataframe(corr_df, use_container_width=True, hide_index=True)
        else:
            st.info("Sin datos de correlaciones.")
    else:
        st.warning(f"No se pudo cargar correlaciones: {corr_result['error']}")

    st.caption(
        "Correlacion de Pearson entre cada variable del Set A (18 features) "
        "y la perdida de rendimiento anual (%). Datos: 2007-2024, ambos departamentos."
    )

# ─── Tab 3: Performance ──────────────────────────────────────────────────────
with tab_perf:
    st.markdown('<div class="section-label">Metricas de desempeno</div>', unsafe_allow_html=True)

    perf_data = {
        "Modelo": ["M1 (XGBoost Magnitud)", "M2/M3 (HGB Detector+Trigger)", "M4 (HGB Mensual)"],
        "MAE (pp)": [MODEL_MAE_ANNUAL, "---", MODEL_MAE_MONTHLY_ANNUALIZED],
        "Entrenamiento": ["2007-2020", "2007-2020", "2007-2020"],
        "Prueba": ["2021-2024", "2021-2024", "2021-2024"],
        "N obs": [MODEL_N_OBS, MODEL_N_OBS, "628 (mensuales)"],
    }
    st.dataframe(pd.DataFrame(perf_data), use_container_width=True, hide_index=True)

    oof_result = get_oof()
    if oof_result["ok"]:
        oof_data = oof_result["data"]
        if oof_data:
            st.markdown('<div class="section-label" style="margin-top:16px;">Predicciones Out-of-Fold (OOF)</div>', unsafe_allow_html=True)
            oof_df = pd.DataFrame(oof_data)
            st.dataframe(oof_df, use_container_width=True, hide_index=True)
            st.caption("Predicciones generadas por validacion cruzada leave-one-out en el set de entrenamiento.")

    st.markdown(f"""
**Metricas del trigger (umbral {TRIGGER_THRESHOLD}%):**
- Recall: {MODEL_RECALL:.0%} ({int(MODEL_RECALL * 7)}/7 eventos detectados)
- N observaciones anuales: {MODEL_N_OBS}
- N eventos historicos de perdida: 7
""")

# ─── Tab 4: Data Sources ─────────────────────────────────────────────────────
with tab_data:
    st.markdown('<div class="section-label">Fuentes de datos</div>', unsafe_allow_html=True)

    sources = [
        {"Fuente": "CHIRPS", "Variable": "Precipitacion", "Resolucion": "0.05° (~5 km)", "Periodo": "2000-2026", "Frecuencia": "Mensual"},
        {"Fuente": "ERA5-Land", "Variable": "Temperatura del aire", "Resolucion": "0.1° (~9 km)", "Periodo": "2000-2026", "Frecuencia": "Mensual"},
        {"Fuente": "TerraClimate", "Variable": "Deficit hidrico, AET, PET", "Resolucion": "~4 km", "Periodo": "2000-2024", "Frecuencia": "Mensual"},
        {"Fuente": "MODIS MOD13", "Variable": "NDVI, EVI", "Resolucion": "250 m", "Periodo": "2000-2026", "Frecuencia": "16 dias"},
        {"Fuente": "MODIS MOD17", "Variable": "GPP (productividad primaria)", "Resolucion": "500 m", "Periodo": "2000-2026", "Frecuencia": "8 dias"},
        {"Fuente": "MODIS MOD11", "Variable": "LST Day/Night", "Resolucion": "1 km", "Periodo": "2000-2026", "Frecuencia": "8 dias"},
        {"Fuente": "SRTM", "Variable": "Elevacion, pendiente", "Resolucion": "30 m", "Periodo": "Estatico", "Frecuencia": "---"},
        {"Fuente": "Agronet (MADR)", "Variable": "Produccion y rendimiento cafe", "Resolucion": "Departamental", "Periodo": "2007-2024", "Frecuencia": "Anual"},
        {"Fuente": "ICO", "Variable": "Precio internacional cafe", "Resolucion": "Nacional", "Periodo": "2000-2026", "Frecuencia": "Mensual"},
    ]
    st.dataframe(pd.DataFrame(sources), use_container_width=True, hide_index=True)

    st.markdown("""
**Departamentos cubiertos:** Risaralda y Cundinamarca

**Extraccion:** Google Earth Engine (GEE) con geometrias departamentales. Agregacion zonal por media.

**Anomalias:** Calculadas como desviacion porcentual respecto a la media historica 2000-2024 de cada variable y departamento.
""")

# ─── Tab 5: Limitations ──────────────────────────────────────────────────────
with tab_lim:
    st.markdown('<div class="section-label">Limitaciones conocidas</div>', unsafe_allow_html=True)

    st.markdown(f"""
**1. Muestra pequena**
- Solo {MODEL_N_OBS} observaciones anuales (18 anos x 2 departamentos).
- 7 eventos historicos de perdida significativa.
- El AUC-ROC del clasificador anual es 0.32 (inferior al azar).

**2. Capacidad discriminativa**
- El detector/trigger tiene recall = {MODEL_RECALL:.0%} pero precision limitada.
- Basis risk residual de ~5.5 pp en la configuracion optima.

**3. Extrapolacion**
- Los modelos fueron entrenados con datos 2007-2024. Predicciones fuera de este rango son extrapolaciones.
- El cambio climatico puede alterar las relaciones historicas entre indices y rendimiento.

**4. Agregacion espacial**
- Los datos satelitales se agregan a nivel departamental (media zonal).
- No captura variabilidad intra-departamental.

**5. Variables omitidas**
- No incluye variables agronomicas (variedad, edad del cafetal, practicas de manejo).
- No incluye plagas ni enfermedades (roya, broca).

**6. Modelo mensual (M4)**
- R-cuadrado negativo en test: el modelo no supera la prediccion por la media.
- MAE anualizado de {MODEL_MAE_MONTHLY_ANNUALIZED} pp.
- Util como alerta temprana relativa, no como prediccion absoluta.
""")

# ─── Tab 6: Pipeline ─────────────────────────────────────────────────────────
with tab_pipe:
    st.markdown('<div class="section-label">Estado del pipeline</div>', unsafe_allow_html=True)

    health = get_health_full()
    if health["ok"]:
        h = health["data"]

        p1, p2, p3 = st.columns(3)
        with p1:
            st.metric("Estado", h.get("status", "---"))
        with p2:
            st.metric("Modelos cargados", "Si" if h.get("models_loaded") else "No")
        with p3:
            st.metric("Datos frescos (dias)", h.get("data_freshness_days", "---"))

        p4, p5 = st.columns(2)
        with p4:
            st.metric("Entrenado en", h.get("trained_at", "---"))
        with p5:
            st.metric("Pipeline ultima ejecucion", h.get("pipeline_last_run", "---"))

        metrics = h.get("metrics")
        if metrics:
            st.markdown('<div class="section-label" style="margin-top:16px;">Metricas de modelos (en memoria)</div>', unsafe_allow_html=True)
            st.json(metrics)
    else:
        st.error(f"No se pudo obtener el estado: {health['error']}")

    st.markdown("""
**Pipeline de reentrenamiento:**
1. `run_pipeline.py` lee los datasets CSV de `PROYECTO_V2/BASE_DE_DATOS/FINALES/`
2. Entrena 3 modelos: XGBoost magnitud, HGB detector+trigger, HGB mensual
3. Genera 4 artefactos: backtest, OOF, historial mensual, correlaciones
4. Serializa modelos y metadata a `insumos/models/`
5. La API carga los `.pkl` al inicio y sirve predicciones en tiempo real
""")
