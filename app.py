import streamlit as st
from pathlib import Path

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

# ─── Shared session state defaults ────────────────────────────────────────────
from utils.defaults import DEFAULT_DEPARTMENT, DEFAULT_YEAR, DEFAULT_MODE

if "department" not in st.session_state:
    st.session_state["department"] = DEFAULT_DEPARTMENT
if "year" not in st.session_state:
    st.session_state["year"] = DEFAULT_YEAR
if "mode" not in st.session_state:
    st.session_state["mode"] = DEFAULT_MODE
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

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
_NAV_HTML = (
    '<div class="sb-nav">'
    f'<a href="/" target="_self" class="sb-nav-item">'
    f'<span class="sb-nav-icon" style="color:#5C3D2E;background:#FDF6F0;">{_SVG_HOME}</span>'
    '<span class="sb-nav-label">Inicio</span></a>'
    f'<a href="/Alerta_Actual" target="_self" class="sb-nav-item">'
    f'<span class="sb-nav-icon" style="color:#1E40AF;background:#EFF6FF;">{_SVG_ALERT}</span>'
    '<span class="sb-nav-label">Evaluación de Riesgo Anual</span></a>'
    f'<a href="/Monitoreo_Mensual" target="_self" class="sb-nav-item">'
    f'<span class="sb-nav-icon" style="color:#16A34A;background:#F0FDF4;">{_SVG_CHART}</span>'
    '<span class="sb-nav-label">Monitoreo Mensual</span></a>'
    f'<a href="/Historico" target="_self" class="sb-nav-item">'
    f'<span class="sb-nav-icon" style="color:#D97706;background:#FFF7ED;">{_SVG_HIST}</span>'
    '<span class="sb-nav-label">Análisis Histórico</span></a>'
    f'<a href="/Escenarios" target="_self" class="sb-nav-item">'
    f'<span class="sb-nav-icon" style="color:#7C3AED;background:#F5F3FF;">{_SVG_SCEN}</span>'
    '<span class="sb-nav-label">Escenarios What-If</span></a>'
    '</div>'
)

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">☕ Seguro Cafetero</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">Navegación</div>', unsafe_allow_html=True)
    st.markdown(_NAV_HTML, unsafe_allow_html=True)

    st.markdown('<div class="section-label" style="margin-top:16px;">Configuración</div>', unsafe_allow_html=True)

    st.selectbox(
        "Departamento",
        options=["Risaralda", "Cundinamarca"],
        index=0 if st.session_state.get("department", DEFAULT_DEPARTMENT) == "Risaralda" else 1,
        key="department",
        help="Departamento caficultor a analizar",
    )

    st.slider(
        "Año de análisis",
        min_value=2007, max_value=2024,
        value=st.session_state.get("year", DEFAULT_YEAR),
        step=1, key="year",
        help="Año para la evaluación anual de riesgo",
    )

    st.radio(
        "Modo de análisis",
        options=["Básico", "Técnico"],
        index=0 if st.session_state.get("mode", DEFAULT_MODE) == "Básico" else 1,
        key="mode",
        help="Básico: 10 variables siempre disponibles. Técnico: +8 variables satelitales.",
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
        '<div class="sidebar-footer">Seguro Agrícola Indexado · MIAD</div>',
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
        <span class="home-stat-value">3</span>
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

NAV_SVG_ALERT = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
NAV_SVG_CHART = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
NAV_SVG_HIST  = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'
NAV_SVG_SCEN  = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 010 14.14M4.93 4.93a10 10 0 000 14.14"/></svg>'

def _nav_card_html(icon_svg, icon_style, title, desc, tags):
    tags_html = "".join(f'<span class="nav-tag">{t}</span>' for t in tags)
    return f"""
<div class="nav-card-visual">
  <div class="nav-card-icon" style="{icon_style}">{icon_svg}</div>
  <div class="nav-card-body">
    <div class="nav-card-title">{title}</div>
    <div class="nav-card-desc">{desc}</div>
    <div class="nav-card-tags">{tags_html}</div>
  </div>
</div>"""

r1c1, r1c2 = st.columns(2, gap="medium")
r2c1, r2c2 = st.columns(2, gap="medium")

with r1c1:
    st.markdown(_nav_card_html(
        NAV_SVG_ALERT, "background:#EFF6FF; color:#1E40AF;",
        "Evaluación de Riesgo Anual",
        "Ingresa variables climáticas y obtén la predicción de pérdida con semáforo de riesgo.",
        ["XGBoost", "MAE 9.6 pp", "Semana 6"],
    ), unsafe_allow_html=True)
    st.page_link("pages/1_Alerta_Actual.py", label="Ir a Evaluación de Riesgo Anual", use_container_width=True)

with r1c2:
    st.markdown(_nav_card_html(
        NAV_SVG_CHART, "background:#F0FDF4; color:#16A34A;",
        "Monitoreo Mensual",
        "Detecta señales de alerta durante la cosecha (abr–jun, oct–dic) antes de que termine el ciclo.",
        ["HGB Mensual", "MAE 11.1 pp", "Cosecha"],
    ), unsafe_allow_html=True)
    st.page_link("pages/2_Monitoreo_Mensual.py", label="Ir a Monitoreo Mensual", use_container_width=True)

with r2c1:
    st.markdown(_nav_card_html(
        NAV_SVG_HIST, "background:#FFF7ED; color:#D97706;",
        "Análisis Histórico",
        "Backtesting 2007–2024: frecuencia del trigger, basis risk promedio y descarga de datos.",
        ["Agronet", "2007–2024", "CSV Export"],
    ), unsafe_allow_html=True)
    st.page_link("pages/3_Historico.py", label="Ir a Análisis Histórico", use_container_width=True)

with r2c2:
    st.markdown(_nav_card_html(
        NAV_SVG_SCEN, "background:#F5F3FF; color:#7C3AED;",
        "Escenarios What-If",
        "Ajusta variables climáticas y analiza la sensibilidad del modelo con gráfico tornado.",
        ["Sliders", "Tornado chart", "R11"],
    ), unsafe_allow_html=True)
    st.page_link("pages/4_Escenarios.py", label="Ir a Escenarios What-If", use_container_width=True)

# ─── Model summary strip ──────────────────────────────────────────────────────
st.markdown("""
<div class="model-strip">
  <div class="model-strip-title">Modelos entrenados</div>
  <div class="model-strip-items">
    <div class="model-item">
      <div class="model-item-name">XGBoost — Magnitud</div>
      <div class="model-item-meta">10 vars · MAE 9.63 pp · anual</div>
    </div>
    <div class="model-strip-sep"></div>
    <div class="model-item">
      <div class="model-item-name">HGB — Detector / Trigger</div>
      <div class="model-item-meta">18 vars · umbral −2.8% / −14%</div>
    </div>
    <div class="model-strip-sep"></div>
    <div class="model-item">
      <div class="model-item-name">HGB — Alerta Mensual</div>
      <div class="model-item-meta">~35 vars · lags cosecha · MAE 11.1 pp</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
