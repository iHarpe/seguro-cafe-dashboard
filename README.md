# Seguro Cafetero — Dashboard Analítico

Dashboard de análisis de riesgo para el **Seguro Agrícola Indexado Cafetero** de Colombia. Conecta con la API `seguro-cafe-api` para visualizar predicciones de pérdida, monitorear cosechas y explorar el histórico de pagos del seguro paramétrico.

## Pantallas

| Pantalla | Descripción |
|---|---|
| **1 — Evaluación de Riesgo Anual** | Ingresa variables climáticas anuales → obtiene pérdida estimada + nivel de riesgo (semáforo) |
| **2 — Monitoreo Mensual** | Seguimiento mensual durante la cosecha para detección temprana |
| **3 — Análisis Histórico** | Backtesting 2007–2024: frecuencia de trigger, basis risk promedio, descarga CSV |
| **4 — Escenarios What-If** | Sliders de variables → análisis de sensibilidad con gráfico tornado |

## Requisitos

- Python 3.11+
- [`seguro-cafe-api`](https://github.com/iHarpe/seguro-cafe-api) corriendo en `localhost:8000`

## Instalación

```bash
# 1. Clonar
git clone https://github.com/iHarpe/seguro-cafe-dashboard
cd seguro-cafe-dashboard

# 2. Entorno virtual
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # Linux/Mac

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
copy .env.example .env      # Windows
# cp .env.example .env      # Linux/Mac
```

## Configuración `.env`

```
API_BASE_URL=http://localhost:8000
API_KEY=dev-key-local
```

## Ejecución

```bash
# Terminal 1: API
cd ../seguro-cafe-api
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Dashboard
cd ../seguro-cafe-dashboard
python -m streamlit run app.py
# → http://localhost:8501
```

## Arquitectura

```
app.py                     # Entry point: CSS global + sidebar compartido
pages/
  1_Alerta_Actual.py       # Semáforo + KPIs + inputs anuales
  2_Monitoreo_Mensual.py   # Inputs mensuales + gráfico cosecha
  3_Historico.py           # Backtesting + tabla + descarga CSV
  4_Escenarios.py          # Sliders + tornado de sensibilidad
components/
  semaphore.py             # HTML del círculo semáforo
  metric_card.py           # Tarjetas KPI con borde de color
  charts.py                # Gráficos Plotly reutilizables
  disclaimer.py            # Banner de advertencia del modelo
utils/
  api_client.py            # Único punto de llamadas HTTP
  defaults.py              # Rangos de variables y constantes
  formatters.py            # Funciones de formato puras
  validators.py            # Validación de inputs antes de la API
assets/
  style.css                # Overrides CSS de Streamlit
```

## Modelos

| Uso | Algoritmo | MAE test |
|---|---|---|
| Pérdida anual (magnitud) | XGBoost | 9.63 pp |
| Detector + Trigger anual | HGB Set A | — |
| Alerta mensual | HGB lags cosecha | 11.08 pp (anualizado) |

Umbrales: Detector −2.8% · Trigger −14.0%
