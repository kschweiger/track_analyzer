import click

from track_analyzer.track import FITFileTrack


@click.command()
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "--name", help="Optinally set the Name property in the output file", default=None
)
@click.option(
    "--email", help="Optinally set the eMail property in the output file", default=None
)
def main(filename: str, name: None | str, email: None | str):
    """
    Extract the track information for FILENAME file in fit format and
    save to regular gpx file
    """
    click.echo("Extracting track from %s" % filename)
    track = FITFileTrack(filename)

    out_file_name = filename.replace(".fit", "") + ".gpx"
    click.echo("Writing file %s" % out_file_name)
    with open(out_file_name, "w") as f:
        f.write(track.get_xml(name=name, email=email))


if __name__ == "__main__":
    main()