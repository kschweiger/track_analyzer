#!/bin/sh

set -eu

OLD_VERSION=$(uv run --no-sync python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

echo "Bumping Version"

if ! uv run --no-sync python bump.py . "$1" --init --package geo_track_analyzer; then
  echo "Bumping version failed. Exiting..." >&2
  exit 1
fi

VERSION=$(uv run --no-sync python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
if [ -z "$VERSION" ]; then
  echo "Could not determine the new version. Exiting..." >&2
  exit 1
fi

echo "$VERSION"

git-changelog --bump "$VERSION"

git add pyproject.toml CHANGELOG.md uv.lock geo_track_analyzer/__init__.py
git commit -n -m "build: Bumping ${OLD_VERSION} -> ${VERSION} 🔖"

git tag "$VERSION"

echo "Pushing"
git push

echo "Pushing tag"
git push --tag
