ACCENT_COLORS = {
    "normal":  "#16A34A",
    "caution": "#D97706",
    "alert":   "#DC2626",
    "unknown": "#94A3B8",
    "info":    "#1E40AF",
    "neutral": "#64748B",
}


def render_kpi_card(
    label: str,
    value: str,
    context: str = "",
    level: str = "neutral",
    tooltip: str = "",
) -> str:
    accent = ACCENT_COLORS.get(level, ACCENT_COLORS["neutral"])
    value_class = f"kpi-value kpi-value-{level}" if level in ("normal", "caution", "alert") else "kpi-value"
    title_attr = f'title="{tooltip}"' if tooltip else ""

    context_html = f'<div class="kpi-context">{context}</div>' if context else ""

    return f"""
<div class="kpi-card animate-fade-in" style="--kpi-accent: {accent};">
  <div class="kpi-label" {title_attr}>{label}</div>
  <div class="{value_class}">{value}</div>
  {context_html}
</div>
"""


def render_trigger_card(activated: bool, score: float | None) -> str:
    if score is None:
        return render_kpi_card(
            label="Estado del Trigger",
            value="—",
            context="umbral: −14.0%",
            level="neutral",
            tooltip="El trigger se activa cuando la pérdida estimada supera −14.0%",
        )

    if activated:
        return render_kpi_card(
            label="Estado del Trigger",
            value="Activado",
            context=f"score {score:+.1f}% ≤ umbral −14.0%",
            level="alert",
            tooltip="El trigger se activa cuando la pérdida estimada supera −14.0%",
        )
    return render_kpi_card(
        label="Estado del Trigger",
        value="No activado",
        context=f"score {score:+.1f}% > umbral −14.0%",
        level="normal",
        tooltip="El trigger se activa cuando la pérdida estimada supera −14.0%",
    )
