import click
from requests.exceptions import MissingSchema
from rich.console import Console

from geo_track_analyzer.enhancer import EnhancerType, get_enhancer
from geo_track_analyzer.exceptions import (
    APIDataNotAvailableError,
    APIHealthCheckFailedError,
)
from geo_track_analyzer.track import GPXFileTrack


def convert_kwargs(raw_kwargs: tuple[str, ...]) -> dict[str, str | bool]:
    converted_kwargs: dict[str, str | bool] = {}
    for kwarg in raw_kwargs:
        if "=" not in kwarg:
            raise click.BadParameter(
                "All values in RAW_ENHANCER_INIT_ARGS need to contain =. "
                f"{kwarg} does not fulfill that requirement"
            )
        split_kwarg = kwarg.split("=")
        if len(split_kwarg) != 2:
            raise click.BadParameter(
                "All values in RAW_ENHANCER_INIT_ARGS need to be a value pair. "
                f"{kwarg} does not fulfill that requirement"
            )
        key, value = split_kwarg
        if value.lower() == "false":
            converted_kwargs[key] = False
        elif value.lower() == "true":
            converted_kwargs[key] = True
        else:
            converted_kwargs[key] = value

    return converted_kwargs


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "--enhancer",
    type=click.Choice(list(EnhancerType), case_sensitive=True),
    help="Specify the enhancer type to be used to make the requests.",
    required=True,
)
@click.option(
    "--url",
    help="URL of the API. Should be the full url including port if necessary. "
    "Example: http://localhost:8080/",
    required=True,
)
@click.option(
    "--postfix",
    default="enhanced_elevation",
    help="String that will be appended to the output file.",
    show_default=True,
)
@click.option(
    "-v", "--verbose", count=True, help="Set the verbosity level of the script."
)
@click.argument("raw_enhancer_init_args", nargs=-1, type=click.UNPROCESSED)
def main(
    filename: str,
    enhancer: EnhancerType,
    url: str,
    postfix: str,
    raw_enhancer_init_args: tuple[str, ...],
    verbose: int,
) -> None:
    """
    Enhance elevation data in a gpx file FILENAME using the Enahncer APIs
    provided in this package. Additional keyword-arguments for the Enhancers
    can be passed as key-value-pairs with = sizes. E.g. dataset=eudem25m for
    the OpenTopoElevationEnhancer.
    """
    console = Console()
    if not filename.endswith(".gpx"):
        raise click.UsageError("Only .gpx files are supported")
    init_kwargs = convert_kwargs(raw_enhancer_init_args)
    console.print(f"Enhancing [red]elevation[/red] for {filename}")

    try:
        track = GPXFileTrack(filename)
    except:  # noqa: E722
        console.print(":x: Track could not be loaded")
        exit(1)
    else:
        console.print(":white_check_mark: Track sucessfully loaded")

    enhancer_type = get_enhancer(enhancer)
    console.print(":white_check_mark: Enhancer selected")

    try:
        this_enhancer = enhancer_type(
            url=url,
            **init_kwargs,
        )
    except TypeError as e:
        console.print(":x: Enhancer could not be initialized. Check the passed kwargs")
        if verbose <= 1:
            console.print(f":exclamation_mark: {e}")
        exit(1)
    except MissingSchema as e:
        console.print(":x: Could not reach API")
        if verbose <= 1:
            console.print(f":exclamation_mark: {e}")
        exit(1)
    except APIHealthCheckFailedError as e:
        console.print(":x: Enhancer API Health-Check failed")
        if verbose <= 1:
            console.print(f":exclamation_mark: {e}")
        exit(1)
    except APIDataNotAvailableError as e:
        console.print(":x: Invalud dataset set. Check the passed kwargs")
        if verbose <= 1:
            console.print(f":exclamation_mark: {e}")
        exit(1)
    else:
        console.print(":white_check_mark: Enhancer initialized")

    with console.status("Running elevation enhancement"):
        this_enhancer.enhance_track(track.track, inplace=True)  # noqa: PD002
    console.print(":white_check_mark: Enhancement done")

    new_file_name = filename.replace(".gpx", f"_{postfix}.gpx")
    with open(new_file_name, "w") as f:
        f.write(track.get_xml())

    console.print(f":white_check_mark: File saved to {new_file_name}")


if __name__ == "__main__":
    main()
