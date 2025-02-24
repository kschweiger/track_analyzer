test-cov:
	pytest  --cov=geo_track_analyzer tests --cov-report xml:cov.xml  --cov-report json --cov-report term --disable-warnings


