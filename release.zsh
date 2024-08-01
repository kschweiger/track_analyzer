#!/bin/zsh

echo "Bumping Version"
bump-my-version bump $1
if [[ $? != 0 ]]
then
  echo "Bumping version failed. Exiting..."
  exit 1
fi
VERSION=$(bump-my-version show current_version)

git add pyproject.toml
git commit -n -m "build: Bumped version to ${VERSION} :bookmark:"

echo "Updating changelog"
git-changelog --bump ${VERSION}
if [[ $? != 0 ]]
then
  echo "Generating changelog failed. Exiting..."
  exit 1
fi
git add CHANGELOG.md
git commit -n -m "chore: Updated CHANGELOG.md :memo:"

git tag ${VERSION}

# echo "Pushing"
# git push
#
# echo "Pushing tag"
# git push --tag
