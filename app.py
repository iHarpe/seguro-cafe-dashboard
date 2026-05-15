import streamlit as st
from pathlib import Path
from urllib.parse import quote

st.set_page_config(
    page_title="Seguro Cafetero",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Inject global CSS ────────────────────────────────────────────────────────
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ─── Custom fixed top header ─────────────────────────────────────────────────
st.markdown(
    '<div class="custom-top-header">☕ Seguro Cafetero</div>',
    unsafe_allow_html=True,
)

# ─── Shared session state defaults ────────────────────────────────────────────
from utils.defaults import DEFAULT_DEPARTMENT, DEFAULT_YEAR, DEFAULT_MODE

# Initialize from URL query params first so config persists across full-page
# navigations (HTML <a> links cause a new browser request and a fresh session).
if "department" not in st.session_state:
    raw = st.query_params.get("dept", DEFAULT_DEPARTMENT)
    st.session_state["department"] = raw if raw in ["Risaralda", "Cundinamarca"] else DEFAULT_DEPARTMENT
if "year" not in st.session_state:
    try:
        yr = int(st.query_params.get("yr", str(DEFAULT_YEAR)))
        st.session_state["year"] = max(2007, min(2024, yr))
    except (ValueError, TypeError):
        st.session_state["year"] = DEFAULT_YEAR
if "mode" not in st.session_state:
    raw_mode = st.query_params.get("mode", DEFAULT_MODE)
    st.session_state["mode"] = raw_mode if raw_mode in ["Básico", "Técnico"] else DEFAULT_MODE
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

# Query string carrying current config — embedded in every nav href so that
# clicking a link preserves the config even when a fresh session is created.
_qs = (
    f"?dept={quote(st.session_state['department'])}"
    f"&yr={st.session_state['year']}"
    f"&mode={quote(st.session_state['mode'])}"
)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
_SVG_HOME = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>'
    '<polyline points="9 22 9 12 15 12 15 22"/></svg>'
)
_SVG_ALERT = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>'
    '<line x1="12" y1="9" x2="12" y2="13"/>'
    '<line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
)
_SVG_CHART = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
)
_SVG_HIST = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<line x1="18" y1="20" x2="18" y2="10"/>'
    '<line x1="12" y1="20" x2="12" y2="4"/>'
    '<line x1="6" y1="20" x2="6" y2="14"/></svg>'
)
_SVG_SCEN = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="3"/>'
    '<path d="M19.07 4.93a10 10 0 010 14.14M4.93 4.93a10 10 0 000 14.14"/></svg>'
)
_SVG_BOOK = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/>'
    '<path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>'
)
_SVG_PULSE = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
)

_NAV_ITEMS_SIDEBAR = [
    ("/",                  _SVG_HOME,  "#5C3D2E", "#FDF6F0", "Inicio"),
    ("/Alerta_Actual",     _SVG_ALERT, "#1E40AF", "#EFF6FF", "Evaluación de Riesgo Anual"),
    ("/Monitoreo_Mensual", _SVG_CHART, "#16A34A", "#F0FDF4", "Monitoreo Mensual"),
    ("/Historico",         _SVG_HIST,  "#D97706", "#FFF7ED", "Análisis Histórico"),
    ("/Simulador",         _SVG_SCEN,  "#7C3AED", "#F5F3FF", "Simulador Actuarial"),
    ("/Score_Mensual",     _SVG_PULSE, "#BE185D", "#FDF2F8", "Score Mensual"),
    ("/Metodologia",       _SVG_BOOK,  "#0891B2", "#ECFEFF", "Metodología"),
]

_sidebar_nav_parts = ['<div class="sb-nav">']
for _href, _svg, _color, _bg, _label in _NAV_ITEMS_SIDEBAR:
    _sidebar_nav_parts.append(
        f'<a href="{_href}{_qs}" target="_self" class="sb-nav-item">'
        f'<span class="sb-nav-icon" style="color:{_color};background:{_bg};">{_svg}</span>'
        f'<span class="sb-nav-label">{_label}</span></a>'
    )
