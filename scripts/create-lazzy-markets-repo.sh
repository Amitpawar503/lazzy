#!/usr/bin/env bash
#
# Carve the Lazzy Markets platform (docs/ + backend/ + frontend/ + config) out of
# this repo into a brand-new, standalone Git repository and push it to GitHub.
#
# The game POC (poc_game/, src/, pom.xml, mvnw, .mvn/) is intentionally excluded —
# the new repo contains ONLY the stock-market platform.
#
# Usage:
#   scripts/create-lazzy-markets-repo.sh [target-dir] [git-remote-url]
#
# Examples:
#   # 1) Let the GitHub CLI create the repo for you (recommended):
#   scripts/create-lazzy-markets-repo.sh ../lazzy-markets
#   #    → then, inside ../lazzy-markets:  gh repo create lazzy-markets --private --source=. --push
#
#   # 2) You already created an empty repo on GitHub — pass its URL to push directly:
#   scripts/create-lazzy-markets-repo.sh ../lazzy-markets git@github.com:Amitpawar503/lazzy-markets.git
#
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-../lazzy-markets}"
REMOTE_URL="${2:-}"

echo "Source repo : $SRC"
echo "Target dir  : $TARGET"

mkdir -p "$TARGET"
TARGET="$(cd "$TARGET" && pwd)"

# Platform files only (respects .gitignore; excludes the Java game POC).
echo "Copying platform files…"
git -C "$SRC" ls-files \
  | grep -Ev '^(poc_game/|src/|mvnw|mvnw\.cmd|pom\.xml|\.mvn/)' \
  | while read -r f; do
      mkdir -p "$TARGET/$(dirname "$f")"
      cp "$SRC/$f" "$TARGET/$f"
    done

cd "$TARGET"
git init -q
git add -A
git commit -q -m "Initial commit: Lazzy Markets — Indian market intelligence platform

360 & sector heatmaps, FII/DII activity, and multi-algorithm signal consensus.
FastAPI backend + React/Vite/TypeScript frontend. Extracted from the lazzy repo."

echo
echo "✅ Standalone repo created at: $TARGET"
echo

if [ -n "$REMOTE_URL" ]; then
  git branch -M main
  git remote add origin "$REMOTE_URL"
  git push -u origin main
  echo "✅ Pushed to $REMOTE_URL"
else
  cat <<'NEXT'
Next step — create the GitHub repo and push. Either:

  # A) GitHub CLI (creates + pushes in one go):
  gh repo create lazzy-markets --private --source=. --push

  # B) Manually: create an empty repo on github.com, then:
  git branch -M main
  git remote add origin git@github.com:<you>/lazzy-markets.git
  git push -u origin main
NEXT
fi
