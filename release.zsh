#!/bin/sh

OLD_VERSION=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

echo "Bumping Version"

uv run python bump.py . $1 --init --package geo_track_analyzer
if [[ $? != 0 ]]; then
  echo "Bumping version failed. Exiting..."
  exit 1
fi

VERSION=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

echo $VERSION

git-changelog --bump ${VERSION}

git add pyproject.toml CHANGELOG.md uv.lock geo_track_analyzer/__init__.py
git commit -n -m "build: Bumping ${OLD_VERSION} -> ${VERSION} 🔖"

git tag ${VERSION}

echo "Pushing"
git push

echo "Pushing tag"
git push --tag
