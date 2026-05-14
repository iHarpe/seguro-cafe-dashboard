from utils.defaults import DETECTOR_THRESHOLD, TRIGGER_THRESHOLD


def fmt_pct(val: float | None, decimals: int = 1) -> str:
    if val is None:
        return "—"
    return f"{val:+.{decimals}f}%"


def fmt_pp(val: float | None, decimals: int = 1) -> str:
    if val is None:
        return "—"
    return f"{abs(val):.{decimals}f} pp"


def fmt_num(val: float | None, unit: str = "", decimals: int = 1) -> str:
    if val is None:
        return "—"
    s = f"{val:.{decimals}f}"
    return f"{s} {unit}".strip()


def level_from_score(score: float | None) -> str:
    """Return risk level string from annual score (percentage)."""
    if score is None:
        return "unknown"
    if score <= TRIGGER_THRESHOLD:
        return "alert"
    if score <= DETECTOR_THRESHOLD:
        return "caution"
    return "normal"


def label_for_level(level: str) -> str:
    return {
        "normal":  "Normal",
        "caution": "Precaución",
        "alert":   "Alerta",
        "unknown": "—",
    }.get(level, "—")


def color_for_level(level: str) -> str:
    return {
        "normal":  "#16A34A",
        "caution": "#D97706",
        "alert":   "#DC2626",
        "unknown": "#94A3B8",
    }.get(level, "#94A3B8")


def trigger_status(score: float | None) -> tuple[str, str]:
    """Return (status_label, css_class) for trigger KPI card."""
    if score is None:
        return "—", "unknown"
    if score <= TRIGGER_THRESHOLD:
        return "Activado", "alert"
    return "No activado", "normal"


def basis_risk_label(real_loss: float | None, predicted: float | None) -> str:
    if real_loss is None or predicted is None:
        return "—"
    diff = real_loss - predicted
    return fmt_pp(diff)
