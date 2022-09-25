from enum import Enum


class SegmentCharacter(str, Enum):
    FLAT = "flat"
    ASCENT = "ascent"
    DECENT = "descent"
