#!/bin/bash
# Deploy repository to GitHub and enable GitHub Pages
# Usage: ./deploy.sh <user/repo>
set -e

REPO="$1"
if [ -z "$REPO" ]; then
  echo "Usage: $0 <user/repo>" >&2
  exit 1
fi

# Create repo if it does not exist and push
if ! gh repo view "$REPO" >/dev/null 2>&1; then
  gh repo create "$REPO" --public --source=. --remote=origin --push
else
  git push -u origin $(git rev-parse --abbrev-ref HEAD)
fi

# Enable GitHub Pages from docs folder
BRANCH=$(git rev-parse --abbrev-ref HEAD)
PAGES_JSON=$(printf '{"source":{"branch":"%s","path":"docs"}}' "$BRANCH")

gh api --method=POST "/repos/$REPO/pages" --input - <<<"$PAGES_JSON" >/dev/null

# Retrieve and display the Pages URL
URL=$(gh api "/repos/$REPO/pages" --jq '.html_url')
echo "GitHub Pages URL: $URL"
