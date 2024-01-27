test-cov:
	pytest  --cov=geo_track_analyzer tests --cov-report xml:cov.xml --cov-report term --disable-warnings

poetry-install-full:
	poetry install --all-extras --with=dev,test,doc

poetry-install-mim:
	poetry install

poetry-install-extras:
	poetry install --all-extras

doc-preprocess:
	python docs/dump_github_releases.py
	python docs/generate_visualization_examples.py