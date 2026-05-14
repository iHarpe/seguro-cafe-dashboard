SVG_ICONS = {
    "normal":  '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "caution": '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "alert":   '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
    "unknown": '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
}

LABELS = {
    "normal":  "Normal",
    "caution": "Precaución",
    "alert":   "Alerta",
    "unknown": "Sin datos",
}

SUBTITLES = {
    "normal":  "Sin anomalías climáticas significativas",
    "caution": "Anomalía detectada — monitoreo recomendado",
    "alert":   "Riesgo elevado — trigger activado",
    "unknown": "Ingresa datos y presiona Calcular",
}


def render_semaphore(level: str = "unknown") -> str:
    level = level.lower()
    if level not in SVG_ICONS:
        level = "unknown"

    icon    = SVG_ICONS[level]
    label   = LABELS[level]
    subtitle = SUBTITLES[level]

    return f"""
<div class="semaphore-container animate-fade-in">
  <div class="semaphore-circle semaphore-{level}" role="status" aria-label="Nivel de riesgo: {label}">
    <div class="semaphore-icon">{icon}</div>
    <span class="semaphore-label">{label}</span>
  </div>
  <p class="semaphore-subtitle">{subtitle}</p>
</div>
"""
