ENRICH_UNITS: dict[str, str] = {
    "elevation": "m",
    "speed": "km/h",
    "heartrate": "bpm",
    "cadence": "rpm",
    "power": "W",
}

DEFAULT_COLOR_GRADIENT: tuple[str, str] = ("#00CC96", "#FECB52")
COLOR_GRADIENTS: dict[str, tuple[str, str]] = {
    "heartrate": ("#636EFA", "#EF553B"),
}
