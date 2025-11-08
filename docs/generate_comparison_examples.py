from geo_track_analyzer.track import GPXFileTrack
from geo_track_analyzer.utils.base import init_logging

if __name__ == "__main__":
    init_logging(10)

    track = GPXFileTrack(
        "../tests/resources/Freiburger_Münster_nach_Schau_Ins_Land.gpx"
    )
    track_sub = GPXFileTrack("../tests/resources/Teilstueck_Schau_ins_land.gpx")

    overlap_info = track.find_overlap_with_segment(0, track_sub, 0)

    print(overlap_info)