_sidebar_nav_parts.append('</div>')
_SIDEBAR_NAV_HTML = "".join(_sidebar_nav_parts)

with st.sidebar:
    st.markdown('<div class="section-label" style="margin-top:0;">Navegación</div>', unsafe_allow_html=True)
    st.markdown(_SIDEBAR_NAV_HTML, unsafe_allow_html=True)

    st.markdown('<div class="section-label" style="margin-top:16px;">Configuración</div>', unsafe_allow_html=True)

    st.selectbox(
        "Departamento",
        options=["Risaralda", "Cundinamarca"],
        key="department",
        help="Departamento caficultor a analizar",
    )

    st.markdown('<div class="section-label" style="margin-top:24px;">Estado del servicio</div>', unsafe_allow_html=True)

    from utils.api_client import health_check
    api_ok = health_check()

    if api_ok:
        st.markdown(
            '<span class="status-badge status-badge-ok">'
            '<span class="status-dot"></span>API conectada</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="status-badge status-badge-error">'
            '<span class="status-dot"></span>API desconectada</span>',
            unsafe_allow_html=True,
        )
        st.caption("Ejecuta: `uvicorn src.api.main:app --port 8000`")

    st.markdown(
        '<div class="sidebar-footer">Seguro Agrícola Indexado</div>',
        unsafe_allow_html=True,
    )

# ─── Home page ────────────────────────────────────────────────────────────────
department = st.session_state.get("department", DEFAULT_DEPARTMENT)
year       = st.session_state.get("year", DEFAULT_YEAR)

api_color  = "#16A34A" if api_ok else "#DC2626"
api_label  = "Conectada" if api_ok else "Desconectada"
api_bg     = "#F0FDF4" if api_ok else "#FEF2F2"
api_border = "#BBF7D0" if api_ok else "#FECACA"

