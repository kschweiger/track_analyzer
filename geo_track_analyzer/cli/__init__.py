def generate_error_text(entry_point: str) -> str:
    return (
        f"The {entry_point} command line interface can not be run because of missing "
        "dependencies. Make sure that the package was installed with the **cli** "
        "extra. Use: pip install geo-track-analyzer[cli]"
    )


try:
    from ._update_elevation import main as update_elevation
except ImportError:

    def update_elevation() -> None:
        import sys

        print(generate_error_text("enhance-elevation"))
        sys.exit(1)


try:
    from ._extract_track import main as extract_track
except ImportError:

    def extract_track() -> None:
        import sys

        print(generate_error_text("extract-fit-track"))
        sys.exit(1)


__all__ = ["update_elevation", "extract_track"]
