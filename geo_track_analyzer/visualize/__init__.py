try:
    import plotly  # noqa: F401
except ModuleNotFoundError:

    def raise_err_func(*args, **kwargs) -> None:
        raise RuntimeError("Install the visualization extra to use this functionality")

    plot_metrics = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
    plot_segment_box_summary = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
    plot_segment_summary = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
    plot_segment_zones = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
    plot_segments_on_map = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
    plot_track_2d = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
    plot_track_3d = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
    plot_track_enriched_on_map = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
    plot_track_line_on_map = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
    plot_track_with_slope = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
    plot_track_zones = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
    plot_tracks_on_map = lambda *args, **kwargs: raise_err_func(*args, **kwargs)
else:
    from .interactive import plot_track_3d
    from .map import (
        plot_segments_on_map,
        plot_track_enriched_on_map,
        plot_track_line_on_map,
        plot_tracks_on_map,
    )
    from .metrics import plot_metrics
    from .profiles import plot_track_2d, plot_track_with_slope
    from .summary import (
        plot_segment_box_summary,
        plot_segment_summary,
        plot_segment_zones,
        plot_track_zones,
    )

__all__ = [
    "plot_metrics",
    "plot_segment_box_summary",
    "plot_segment_summary",
    "plot_segment_zones",
    "plot_segments_on_map",
    "plot_track_2d",
    "plot_track_3d",
    "plot_track_enriched_on_map",
    "plot_track_line_on_map",
    "plot_track_with_slope",
    "plot_track_zones",
    "plot_tracks_on_map",
]
