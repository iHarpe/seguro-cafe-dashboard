import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from utils.defaults import DETECTOR_THRESHOLD, TRIGGER_THRESHOLD

_LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#1E293B", size=12),
    xaxis=dict(
        gridcolor="#E2E8F0", gridwidth=1, showline=False,
        tickfont=dict(size=11, color="#64748B"),
    ),
    yaxis=dict(
        gridcolor="#E2E8F0", gridwidth=1, showline=False,
        zeroline=True, zerolinecolor="#CBD5E1", zerolinewidth=1,
        tickfont=dict(size=11, color="#64748B"),
    ),
    margin=dict(t=40, b=40, l=50, r=80),
    hovermode="x unified",
    legend=dict(
        bgcolor="rgba(255,255,255,0.9)",
        borderwidth=1,
        bordercolor="#E2E8F0",
        font=dict(size=11),
    ),
)


def _add_thresholds(fig: go.Figure, y_range: tuple | None = None) -> go.Figure:
    fig.add_hline(
        y=DETECTOR_THRESHOLD,
        line_dash="dash", line_color="#F59E0B", line_width=1.5,
        annotation_text=f"Detector {DETECTOR_THRESHOLD}%",
        annotation_position="right",
        annotation_font_size=10,
        annotation_font_color="#D97706",
    )
    fig.add_hline(
        y=TRIGGER_THRESHOLD,
        line_dash="solid", line_color="#DC2626", line_width=2,
        annotation_text=f"Trigger {TRIGGER_THRESHOLD}%",
        annotation_position="right",
        annotation_font_size=10,
        annotation_font_color="#DC2626",
    )
    return fig


def plot_annual_score(df: pd.DataFrame) -> go.Figure:
    """Line chart: predicted annual score 2007-2024 for a single department."""
    fig = go.Figure()

    fig.add_vrect(
        x0=2007, x1=2020.5,
        fillcolor="rgba(219,234,254,0.35)", line_width=0,
        annotation_text="Entrenamiento", annotation_position="top left",
        annotation_font_size=10, annotation_font_color="#3B82F6",
    )
    fig.add_vrect(
        x0=2020.5, x1=2024,
        fillcolor="rgba(254,243,199,0.45)", line_width=0,
        annotation_text="Prueba (out-of-sample)", annotation_position="top right",
        annotation_font_size=10, annotation_font_color="#D97706",
    )

    if "perdida_real_pct" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["anio"], y=df["perdida_real_pct"],
            name="Pérdida real (Agronet)",
            mode="lines+markers",
            line=dict(color="#1E40AF", width=2),
            marker=dict(size=5, color="#1E40AF"),
            hovertemplate="%{y:.1f}%<extra>Real</extra>",
        ))

    if "score_anual" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["anio"], y=df["score_anual"],
            name="Predicción modelo",
            mode="lines+markers",
            line=dict(color="#F97316", width=2, dash="dot"),
            marker=dict(size=5, color="#F97316"),
            hovertemplate="%{y:.1f}%<extra>Modelo</extra>",
        ))

    _add_thresholds(fig)

    layout = dict(**_LAYOUT_BASE)
    layout["yaxis"] = dict(**_LAYOUT_BASE["yaxis"], ticksuffix="%", title="Variación (%)")
    layout["xaxis"] = dict(**_LAYOUT_BASE["xaxis"], title="Año", dtick=1)
    layout["title"] = dict(text="Pérdida Real vs Predicción del Modelo", font=dict(size=14, color="#1E293B"))
    fig.update_layout(**layout)
    return fig


def plot_historical_dual(df: pd.DataFrame) -> go.Figure:
    """Dual line chart for historical analysis page."""
    return plot_annual_score(df)


def plot_monthly_scores(records: list[dict]) -> go.Figure:
    """Line chart for monthly monitoring screen."""
    if not records:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin datos — ingresa registros mensuales",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=13, color="#94A3B8"),
        )
        fig.update_layout(**_LAYOUT_BASE)
        return fig

    df = pd.DataFrame(records)
    fig = go.Figure()

    harvest_months = [4, 5, 6, 10, 11, 12]
    month_labels = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

    for m in harvest_months:
        fig.add_vrect(
            x0=m - 0.5, x1=m + 0.5,
            fillcolor="rgba(240,253,244,0.6)", line_width=0,
        )

    if "score" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["mes"], y=df["score"],
            name="Score mensual",
            mode="lines+markers",
            line=dict(color="#1E40AF", width=2),
            marker=dict(
                size=8,
                color=df["score"].apply(
                    lambda s: "#DC2626" if s <= TRIGGER_THRESHOLD
                    else "#D97706" if s <= DETECTOR_THRESHOLD
                    else "#16A34A"
                ),
                line=dict(color="white", width=1.5),
            ),
            hovertemplate="Mes %{x} — Score: %{y:.1f}%<extra></extra>",
        ))

    _add_thresholds(fig)

    layout = dict(**_LAYOUT_BASE)
    layout["yaxis"] = dict(**_LAYOUT_BASE["yaxis"], ticksuffix="%", title="Score (%)")
    layout["xaxis"] = dict(
        **_LAYOUT_BASE["xaxis"],
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=month_labels,
        title="Mes",
    )
    layout["title"] = dict(text="Score mensual durante la cosecha", font=dict(size=14, color="#1E293B"))
    fig.update_layout(**layout)
    return fig


def plot_tornado(sensitivity_df: pd.DataFrame) -> go.Figure:
    """Horizontal tornado chart for scenario sensitivity analysis."""
    if sensitivity_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin datos de sensibilidad",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=13, color="#94A3B8"),
        )
        fig.update_layout(**_LAYOUT_BASE)
        return fig

    df = sensitivity_df.sort_values("delta_pp", key=abs, ascending=True)

    colors = [
        "#16A34A" if v >= 0 else "#DC2626"
        for v in df["delta_pp"]
    ]

    fig = go.Figure(go.Bar(
        x=df["delta_pp"],
        y=df["variable_label"],
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Δ predicción: %{x:+.2f} pp<extra></extra>",
        text=[f"{v:+.1f} pp" for v in df["delta_pp"]],
        textposition="outside",
        textfont=dict(size=11, color="#64748B"),
    ))

    fig.add_vline(x=0, line_color="#CBD5E1", line_width=1.5)

    layout = dict(**_LAYOUT_BASE)
    layout["xaxis"] = dict(
        **_LAYOUT_BASE["xaxis"],
        title="Cambio en predicción (pp)",
        ticksuffix=" pp",
        zeroline=True, zerolinecolor="#CBD5E1",
    )
    layout["yaxis"] = dict(
        gridcolor="rgba(0,0,0,0)", showline=False,
        tickfont=dict(size=11, color="#1E293B"),
    )
    layout["title"] = dict(
        text="Sensibilidad del modelo por variable (±10%)",
        font=dict(size=14, color="#1E293B"),
    )
    layout["margin"] = dict(t=50, b=40, l=200, r=80)
    fig.update_layout(**layout)
    return fig
