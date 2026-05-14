import streamlit as st
from pathlib import Path
from utils.defaults import DEFAULT_DEPARTMENT, DEFAULT_YEAR, DEFAULT_MODE


def render_sidebar() -> bool:
    """Render shared sidebar: navigation + config + API status. Returns api_ok."""
    css_path = Path(__file__).parent.parent / "assets" / "style.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )

    # Init session state keys before widgets create them
    if "department" not in st.session_state:
        st.session_state["department"] = DEFAULT_DEPARTMENT
    if "year" not in st.session_state:
        st.session_state["year"] = DEFAULT_YEAR
    if "mode" not in st.session_state:
        st.session_state["mode"] = DEFAULT_MODE

    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">☕ Seguro Cafetero</div>',
            unsafe_allow_html=True,
        )

        # ─── Navigation ───────────────────────────────────────────────────────
        st.markdown(
            '<div class="section-label">Navegación</div>',
            unsafe_allow_html=True,
        )
        st.page_link("app.py",                          label="Inicio",                      icon="🏠")
        st.page_link("pages/1_Alerta_Actual.py",        label="Evaluación de Riesgo Anual",  icon="⚠️")
        st.page_link("pages/2_Monitoreo_Mensual.py",    label="Monitoreo Mensual",           icon="📊")
        st.page_link("pages/3_Historico.py",            label="Análisis Histórico",          icon="📈")
        st.page_link("pages/4_Escenarios.py",           label="Escenarios What-If",          icon="🎛️")

        # ─── Config ───────────────────────────────────────────────────────────
        st.markdown(
            '<div class="section-label" style="margin-top:16px;">Configuración</div>',
            unsafe_allow_html=True,
        )
        st.selectbox(
            "Departamento",
            options=["Risaralda", "Cundinamarca"],
            index=0 if st.session_state["department"] == "Risaralda" else 1,
            key="department",
            help="Departamento caficultor a analizar",
        )
        st.slider(
            "Año de análisis",
            min_value=2007, max_value=2024,
            value=st.session_state["year"],
            step=1, key="year",
        )
        st.radio(
            "Modo de análisis",
            options=["Básico", "Técnico"],
            index=0 if st.session_state["mode"] == "Básico" else 1,
            key="mode",
            help=(
                "Básico: 10 variables climáticas siempre disponibles.  \n"
                "Técnico: +7 variables satelitales adicionales (MODIS/TerraClimate)."
            ),
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

        st.markdown("---")
        st.caption(
            "Seguro Agrícola Indexado · PAAD 2026  \n"
            "Universidad de los Andes"
        )

    return api_ok
