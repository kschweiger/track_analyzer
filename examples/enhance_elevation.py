from geo_track_analyzer.enhancer import OpenTopoElevationEnhancer
from geo_track_analyzer.exceptions import (
    APIDataNotAvailableError,
    APIHealthCheckFailedError,
)
from geo_track_analyzer.track import PyTrack


def main() -> None:
    try:
        enhancer = OpenTopoElevationEnhancer(
            # This is the public api with some limitations.
            # See https://www.opentopodata.org/#public-api
            url="https://api.opentopodata.org/",
            # This is a elevation dataset by the European Environment Agency
            # with a 25 metre resolution. Depending on the region you have to
            # choose a different one
            dataset="eudem25m",
        )
    except APIHealthCheckFailedError as e:
        # This exception is raised if the heath checks on the api fails
        # (can not connect or non 200 from /health or /dataset enpoint)
        print(e)
        return
    except APIDataNotAvailableError as e:
        # Raised if the dataset passed on initialization is not valid
        print(e)
        return

    coords = [
        # Berlin
        (52.517037, 13.38886),
        # Paris
        (48.85889, 2.320041),
        # Naples
        (40.835885, 14.248768),
        # Andorra
        (42.540717, 1.573203),
    ]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Retrieve elevations for individual coordinates
    elevations = enhancer.get_elevation_data(input_coordinates=coords)

    print(elevations)
    # Elevations for Berlin, Paris, Naples, Andorra
    # >> [44.69026565551758, 44.59218978881836, 29.364185333251953, 1654.7138671875]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Enricht a Track with elevation data
    track = PyTrack(
        # Points follow the cable-car line from Eibsee to the Zugspitze
        points=[
            (47.45639, 10.99216),
            (47.45343, 10.99154),
            (47.45070, 10.99101),
            (47.44791, 10.99047),
            (47.44558, 10.99010),
            (47.44285, 10.98950),
            (47.44053, 10.98912),
            (47.43449, 10.98796),
            (47.42938, 10.98697),
            (47.42124, 10.98549),
        ],
        # If eletaions are set here they would be overwritten by the
        # enhancer.enhance_track call.
        elevations=None,
        times=None,
    )
    print(f" Pre enhance :: Track has elevation data: {track.track.has_elevations()}")
    # >>>  Pre enhance :: Track has elevation data: False
    enhancer.enhance_track(track=track.track, inplace=True)
    print(f"Post enhance :: Track has elevation data: {track.track.has_elevations()}")
    # >>> Post enhance :: Track has elevation data: True
    print(track.get_track_data()[["latitude", "longitude", "elevation"]])
    # >>>    latitude  longitude    elevation
    # >>> 0  47.45343   10.99154  1032.080322
    # >>> 1  47.45070   10.99101  1116.176025
    # >>> 2  47.44791   10.99047  1223.318848
    # >>> 3  47.44558   10.99010  1310.345581
    # >>> 4  47.44285   10.98950  1402.699097
    # >>> 5  47.44053   10.98912  1476.707886
    # >>> 6  47.43449   10.98796  1654.359985
    # >>> 7  47.42938   10.98697  1998.382324
    # >>> 8  47.42124   10.98549  2934.315918


if __name__ == "__main__":
    main()
