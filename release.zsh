#!/bin/zsh

echo "Bumping Version"
VERSION=$(poetry version --short $1)
if [[ $? != 0 ]]
then
  echo "poetry version failed. Exiting..."
  exit 1
fi
git add pyproject.toml
git commit -n -m "build: Bumped version to ${VERSION} :bookmark:"

echo "Updating changelog"
git-changelog
if [[ $? != 0 ]]
then
  echo "Generating changelog failed. Exiting..."
  exit 1
fi
git add CHANGELOG.md
git commit -n -m "doc: Updated CHANGELOG.md :memo:"

git tag ${VERSION}

echo "Pushing"
git push

echo "Pushing tag"
git push --tag