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
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">☕ Seguro Cafetero</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">Configuración</div>', unsafe_allow_html=True)

    department = st.selectbox(
        "Departamento",
        options=["Risaralda", "Cundinamarca"],
        index=0 if st.session_state["department"] == "Risaralda" else 1,
        key="department",
        help="Departamento caficultor a analizar",
    )

    year = st.slider(
        "Año de análisis",
        min_value=2007,
        max_value=2024,
        value=st.session_state["year"],
        step=1,
        key="year",
        help="Año para la evaluación anual de riesgo",
    )

    mode = st.radio(
        "Modo de análisis",
        options=["Básico", "Técnico"],
        index=0 if st.session_state["mode"] == "Básico" else 1,
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

    st.markdown("---")
    st.caption(
        "Modelo Seguro Agrícola Indexado · PAAD 2026  \n"
        "Maestría en Inteligencia Analítica de Datos  \n"
        "Universidad de los Andes"
    )

# ─── Home page ────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="page-title">Panel de Análisis — Seguro Agrícola Indexado</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="page-subtitle">Selecciona una sección en el menú de la izquierda para comenzar.</div>',
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
**Evaluación de Riesgo Anual**
Ingresa variables climáticas del año y obtén una estimación de pérdida con el nivel de riesgo del seguro.
""")

with col2:
    st.markdown("""
**Monitoreo Mensual**
Seguimiento durante la cosecha. Detecta señales de alerta antes de que termine el ciclo anual.
""")

with col3:
    st.markdown("""
**Análisis Histórico**
Backtesting 2007–2024: cuándo habría pagado el seguro y cuál fue el basis risk promedio.
""")
