#!/bin/zsh

echo "Bumping Version"
bump-my-version bump $1 --commit
if [[ $? != 0 ]]
then
  echo "Bumping version failed. Exiting..."
  exit 1
fi
VERSION=$(bump-my-version show current_version)

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

echo "Pushing"
git push

echo "Pushing tag"
git push --tag
