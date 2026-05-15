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

    pred_col = next((c for c in ("prediccion_m1_pct", "score_anual") if c in df.columns), None)
    if pred_col:
        fig.add_trace(go.Scatter(
            x=df["anio"], y=df[pred_col],
            name="Prediccion modelo (M1)",
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


def plot_historical_triple(df: pd.DataFrame) -> go.Figure:
    """3-series grouped bar: pago seguro, perdida real, sin seguro."""
    fig = go.Figure()

    avg_event_severity = 22.0  # approximate from spec
    sin_seguro = df["perdida_real_pct"].apply(
        lambda x: avg_event_severity if x <= -15 else 0
    )

    fig.add_trace(go.Bar(
        x=df["anio"], y=df["pago_pp"],
        name="Pago seguro",
        marker_color="#3B82F6",
        hovertemplate="Pago: %{y:.1f} pp<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df["anio"], y=df["perdida_real_pct"].abs(),
        name="Perdida real (Agronet)",
        marker_color="#F97316",
        hovertemplate="Perdida: %{y:.1f} pp<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df["anio"], y=sin_seguro,
        name="Sin seguro (severidad media)",
        marker_color="#94A3B8",
        hovertemplate="Sin seguro: %{y:.1f} pp<extra></extra>",
    ))

    layout = dict(**_LAYOUT_BASE)
    layout["barmode"] = "group"
    layout["yaxis"] = dict(**_LAYOUT_BASE["yaxis"], ticksuffix=" pp", title="Puntos porcentuales")
    layout["xaxis"] = dict(**_LAYOUT_BASE["xaxis"], title="Ano", dtick=1)
    layout["title"] = dict(text="Comparacion: Pago del seguro vs Perdida real", font=dict(size=14, color="#1E293B"))
    fig.update_layout(**layout)
    return fig


def plot_calibration_curves(cal_data: list[dict]) -> go.Figure:
    """Dual-axis: recall + basis risk vs trigger threshold."""
    df = pd.DataFrame(cal_data).sort_values("threshold_pct")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["threshold_pct"], y=df["recall"],
        name="Recall",
        mode="lines+markers",
        line=dict(color="#16A34A", width=2),
        marker=dict(size=5),
        hovertemplate="Umbral: %{x}%<br>Recall: %{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["threshold_pct"],
        y=df["basis_risk_medio_pp"],
        name="Basis risk (pp)",
        mode="lines+markers",
        line=dict(color="#DC2626", width=2, dash="dash"),
        marker=dict(size=5),
        yaxis="y2",
        hovertemplate="Umbral: %{x}%<br>BR: %{y:.1f} pp<extra></extra>",
    ))

    layout = dict(**_LAYOUT_BASE)
    layout["xaxis"] = dict(**_LAYOUT_BASE["xaxis"], title="Umbral de trigger (%)", ticksuffix="%")
    layout["yaxis"] = dict(**_LAYOUT_BASE["yaxis"], title="Recall", range=[0, 1.05])
    layout["yaxis2"] = dict(
        title="Basis risk (pp)", overlaying="y", side="right",
        showgrid=False, ticksuffix=" pp",
        title_font=dict(color="#DC2626"), tickfont=dict(color="#DC2626"),
    )
    layout["title"] = dict(text="Sensibilidad: Recall y Basis Risk vs Umbral", font=dict(size=14, color="#1E293B"))
    layout["legend"] = dict(**_LAYOUT_BASE["legend"], x=0.02, y=0.98)
    fig.update_layout(**layout)
    return fig


def plot_tradeoff_scatter(cal_data: list[dict], current_thr: float = -14.0) -> go.Figure:
    """Scatter: recall (x) vs basis risk (y), highlight current threshold."""
    df = pd.DataFrame(cal_data).dropna(subset=["recall", "basis_risk_medio_pp"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["recall"], y=df["basis_risk_medio_pp"],
        mode="markers+text",
        text=df["threshold_pct"].apply(lambda t: f"{t:.0f}%"),
        textposition="top center",
        textfont=dict(size=9, color="#64748B"),
        marker=dict(size=8, color="#3B82F6", opacity=0.6),
        hovertemplate="Recall: %{x:.2f}<br>BR: %{y:.1f} pp<br>Umbral: %{text}<extra></extra>",
        name="Configuraciones",
    ))

    current = df[df["threshold_pct"] == current_thr]
    if not current.empty:
        fig.add_trace(go.Scatter(
            x=current["recall"], y=current["basis_risk_medio_pp"],
            mode="markers",
            marker=dict(size=14, color="#DC2626", symbol="star", line=dict(width=2, color="white")),
            name=f"Actual ({current_thr:.0f}%)",
            hovertemplate="Recall: %{x:.2f}<br>BR: %{y:.1f} pp<extra>Actual</extra>",
        ))

    layout = dict(**_LAYOUT_BASE)
    layout["xaxis"] = dict(**_LAYOUT_BASE["xaxis"], title="Recall", range=[0, 1.05])
    layout["yaxis"] = dict(**_LAYOUT_BASE["yaxis"], title="Basis Risk medio (pp)", ticksuffix=" pp")
    layout["title"] = dict(text="Trade-off: Recall vs Basis Risk", font=dict(size=14, color="#1E293B"))
    fig.update_layout(**layout)
    return fig


def plot_monthly_history_full(df: pd.DataFrame) -> go.Figure:
    """Full M4 score trajectory with harvest shading and threshold lines."""
    fig = go.Figure()

    df = df.sort_values(["anio", "mes"])
    df["fecha"] = pd.to_datetime(df["anio"].astype(str) + "-" + df["mes"].astype(str) + "-01")

    for depto in df["departamento"].unique():
        d = df[df["departamento"] == depto]
        color = "#1E40AF" if depto == "Risaralda" else "#16A34A"
        fig.add_trace(go.Scatter(
            x=d["fecha"], y=d["score_m4"],
            name=depto,
            mode="lines",
            line=dict(color=color, width=1.5),
            hovertemplate="%{x|%Y-%m}<br>Score: %{y:.1f}%<extra>" + depto + "</extra>",
        ))

    harvest_months = {4, 5, 6, 10, 11, 12}
    years = df["anio"].unique()
    for yr in years:
        for m in harvest_months:
            x0 = pd.Timestamp(f"{yr}-{m}-01")
            x1 = x0 + pd.DateOffset(months=1)
            fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(240,253,244,0.3)", line_width=0)

    _add_thresholds(fig)

    layout = dict(**_LAYOUT_BASE)
    layout["yaxis"] = dict(**_LAYOUT_BASE["yaxis"], ticksuffix="%", title="Score M4 (%)")
    layout["xaxis"] = dict(**_LAYOUT_BASE["xaxis"], title="Fecha")
    layout["title"] = dict(text="Trayectoria historica del Score Mensual (M4)", font=dict(size=14, color="#1E293B"))
    fig.update_layout(**layout)
    return fig
