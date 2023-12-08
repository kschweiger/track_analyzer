import importlib.resources

import data as examples

from geo_track_analyzer.track import GPXFileTrack
from geo_track_analyzer.visualize.map import plot_tracks_on_map


def main() -> None:
    example_files = importlib.resources.files(examples)

    # The main track. In this case a track starting at the Franklin D. Roosevelt
    # metro station, goes up the Av. des Champs-Elysees, arount the Arc de Triomphe,
    # down Av. d'lena with a detour around some smaller streets and ends at Alma-Marceau
    # metro station.
    track = GPXFileTrack((example_files / "track_paris.gpx"))

    # First we want to match a segment going up the Av. des Champs-Elysees
    track_av_champs_elysees = GPXFileTrack((example_files / "av_camps_elysees.gpx"))
    # Second we want to match a segment going down Av. d'lena but machting
    # should fail because of the detour.
    track_av_d_lena = GPXFileTrack((example_files / "av_dlena.gpx"))

    # Display the track and the segments we want to match on a map
    plot_tracks_on_map(
        [
            track.get_track_data(),
            track_av_champs_elysees.get_track_data(),
            track_av_d_lena.get_track_data(),
        ],
        ["Main track", "Segment 1", "Segment 2"],
    ).show()

    result_champs_elysees = track.find_overlap_with_segment(
        n_segment=0,
        match_track=track_av_champs_elysees,
        match_track_segment=0,
        overlap_threshold=0.5,
    )
    seg_match_champs_elysees, _, _ = result_champs_elysees[0]

    print(result_champs_elysees)
    # >>> [(<geo_track_analyzer.track.SegmentTrack object at 0x13f4e1c10>, 1.0, False)]
    # We get one matching subsegment from the main track with an overlap of 100 % and
    # the direction in the main track and match track is the same
    result_dlena = track.find_overlap_with_segment(
        n_segment=0,
        match_track=track_av_d_lena,
        match_track_segment=0,
        overlap_threshold=0.5,
    )
    seg_match_dlena, _, _ = result_dlena[0]

    print(result_dlena)
    # >>> [(<geo_track_analyzer.track.SegmentTrack object at 0x12a298fd0>, 0.7222222222222222, False)]
    # We get one matching subsegment from the main track with an overlap of 72% and
    # the direction in the main track and match track is the same. The overlap is lower
    # due to the detour in the main track. This should not be conisdered match

    plot_tracks_on_map(
        [
            seg_match_champs_elysees.get_track_data(),
            seg_match_dlena.get_track_data(),
        ],
        [
            "Extracted Segment Champs-Elysees",
            "Extracted Segment d'lena",
        ],
    ).show()


if __name__ == "__main__":
    main()
