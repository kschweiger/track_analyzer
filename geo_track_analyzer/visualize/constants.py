ENRICH_UNITS: dict[str, str] = {
    "elevation": "m",
    "speed": "km/h",
    "heartrate": "bpm",
    "cadence": "rpm",
    "power": "W",
}

# Based on plotly.express.colors.sequential.Plotly3
DEFAULT_COLOR_GRADIENT: tuple[str, str] = ("#0508b8", "#fec3fe")

COLOR_GRADIENTS: dict[str, tuple[str, str]] = {
    "heartrate": ("#636EFA", "#EF553B"),
}
