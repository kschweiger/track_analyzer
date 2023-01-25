class APIResponseException(Exception):
    pass


class APIHealthCheckFailedException(Exception):
    pass


class APIDataNotAvailableException(Exception):
    pass


class TrackInitializationException(Exception):
    pass


class TrackTransformationException(Exception):
    pass
