from utils.defaults import VARIABLE_RANGES, TECHNICAL_VARIABLE_RANGES


def validate_annual_payload(data: dict) -> tuple[bool, str | None]:
    all_ranges = {**VARIABLE_RANGES, **TECHNICAL_VARIABLE_RANGES}
    for key, val in data.items():
        if key in ("departamento", "anio", "es_risaralda"):
            continue
        if key not in all_ranges:
            continue
        r = all_ranges[key]
        floor = r.get("floor")
        if floor is not None and val < floor:
            label = r.get("label", key)
            return False, f"{label}: el valor no puede ser negativo."
    return True, None
