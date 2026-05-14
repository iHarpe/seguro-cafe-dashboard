from utils.defaults import MODEL_N_OBS, MODEL_MAE_ANNUAL, MODEL_RECALL


_WARN_SVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'


def render_disclaimer(detail_level: str = "basic") -> str:
    basic_text = (
        f"<strong>Resultado indicativo</strong> — Este modelo fue entrenado con "
        f"{MODEL_N_OBS} observaciones ({MODEL_N_OBS // 2} años × 2 departamentos). "
        f"Los resultados son señales de alerta, no diagnósticos definitivos."
    )

    if detail_level == "basic":
        return f"""
<div class="disclaimer-card">
  <div class="disclaimer-icon">{_WARN_SVG}</div>
  <div class="disclaimer-body">{basic_text}</div>
</div>
"""

    details_html = f"""
<details style="margin-top:8px;">
  <summary style="font-size:12px; color:#92400E; cursor:pointer; font-weight:600;">
    Ver métricas técnicas del modelo
  </summary>
  <table style="font-size:12px; color:#78350F; margin-top:8px; border-collapse:collapse; width:100%;">
    <tr><td style="padding:4px 8px 4px 0; color:#92400E; font-weight:600;">Observaciones de entrenamiento</td><td style="padding:4px 0; font-variant-numeric:tabular-nums;">{MODEL_N_OBS} (18 años × 2 departamentos)</td></tr>
    <tr><td style="padding:4px 8px 4px 0; color:#92400E; font-weight:600;">MAE modelo anual (XGBoost)</td><td style="padding:4px 0; font-variant-numeric:tabular-nums;">{MODEL_MAE_ANNUAL} pp</td></tr>
    <tr><td style="padding:4px 8px 4px 0; color:#92400E; font-weight:600;">Recall del trigger</td><td style="padding:4px 0; font-variant-numeric:tabular-nums;">{MODEL_RECALL} (detecta ~{int(MODEL_RECALL*100)}% de los eventos reales)</td></tr>
    <tr><td style="padding:4px 8px 4px 0; color:#92400E; font-weight:600;">Cobertura geográfica</td><td style="padding:4px 0;">Solo Risaralda y Cundinamarca</td></tr>
    <tr><td style="padding:4px 8px 4px 0; color:#92400E; font-weight:600;">Período de entrenamiento</td><td style="padding:4px 0;">2007–2020</td></tr>
    <tr><td style="padding:4px 8px 4px 0; color:#92400E; font-weight:600;">Período de prueba (out-of-sample)</td><td style="padding:4px 0;">2021–2024</td></tr>
  </table>
</details>
"""

    return f"""
<div class="disclaimer-card">
  <div class="disclaimer-icon">{_WARN_SVG}</div>
  <div class="disclaimer-body">
    {basic_text}
    {details_html}
  </div>
</div>
"""
