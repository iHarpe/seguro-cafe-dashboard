import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_KEY  = os.environ.get("API_KEY", "dev-key-local")
HEADERS  = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
TIMEOUT  = 10


def _get(path: str) -> dict:
    try:
        r = requests.get(f"{API_BASE}{path}", headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return {"ok": True, "data": r.json()}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": f"API no disponible en {API_BASE}. ¿Está corriendo?"}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Tiempo de espera agotado (10 s). Intenta de nuevo."}
    except requests.exceptions.HTTPError as e:
        return {"ok": False, "error": f"Error {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _post(path: str, payload: dict) -> dict:
    try:
        r = requests.post(
            f"{API_BASE}{path}", json=payload, headers=HEADERS, timeout=TIMEOUT
        )
        r.raise_for_status()
        return {"ok": True, "data": r.json()}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": f"API no disponible en {API_BASE}. ¿Está corriendo?"}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Tiempo de espera agotado (10 s). Intenta de nuevo."}
    except requests.exceptions.HTTPError as e:
        return {"ok": False, "error": f"Error {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def health_check() -> bool:
    result = _get("/health")
    return result["ok"]


def predict_annual(payload: dict) -> dict:
    return _post("/predict/annual", payload)


def predict_monthly(records: list) -> dict:
    return _post("/predict/monthly", {"records": records})


def get_history(departamento: str) -> dict:
    return _get(f"/data/history/{departamento}")


def get_calibration() -> dict:
    return _get("/calibrate/trigger")


def get_backtest(departamento: str | None = None,
                 umbral_pct: float | None = None) -> dict:
    params = []
    if departamento:
        params.append(f"departamento={departamento}")
    if umbral_pct is not None:
        params.append(f"umbral_pct={umbral_pct}")
    qs = f"?{'&'.join(params)}" if params else ""
    return _get(f"/data/backtest{qs}")


def get_monthly_history(departamento: str) -> dict:
    return _get(f"/data/monthly-history/{departamento}")


def get_oof() -> dict:
    return _get("/data/oof")


def get_correlations() -> dict:
    return _get("/data/correlations")


def get_health_full() -> dict:
    return _get("/health")