st.markdown(f"""
<div class="home-hero">
  <div class="home-hero-content">
    <div class="home-hero-badge">Sistema de Análisis de Riesgo Paramétrico</div>
    <h1 class="home-hero-title">Seguro Agrícola Indexado<br><span class="home-hero-accent">Sector Cafetero Colombiano</span></h1>
    <p class="home-hero-subtitle">
      Evalúa el riesgo climático, monitorea cosechas en tiempo real y analiza el historial de pagos del seguro
      paramétrico para <strong>{department}</strong> · Año {year}
    </p>
    <div class="home-hero-stats">
      <div class="home-stat">
        <span class="home-stat-value">2</span>
        <span class="home-stat-label">Departamentos</span>
      </div>
      <div class="home-stat-divider"></div>
      <div class="home-stat">
        <span class="home-stat-value">18</span>
        <span class="home-stat-label">Años de datos</span>
      </div>
      <div class="home-stat-divider"></div>
      <div class="home-stat">
        <span class="home-stat-value">4</span>
        <span class="home-stat-label">Modelos ML</span>
      </div>
      <div class="home-stat-divider"></div>
      <div class="home-stat">
        <span class="home-stat-value" style="color:{api_color}; background:{api_bg}; padding:2px 10px; border-radius:99px; font-size:13px; border:1px solid {api_border};">API {api_label}</span>
        <span class="home-stat-label">Servicio</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Navigation cards ─────────────────────────────────────────────────────────
st.markdown('<div class="section-label" style="margin-top:32px;">Secciones del dashboard</div>', unsafe_allow_html=True)

_NAV_SVG_ALERT = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
_NAV_SVG_CHART = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
_NAV_SVG_HIST  = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'
_NAV_SVG_SCEN  = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 010 14.14M4.93 4.93a10 10 0 000 14.14"/></svg>'
_NAV_SVG_BOOK  = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>'
_NAV_SVG_PULSE = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'


def _nav_card(href, svg, icon_style, color_class, title, desc, delay_ms=0):
    return f"""
<a href="{href}" target="_self" class="nav-card {color_class}" style="animation-delay:{delay_ms}ms">
  <div class="nav-card-icon" style="{icon_style}">{svg}</div>
  <div class="nav-card-body">
    <div class="nav-card-title">{title}</div>
    <div class="nav-card-desc">{desc}</div>
  </div>
  <div class="nav-card-arrow">›</div>
</a>"""


r1c1, r1c2 = st.columns(2, gap="medium")
r2c1, r2c2 = st.columns(2, gap="medium")

with r1c1:
    st.markdown(_nav_card(
        f"/Alerta_Actual{_qs}", _NAV_SVG_ALERT,
        "background:#EFF6FF; color:#1E40AF;", "nav-card--blue",
        "Evaluación de Riesgo Anual",
        "Ingresa variables climáticas y obtén la predicción de pérdida con semáforo de riesgo.",
        delay_ms=0,
    ), unsafe_allow_html=True)

with r1c2:
    st.markdown(_nav_card(
        f"/Monitoreo_Mensual{_qs}", _NAV_SVG_CHART,
        "background:#F0FDF4; color:#16A34A;", "nav-card--green",
        "Monitoreo Mensual",
        "Detecta señales de alerta durante la cosecha (abr–jun, oct–dic) antes de que termine el ciclo.",
        delay_ms=60,
    ), unsafe_allow_html=True)

with r2c1:
    st.markdown(_nav_card(
        f"/Historico{_qs}", _NAV_SVG_HIST,
        "background:#FFF7ED; color:#D97706;", "nav-card--amber",
        "Análisis Histórico",
        "Backtesting 2007–2024: historial de pérdidas reales y análisis de años críticos.",
        delay_ms=120,
    ), unsafe_allow_html=True)

with r2c2:
    st.markdown(_nav_card(
        f"/Simulador{_qs}", _NAV_SVG_SCEN,
        "background:#F5F3FF; color:#7C3AED;", "nav-card--purple",
        "Simulador Actuarial",
        "Configura umbrales, cobertura y loading factor para evaluar el trade-off costo-riesgo del seguro.",
        delay_ms=180,
    ), unsafe_allow_html=True)

r3c1, r3c2 = st.columns(2, gap="medium")

with r3c1:
    st.markdown(_nav_card(
        f"/Score_Mensual{_qs}", _NAV_SVG_PULSE,
        "background:#FDF2F8; color:#BE185D;", "nav-card--pink",
        "Score Mensual (M4)",
        "Trayectoria histórica del score mensual de alerta temprana y comparación M4 vs M1.",
        delay_ms=240,
    ), unsafe_allow_html=True)

with r3c2:
    st.markdown(_nav_card(
        f"/Metodologia{_qs}", _NAV_SVG_BOOK,
        "background:#ECFEFF; color:#0891B2;", "nav-card--cyan",
        "Metodología",
        "Arquitectura del sistema, fuentes de datos, métricas de desempeño y limitaciones conocidas.",
        delay_ms=300,
    ), unsafe_allow_html=True)

# ─── Collapsible disclaimer (replaces model strip) ────────────────────────────
st.markdown("""
<details class="home-disclaimer-details">
  <summary>⚠️&nbsp; Resultado indicativo</summary>
  <div class="home-disclaimer-body">
    <p><strong>Los resultados de este dashboard son señales indicativas.</strong>
    Los modelos estadísticos fueron entrenados con datos históricos (2007–2024)
    de Risaralda y Cundinamarca. Las predicciones tienen un error promedio de ±9.6 pp (anual)
    y ±11.1 pp (mensual). Los umbrales y primas son valores de referencia actuariales.</p>
    <table>
      <tr><th>Modelo</th><th>Algoritmo</th><th>Entrenamiento</th><th>Prueba (out-of-sample)</th><th>MAE</th></tr>
      <tr><td>Magnitud anual</td><td>XGBoost</td><td>2007–2020</td><td>2021–2024</td><td>9.63 pp</td></tr>
      <tr><td>Detector / Trigger</td><td>HGB</td><td>2007–2020</td><td>2021–2024</td><td>—</td></tr>
      <tr><td>Alerta mensual</td><td>HGB + lags cosecha</td><td>2007–2020</td><td>2021–2024</td><td>11.08 pp</td></tr>
    </table>
  </div>
</details>
""", unsafe_allow_html=True)
