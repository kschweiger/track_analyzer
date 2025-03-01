from dash import Dash, Input, Output, callback, dcc, html

from geo_track_analyzer.track import Track
from geo_track_analyzer.visualize.map import plot_track_enriched_on_map
from geo_track_analyzer.visualize.progression import (
    ProgressionBase,
    ProgressionMetric,
    plot_progressions,
)
from geo_track_analyzer.visualize.summary import plot_track_zones


def get_app(track: Track) -> Dash:
    app = Dash()
    data = track.get_track_data()

    map_div = [
        html.Div(
            [
                dcc.Dropdown(
                    [
                        "heartrate",
                        "cadence",
                        "power",
                        "elevation",
                        "speed",
                    ],
                    "elevation",
                    id="dropdown_map_metric",
                ),
            ],
            # style={"width": "48%", "display": "inline-block"},
        ),
        dcc.Graph(id="enrichted_map"),
    ]

    prog_div_dropdown = [
        html.Div(
            [
                dcc.Dropdown(
                    [
                        "heartrate",
                        "cadence",
                        "power",
                        "elevation",
                        "speed",
                    ],
                    "heartrate",
                    id="dropdown_progression_metric",
                ),
            ],
            style={"width": "48%", "display": "inline-block"},
        ),
        html.Div(
            [
                dcc.Dropdown(
                    [
                        ProgressionBase.DISTANCE,
                        ProgressionBase.DURATION,
                    ],
                    ProgressionBase.DISTANCE,
                    id="dropdown_progression_base",
                ),
            ],
            style={"width": "48%", "display": "inline-block"},
        ),
    ]
    prog_div = [
        html.Div(prog_div_dropdown),
        dcc.Graph(id="metric_progression"),
    ]

    layout = [
        html.H1(children="Track visualization", style={"textAlign": "center"}),
        html.Div(map_div),
        html.Div(prog_div),
    ]
    # -----------------------
    zones = []
    if track.heartrate_zones is not None:
        zones.append("heartrate")
    if track.cadence_zones is not None:
        zones.append("cadence")
    if track.power_zones is not None:
        zones.append("power")

    if zones:
        zone_summary_div_dropdown = [
            html.Div(
                [
                    dcc.Dropdown(
                        zones,
                        zones[0],
                        id="dropdown_zone_summary_metric",
                    ),
                ],
                # style={"width": "48%", "display": "inline-block"},
            ),
            html.Div(
                [
                    dcc.Dropdown(
                        ["time", "distance", "speed"],
                        "time",
                        id="dropdown_zone_summary_agg",
                    ),
                ],
                # style={"width": "48%", "display": "inline-block"},
            ),
        ]
        layout.append(
            html.Div(
                [
                    html.Div(zone_summary_div_dropdown),
                    dcc.Graph(id="zone_summary_graph"),
                ]
            )
        )

    # -----------------------

    app.layout = layout

    @callback(
        Output("metric_progression", "figure"),
        Input("dropdown_progression_metric", "value"),
        Input("dropdown_progression_base", "value"),
    )
    def update_progression(metric, base):
        kwargs = dict()
        if metric is None:
            return

        figure = plot_progressions(data, metrics=[ProgressionMetric(metric)], base=base)
        return figure

    @callback(
        Output("enrichted_map", "figure"),
        Input("dropdown_map_metric", "value"),
    )
    def update_enrich_map(metric):
        kwargs = dict()
        if metric is None:
            return

        figure = plot_track_enriched_on_map(data, enrich_with_column=metric)
        return figure

    @callback(
        Output("zone_summary_graph", "figure"),
        Input("dropdown_zone_summary_metric", "value"),
        Input("dropdown_zone_summary_agg", "value"),
    )
    def zone_summary(metric, agg):
        kwargs = dict()
        if metric is None:
            return

        figure = plot_track_zones(data, metric, agg, **kwargs)
        return figure

    return app
