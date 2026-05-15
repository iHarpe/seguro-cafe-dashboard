import streamlit as st
from pathlib import Path
from urllib.parse import quote
from utils.defaults import DEFAULT_DEPARTMENT, DEFAULT_YEAR, DEFAULT_MODE

# SVG icons — same paths used in home page cards, resized to 16×16
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

_NAV_ITEMS = [
    ("/",                  _SVG_HOME,  "#5C3D2E", "#FDF6F0", "Inicio"),
    ("/Alerta_Actual",     _SVG_ALERT, "#1E40AF", "#EFF6FF", "Evaluación de Riesgo Anual"),
    ("/Monitoreo_Mensual", _SVG_CHART, "#16A34A", "#F0FDF4", "Monitoreo Mensual"),
    ("/Historico",         _SVG_HIST,  "#D97706", "#FFF7ED", "Análisis Histórico"),
    ("/Simulador",         _SVG_SCEN,  "#7C3AED", "#F5F3FF", "Simulador Actuarial"),
    ("/Score_Mensual",     _SVG_PULSE, "#BE185D", "#FDF2F8", "Score Mensual"),
    ("/Metodologia",       _SVG_BOOK,  "#0891B2", "#ECFEFF", "Metodología"),
]


def _nav_html() -> str:
    # Config is embedded in the href so it survives across full-page navigations.
    dept = st.session_state.get("department", DEFAULT_DEPARTMENT)
    yr   = st.session_state.get("year", DEFAULT_YEAR)
    mode = st.session_state.get("mode", DEFAULT_MODE)
    qs   = f"?dept={quote(str(dept))}&yr={yr}&mode={quote(str(mode))}"
    items = []
    for href, svg, color, bg, label in _NAV_ITEMS:
        items.append(
            f'<a href="{href}{qs}" target="_self" class="sb-nav-item">'
            f'<span class="sb-nav-icon" style="color:{color};background:{bg};">{svg}</span>'
            f'<span class="sb-nav-label">{label}</span>'
            f'</a>'
        )
    return '<div class="sb-nav">' + "".join(items) + "</div>"


def render_sidebar() -> bool:
    """Render shared sidebar: navigation + config + API status. Returns api_ok."""
    css_path = Path(__file__).parent.parent / "assets" / "style.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )

    # Fixed top header (injected into main content area, position:fixed spans full width)
    st.markdown(
        '<div class="custom-top-header">☕ Seguro Cafetero</div>',
        unsafe_allow_html=True,
    )

    # Initialize from URL query params first so config persists across full-page
    # navigations (HTML <a> links cause a new browser request and a fresh session).
    # Falls back to defaults when no params are present (first visit).
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

    with st.sidebar:
        # ─── Navigation ───────────────────────────────────────────────────────
        st.markdown(
            '<div class="section-label" style="margin-top:0;">Navegación</div>',
            unsafe_allow_html=True,
        )
        st.markdown(_nav_html(), unsafe_allow_html=True)

        # ─── Config ───────────────────────────────────────────────────────────
        st.markdown(
            '<div class="section-label" style="margin-top:16px;">Configuración</div>',
            unsafe_allow_html=True,
        )
        st.selectbox(
            "Departamento",
            options=["Risaralda", "Cundinamarca"],
            key="department",
            help="Departamento caficultor a analizar",
        )

        # ─── API status ───────────────────────────────────────────────────────
        st.markdown(
            '<div class="section-label" style="margin-top:16px;">Servicio</div>',
            unsafe_allow_html=True,
        )
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
            st.caption("Ejecuta en otra terminal:  \n`uvicorn src.api.main:app --port 8000`")

        st.markdown(
            '<div class="sidebar-footer">Seguro Agrícola Indexado</div>',
            unsafe_allow_html=True,
        )

    return api_ok
