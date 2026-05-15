import streamlit as st

st.set_page_config(
    page_title="Metodologia -- Seguro Cafetero",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from components.sidebar import render_sidebar
from utils.api_client import get_correlations, get_oof, get_health_full, get_calibration
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
    "Arquitectura", "Correlaciones", "Desempeño", "Fuentes de datos", "Limitaciones", "Pipeline",
])

# ─── Tab 1: Architecture ─────────────────────────────────────────────────────
with tab_arch:
    st.markdown('<div class="section-label">Diagrama del sistema</div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="max-width:720px;margin:0 auto;font-family:Inter,sans-serif;">'
        '<div style="background:linear-gradient(135deg,#ECFDF5,#D1FAE5);border:2px solid #6EE7B7;border-radius:12px;padding:18px 24px;text-align:center;">'
        '<div style="font-weight:700;font-size:15px;color:#065F46;margin-bottom:6px;">'
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#065F46" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px;"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>'
        'Google Earth Engine</div>'
        '<div style="display:flex;justify-content:center;gap:8px;flex-wrap:wrap;">'
        '<span style="background:#fff;border:1px solid #A7F3D0;border-radius:6px;padding:3px 10px;font-size:12px;color:#047857;">CHIRPS</span>'
        '<span style="background:#fff;border:1px solid #A7F3D0;border-radius:6px;padding:3px 10px;font-size:12px;color:#047857;">ERA5</span>'
        '<span style="background:#fff;border:1px solid #A7F3D0;border-radius:6px;padding:3px 10px;font-size:12px;color:#047857;">MODIS</span>'
        '<span style="background:#fff;border:1px solid #A7F3D0;border-radius:6px;padding:3px 10px;font-size:12px;color:#047857;">TerraClimate</span>'
        '<span style="background:#fff;border:1px solid #A7F3D0;border-radius:6px;padding:3px 10px;font-size:12px;color:#047857;">SRTM</span>'
        '</div></div>'
        '<div style="text-align:center;font-size:22px;color:#94A3B8;line-height:1.2;padding:4px 0;">&darr;</div>'
        '<div style="background:linear-gradient(135deg,#F5F3FF,#EDE9FE);border:2px solid #C4B5FD;border-radius:12px;padding:18px 24px;text-align:center;">'
        '<div style="font-weight:700;font-size:15px;color:#5B21B6;margin-bottom:4px;">'
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#5B21B6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px;"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>'
        'Limpieza, exploraci&oacute;n y experimentaci&oacute;n</div>'
        '<div style="font-size:12px;color:#6D28D9;">Notebooks + procesamiento de datos</div>'
        '<div style="display:flex;justify-content:center;gap:8px;margin-top:8px;flex-wrap:wrap;">'
        '<span style="background:#fff;border:1px solid #DDD6FE;border-radius:6px;padding:3px 10px;font-size:11px;color:#7C3AED;font-family:monospace;">dataset_anual.csv</span>'
        '<span style="background:#fff;border:1px solid #DDD6FE;border-radius:6px;padding:3px 10px;font-size:11px;color:#7C3AED;font-family:monospace;">dataset_mensual.csv</span>'
        '</div></div>'
        '<div style="text-align:center;font-size:22px;color:#94A3B8;line-height:1.2;padding:4px 0;">&darr;</div>'
        '<div style="background:linear-gradient(135deg,#EFF6FF,#DBEAFE);border:2px solid #93C5FD;border-radius:12px;padding:20px 24px;">'
        '<div style="text-align:center;font-weight:700;font-size:15px;color:#1E40AF;margin-bottom:12px;">'
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1E40AF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px;"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>'
        'seguro-cafe-api <span style="font-weight:400;font-size:12px;color:#3B82F6;">(FastAPI)</span></div>'
        '<div style="display:flex;justify-content:center;gap:10px;margin-bottom:14px;flex-wrap:wrap;">'
        '<div style="background:#fff;border:1px solid #BFDBFE;border-radius:8px;padding:10px 14px;text-align:center;min-width:140px;">'
        '<div style="font-weight:700;font-size:13px;color:#1E40AF;">M1: XGBoost</div>'
        '<div style="font-size:11px;color:#64748B;">Magnitud &middot; 10 vars</div></div>'
        '<div style="background:#fff;border:1px solid #BFDBFE;border-radius:8px;padding:10px 14px;text-align:center;min-width:140px;">'
        '<div style="font-weight:700;font-size:13px;color:#1E40AF;">M2/M3: HGB</div>'
        '<div style="font-size:11px;color:#64748B;">Detector + Trigger &middot; 18 vars</div></div>'
        '<div style="background:#fff;border:1px solid #BFDBFE;border-radius:8px;padding:10px 14px;text-align:center;min-width:140px;">'
        '<div style="font-weight:700;font-size:13px;color:#1E40AF;">M4: HGB Mensual</div>'
        '<div style="font-size:11px;color:#64748B;">Lags cosecha &middot; ~50 vars</div></div>'
        '</div>'
        '<div style="background:rgba(255,255,255,0.7);border-radius:8px;padding:10px 14px;">'
        '<div style="font-size:11px;font-weight:600;color:#3B82F6;margin-bottom:4px;">9 Endpoints:</div>'
        '<div style="display:flex;flex-wrap:wrap;gap:4px 8px;">'
        '<span style="font-size:10px;color:#475569;font-family:monospace;">POST /predict/annual</span>'
        '<span style="font-size:10px;color:#475569;font-family:monospace;">POST /predict/monthly</span>'
        '<span style="font-size:10px;color:#475569;font-family:monospace;">GET /data/backtest</span>'
        '<span style="font-size:10px;color:#475569;font-family:monospace;">GET /data/history</span>'
        '<span style="font-size:10px;color:#475569;font-family:monospace;">GET /data/monthly-history</span>'
        '<span style="font-size:10px;color:#475569;font-family:monospace;">GET /data/oof</span>'
        '<span style="font-size:10px;color:#475569;font-family:monospace;">GET /data/correlations</span>'
        '<span style="font-size:10px;color:#475569;font-family:monospace;">GET /calibrate/trigger</span>'
        '<span style="font-size:10px;color:#475569;font-family:monospace;">GET /health</span>'
        '</div></div></div>'
        '<div style="text-align:center;font-size:22px;color:#94A3B8;line-height:1.2;padding:4px 0;">&darr;</div>'
        '<div style="background:linear-gradient(135deg,#FFF7ED,#FED7AA);border:2px solid #FDBA74;border-radius:12px;padding:20px 24px;">'
        '<div style="text-align:center;font-weight:700;font-size:15px;color:#9A3412;margin-bottom:12px;">'
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9A3412" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px;"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>'
        'seguro-cafe-dashboard <span style="font-weight:400;font-size:12px;color:#C2410C;">(Streamlit)</span></div>'
        '<div style="display:flex;justify-content:center;gap:8px;flex-wrap:wrap;">'
        '<span style="background:#fff;border:1px solid #FED7AA;border-radius:6px;padding:5px 10px;font-size:11px;color:#1E40AF;font-weight:600;">P1 Evaluaci&oacute;n Anual</span>'
        '<span style="background:#fff;border:1px solid #FED7AA;border-radius:6px;padding:5px 10px;font-size:11px;color:#16A34A;font-weight:600;">P2 Monitoreo Mensual</span>'
        '<span style="background:#fff;border:1px solid #FED7AA;border-radius:6px;padding:5px 10px;font-size:11px;color:#D97706;font-weight:600;">P3 An&aacute;lisis Hist&oacute;rico</span>'
        '<span style="background:#fff;border:1px solid #FED7AA;border-radius:6px;padding:5px 10px;font-size:11px;color:#7C3AED;font-weight:600;">P4 Simulador</span>'
        '<span style="background:#fff;border:1px solid #FED7AA;border-radius:6px;padding:5px 10px;font-size:11px;color:#0891B2;font-weight:600;">P5 Metodolog&iacute;a</span>'
        '<span style="background:#fff;border:1px solid #FED7AA;border-radius:6px;padding:5px 10px;font-size:11px;color:#BE185D;font-weight:600;">P6 Score Mensual</span>'
        '</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

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
    # --- Checklist de criterios de exito ---
    st.markdown('<div class="section-label">Criterios de exito</div>', unsafe_allow_html=True)

    cal_result = get_calibration()
    br_actual = None
    if cal_result["ok"]:
        cal_df = pd.DataFrame(cal_result["data"])
        row14 = cal_df[cal_df["threshold_pct"] == int(TRIGGER_THRESHOLD)]
        if not row14.empty:
            br_actual = row14.iloc[0].get("basis_risk_medio_pp")

    criteria = [
        {"Criterio": "MAE ≤ 10 pp", "Objetivo": "≤ 10.00 pp", "Actual": f"{MODEL_MAE_ANNUAL:.2f} pp", "Cumple": MODEL_MAE_ANNUAL <= 10},
        {"Criterio": "Recall ≥ 0.70", "Objetivo": "≥ 70%", "Actual": f"{MODEL_RECALL:.0%}", "Cumple": MODEL_RECALL >= 0.70},
        {"Criterio": "Basis risk ≤ 8 pp", "Objetivo": "≤ 8.00 pp", "Actual": f"{br_actual:.2f} pp" if br_actual is not None else "pendiente", "Cumple": br_actual is not None and br_actual <= 8},
        {"Criterio": "Pipeline < 10 min", "Objetivo": "< 10 min", "Actual": "< 1 min", "Cumple": True},
    ]
    criteria_df = pd.DataFrame(criteria)
    criteria_df["Estado"] = criteria_df["Cumple"].map({True: "CUMPLE", False: "NO CUMPLE"})

    def _color_estado(val):
        if val == "CUMPLE":
            return "background-color: #DCFCE7; color: #166534;"
        return "background-color: #FEE2E2; color: #991B1B;"

    st.dataframe(
        criteria_df[["Criterio", "Objetivo", "Actual", "Estado"]].style.applymap(
            _color_estado, subset=["Estado"]
        ),
        use_container_width=True, hide_index=True,
    )
    n_pass = sum(c["Cumple"] for c in criteria)
    st.markdown(f"**Resultado: {n_pass}/{len(criteria)} criterios cumplidos.**")

    # --- Tabla modelo vs baseline ---
    st.markdown('<div class="section-label" style="margin-top:24px;">Comparacion modelo vs baseline</div>', unsafe_allow_html=True)

    perf_data = {
        "Modelo": [
            "Regresion lineal (baseline)",
            "M1 — XGBoost Magnitud",
            "M2/M3 — HGB Set A (Detector+Trigger)",
            "HGB baseline (mejor R²)",
            "M4 — HGB Mensual (anualizado)",
        ],
        "MAE (pp)": ["12.41", f"{MODEL_MAE_ANNUAL:.2f}", "10.13", "9.32", f"{MODEL_MAE_MONTHLY_ANNUALIZED:.2f}"],
        "R²": ["0.000", "0.011", "0.169", "0.379", "< 0"],
        "Recall (-14%)": ["0.00", "0.00", f"{MODEL_RECALL:.2f}", "0.00", "---"],
        "N obs": [MODEL_N_OBS, MODEL_N_OBS, MODEL_N_OBS, MODEL_N_OBS, "628 (mensuales)"],
        "Periodo prueba": ["2021-2024", "2021-2024", "2021-2024", "2021-2024", "2021-2024"],
    }
    st.dataframe(pd.DataFrame(perf_data), use_container_width=True, hide_index=True)
    st.caption(
        "M1 es el modelo seleccionado para estimar magnitud de perdida. "
        "M2/M3 usa el mismo HGB con umbrales distintos (detector -2.8%, trigger -14%). "
        "El baseline lineal sirve como referencia minima."
    )

    # --- Curva ROC ---
    st.markdown('<div class="section-label" style="margin-top:24px;">Curva ROC del clasificador (M2/M3)</div>', unsafe_allow_html=True)

    oof_result = get_oof()
    roc_plotted = False
    if oof_result["ok"] and oof_result["data"]:
        oof_df = pd.DataFrame(oof_result["data"])
        if "y_true" in oof_df.columns and "y_pred_m3" in oof_df.columns:
            oof_clean = oof_df.dropna(subset=["y_true", "y_pred_m3"])
            if len(oof_clean) >= 5:
                y_binary = (oof_clean["y_true"] <= -15).astype(int)
                scores = -oof_clean["y_pred_m3"].values

                sorted_idx = np.argsort(-scores)
                y_sorted = y_binary.values[sorted_idx]
                n_pos = y_sorted.sum()
                n_neg = len(y_sorted) - n_pos

                if n_pos > 0 and n_neg > 0:
                    tpr_list = [0.0]
                    fpr_list = [0.0]
                    tp_count = 0
                    fp_count = 0
                    for label in y_sorted:
                        if label == 1:
                            tp_count += 1
                        else:
                            fp_count += 1
                        tpr_list.append(tp_count / n_pos)
                        fpr_list.append(fp_count / n_neg)

                    auc_val = sum(
                        (fpr_list[i] - fpr_list[i - 1]) * (tpr_list[i] + tpr_list[i - 1]) / 2
                        for i in range(1, len(fpr_list))
                    )

                    fig_roc = go.Figure()
                    fig_roc.add_trace(go.Scatter(
                        x=fpr_list, y=tpr_list,
                        mode="lines",
                        line=dict(color="#1E40AF", width=2),
                        name=f"ROC (AUC = {auc_val:.2f})",
                        fill="tozeroy",
                        fillcolor="rgba(30,64,175,0.1)",
                    ))
                    fig_roc.add_trace(go.Scatter(
                        x=[0, 1], y=[0, 1],
                        mode="lines",
                        line=dict(color="#94A3B8", width=1, dash="dash"),
                        name="Azar (AUC = 0.50)",
                        showlegend=True,
                    ))
                    fig_roc.update_layout(
                        xaxis=dict(title="Tasa de Falsos Positivos (FPR)", range=[0, 1.02]),
                        yaxis=dict(title="Tasa de Verdaderos Positivos (TPR)", range=[0, 1.02]),
                        title=dict(text=f"Curva ROC — AUC = {auc_val:.2f}", font=dict(size=14)),
                        legend=dict(x=0.55, y=0.05),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=50, b=40, l=50, r=30),
                        width=550, height=450,
                    )
                    st.plotly_chart(fig_roc, use_container_width=True, config={"displayModeBar": False})
                    roc_plotted = True

    if not roc_plotted:
        st.info("No se pudieron calcular los datos para la curva ROC. Verifica que la API este corriendo.")

    st.markdown(
        "**AUC = 0.32** — discriminacion limitada por muestra de 36 observaciones anuales "
        "con solo 7 eventos de perdida significativa (≤ -15%). "
        "La curva ROC se calcula binarizando `y_true` en -15% y usando las predicciones OOF de M3."
    )

    # --- OOF table ---
    if oof_result["ok"] and oof_result["data"]:
        with st.expander("Predicciones Out-of-Fold (OOF)"):
            st.dataframe(pd.DataFrame(oof_result["data"]), use_container_width=True, hide_index=True)
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
- Solo {MODEL_N_OBS} observaciones anuales (18 años x 2 departamentos).
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
