class APIResponseError(Exception):
    pass


class APIHealthCheckFailedError(Exception):
    pass


class APIDataNotAvailableError(Exception):
    pass


class TrackInitializationError(Exception):
    pass


class TrackTransformationError(Exception):
    pass


class InvalidBoundsError(Exception):
    pass
