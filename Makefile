test-cov:
	pytest  --cov=track_analyzer tests --cov-report xml:cov.xml --cov-report term --disable-warnings