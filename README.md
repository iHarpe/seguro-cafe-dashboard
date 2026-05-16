# seguro-cafe-dashboard

Dashboard Streamlit para análisis de riesgo del Seguro Agrícola Indexado Cafetero (Risaralda y Cundinamarca, Colombia). Consume la API [`seguro-cafe-api`](https://github.com/iHarpe/seguro-cafe-api).

## Inicio rápido

```bash
# Requiere seguro-cafe-api corriendo en localhost:8000
cp .env.example .env
pip install -r requirements.txt
streamlit run app.py
```

Dashboard: http://localhost:8501

## Variables de entorno

```
API_BASE_URL=http://localhost:8000
API_KEY=dev-key-local
```

## Páginas

| # | Archivo | Descripción |
|---|---|---|
| 1 | `1_Alerta_Actual.py` | Evaluación anual: formulario climático + semáforo de riesgo + KPIs |
| 2 | `2_Monitoreo_Mensual.py` | Monitoreo mensual de cosecha con detección temprana (M4) |
| 3 | `3_Historico.py` | Backtesting 2007-2024: frecuencia trigger, basis risk, descarga CSV |
| 4 | `4_Simulador.py` | Simulador actuarial: umbral, cobertura, loading, comparar configs |
| 5 | `5_Metodologia.py` | Documentación técnica: arquitectura, correlaciones, desempeño, ROC, datos, pipeline |
| 6 | `6_Score_Mensual.py` | Trayectoria histórica del score M4 + KPIs + tabla últimos 12 meses |

## Estructura

```
app.py                         # Entry point + home + nav cards
pages/                         # 6 páginas Streamlit
components/
  charts.py                    # Gráficos Plotly reutilizables
  metric_card.py               # Tarjetas KPI
  semaphore.py                 # Semáforo visual de riesgo
  sidebar.py                   # Navegación + config global
  disclaimer.py                # Disclaimer legal
utils/
  api_client.py                # Wrapper HTTP (9 endpoints)
  defaults.py                  # Umbrales, MAE, rangos de variables
  formatters.py                # Formato de porcentajes, niveles
  validators.py                # Validación de inputs pre-API
assets/style.css               # CSS global
```

## Modelos (vía API)

| Uso | Algoritmo | MAE test |
|---|---|---|
| Pérdida anual (M1) | XGBoost | 9.63 pp |
| Detector + Trigger (M2/M3) | HGB Set A | — |
| Alerta mensual (M4) | HGB lags cosecha | 11.08 pp |

Umbrales: Detector -2.8% / Trigger -14.0%

## Requisitos

- Python 3.11+
- [`seguro-cafe-api`](https://github.com/iHarpe/seguro-cafe-api) corriendo localmente
