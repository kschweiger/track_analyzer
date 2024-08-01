test-cov:
	pytest  --cov=geo_track_analyzer tests --cov-report xml:cov.xml  --cov-report json --cov-report term --disable-warnings

uv-compile:
	uv pip compile pyproject.toml -o requirements/prod.txt --all-extras --no-header
	uv pip compile requirements/dev.in -o requirements/dev.txt --no-header
	uv pip compile requirements/test.in -o requirements/test.txt --no-header
	uv pip compile requirements/doc.in -o requirements/doc.txt --no-header

uv-sync:
	uv pip sync requirements/prod.txt requirements/dev.txt requirements/test.txt requirements/doc.txt
	uv pip install -e . --no-deps
