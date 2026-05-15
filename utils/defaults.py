VARIABLE_RANGES = {
    "precipitation_annual_sum": {
        "min": 0, "max": 5000, "default": 1450, "step": 10, "unit": "mm",
        "floor": 0.0,
        "label": "Precipitación anual total",
        "tooltip": "Suma de precipitaciones durante el año calendario",
    },
    "temp_aire_C_annual_mean": {
        "min": -10.0, "max": 40.0, "default": 17.5, "step": 0.1, "unit": "°C",
        "label": "Temperatura media anual",
        "tooltip": "Temperatura del aire promedio anual (ERA5)",
    },
    "def_annual_mean": {
        "min": 0, "max": 600, "default": 45, "step": 1, "unit": "mm",
        "floor": 0.0,
        "label": "Déficit hídrico anual medio",
        "tooltip": "Déficit hídrico acumulado promedio (TerraClimate)",
    },
    "GDD_cafe_annual_mean": {
        "min": 0.0, "max": 20.0, "default": 7.8, "step": 0.1, "unit": "°C-día",
        "floor": 0.0,
        "label": "Grados día acumulados café",
        "tooltip": "Grados día de crecimiento acumulados, referencia café",
    },
    "NDVI_anomalia_pct_annual_mean": {
        "min": -80.0, "max": 80.0, "default": 0.0, "step": 0.5, "unit": "%",
        "label": "Anomalía NDVI anual",
        "tooltip": "Desviación porcentual del NDVI respecto a la media histórica (MODIS)",
    },
    "precio_ico_usd_ton": {
        "min": 0, "max": 15000, "default": 3200, "step": 50, "unit": "USD/t",
        "floor": 0.0,
        "label": "Precio internacional (ICO)",
        "tooltip": "Precio del café colombiano en mercados internacionales (ICO)",
    },
    "precipitation_cosecha_sum": {
        "min": 0, "max": 5000, "default": 900, "step": 10, "unit": "mm",
        "floor": 0.0,
        "label": "Precipitación período cosecha",
        "tooltip": "Precipitación total en meses de cosecha (abr-jun, oct-dic)",
    },
    "temp_aire_C_cosecha_mean": {
        "min": -10.0, "max": 40.0, "default": 17.0, "step": 0.1, "unit": "°C",
        "label": "Temperatura media cosecha",
        "tooltip": "Temperatura promedio durante los meses de cosecha",
    },
    "def_cosecha_mean": {
        "min": 0, "max": 400, "default": 15, "step": 1, "unit": "mm",
        "floor": 0.0,
        "label": "Déficit hídrico cosecha",
        "tooltip": "Déficit hídrico promedio durante los meses de cosecha",
    },
    "NDVI_anomalia_pct_cosecha_mean": {
        "min": -80.0, "max": 80.0, "default": 0.0, "step": 0.5, "unit": "%",
        "label": "Anomalía NDVI cosecha",
        "tooltip": "Anomalía NDVI promedio durante la cosecha (MODIS)",
    },
}

TECHNICAL_VARIABLE_RANGES = {
    "Gpp_anomalia_pct_annual_mean": {
        "min": -100.0, "max": 100.0, "default": 0.0, "step": 0.5, "unit": "%",
        "label": "Anomalía GPP anual",
        "tooltip": "Anomalía de Productividad Primaria Bruta (MODIS MOD17)",
    },
    "Gpp_cosecha_mean": {
        "min": 0.0, "max": 20.0, "default": 1.8, "step": 0.05, "unit": "kgC/m²",
        "floor": 0.0,
        "label": "GPP cosecha",
        "tooltip": "Productividad Primaria Bruta promedio en cosecha (MODIS)",
    },
    "NDVI_cosecha_mean": {
        "min": 0.0, "max": 1.0, "default": 0.65, "step": 0.01, "unit": "",
        "floor": 0.0,
        "label": "NDVI cosecha (absoluto)",
        "tooltip": "Valor absoluto de NDVI en cosecha (MODIS MOD13)",
    },
    "aet_cosecha_mean": {
        "min": 0, "max": 600, "default": 70, "step": 1, "unit": "mm",
        "floor": 0.0,
        "label": "Evapotranspiración real cosecha",
        "tooltip": "AET promedio en meses de cosecha (TerraClimate)",
    },
    "pet_cosecha_mean": {
        "min": 0, "max": 600, "default": 90, "step": 1, "unit": "mm",
        "floor": 0.0,
        "label": "Evapotranspiración potencial cosecha",
        "tooltip": "PET promedio en meses de cosecha (TerraClimate)",
    },
    "LST_Day_1km_cosecha_mean": {
        "min": -10.0, "max": 55.0, "default": 20.5, "step": 0.1, "unit": "°C",
        "label": "Temperatura superficial diurna cosecha",
        "tooltip": "LST Day promedio en cosecha (MODIS MOD11, 1km)",
    },
    "LST_Night_1km_cosecha_mean": {
        "min": -20.0, "max": 40.0, "default": 13.0, "step": 0.1, "unit": "°C",
        "label": "Temperatura superficial nocturna cosecha",
        "tooltip": "LST Night promedio en cosecha (MODIS MOD11, 1km)",
    },
}

DEPARTMENTS = ["Risaralda", "Cundinamarca"]
DEFAULT_DEPARTMENT = "Risaralda"
DEFAULT_YEAR = 2024
DEFAULT_MODE = "Básico"

DETECTOR_THRESHOLD = -2.8
TRIGGER_THRESHOLD = -14.0

MODEL_MAE_ANNUAL = 9.63
MODEL_MAE_MONTHLY_ANNUALIZED = 11.08
MODEL_N_OBS = 36
MODEL_RECALL = 0.71
