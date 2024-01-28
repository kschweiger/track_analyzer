# Track comparison

???+ warning "Warning"

    The features described in this section are **not considered final** and are subject to change. This may include breaking changes in minor releases!


## Finding sub-segments in tracks

A segments in a `Track` can be compared to another segment via the  [`Track.find_overlap_with_segment`][geo_track_analyzer.GPXFileTrack.find_overlap_with_segment] method.
The idea for this method is, that segment in the Track is the base against which the passed Segment is checked. This can be used to implemented
features similar to Segments in Strava. On a match, overlapping segment from the orignal track is returned. Additionally the overlap ratio and
the direction is included (``False`` means both segments are running in the same direction).

???+ note "Example"

    Image the following usecase: You have a longer track that includes serveral ascents and descents over a longer tour.
    You are interested how you performed on a particular ascent. Create a track with the ascent (only latitude/longitude coordinates
    required). Using the  [`Track.find_overlap_with_segment`][geo_track_analyzer.GPXFileTrack.find_overlap_with_segment] method on the `Track` of you tour and
    and track of the ascent you can extract segment corresponding to the ascent from the overall tour.

The maching algorithm can be fine-tuned with the arguements of the functions:

- `width`: The matching works by filling the points of the segments into 2D bins with a specific width in latitude and longitude direction. Overlap is determind by checking if points if both segments end up in the same bin.Smaller values of the  `width` parameter correspond to a stricter matching requirements.
- `overlap_threshold`: Minimum overlap ratio required to return a match.
- `max_queue_normalize`:  This parameter determines how many points needs to fall outside a bin before it can be counted as being visited an additional time in a track. Depends on the `width` setting. Larger values then to be saver but loops may be lost.
- `merge_subsegments`: Maximum distance between matching sub-segments allowed before the sub-segments are not merged anymore. Depends on the `width` setting. The larger the values the larger gaps in matching are allowed. Drawback of large values are the possibility to merge segments that connected via some other segment.

