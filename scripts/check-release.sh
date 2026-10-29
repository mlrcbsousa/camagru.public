#!/bin/sh
set -eu

root=${1:-.}
changelog="$root/CHANGELOG.md"
version_file="$root/VERSION"
pkg="$root/package.json"

if [ ! -f "$changelog" ]; then
  echo "CHANGELOG.md is missing" >&2
  exit 1
fi

if grep -q '^## \[Unreleased\]' "$changelog"; then
  echo "CHANGELOG.md still has [Unreleased]" >&2
  exit 1
fi

version=""
if [ -f "$version_file" ]; then
  version=$(tr -d '[:space:]' < "$version_file")
fi

if [ -f "$pkg" ]; then
  pkg_version=$(node -e '
    const fs = require("fs");
    const pkg = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
    if (!pkg.version) process.exit(2);
    process.stdout.write(pkg.version);
  ' "$pkg") || {
    echo "package.json has no version" >&2
    exit 1
  }
  if [ -n "$version" ] && [ "$version" != "$pkg_version" ]; then
    echo "VERSION is $version and package.json is $pkg_version" >&2
    exit 1
  fi
  if [ -z "$version" ]; then
    version=$pkg_version
  fi
fi

if [ -z "$version" ]; then
  echo "VERSION is missing" >&2
  exit 1
fi

case $version in
  *.*.*) ;;
  *)
    echo "VERSION is not major.minor.patch" >&2
    exit 1
    ;;
esac

heading=$(grep -E '^## \[[0-9]+\.[0-9]+\.[0-9]+\]' "$changelog" | head -n 1 || true)
case $heading in
  "## [$version]"*) ;;
  *)
    echo "newest changelog heading is not $version" >&2
    exit 1
    ;;
esac

if [ -n "${RELEASE_BASE:-}" ]; then
  added=$(git diff "$RELEASE_BASE"...HEAD -- "$changelog" | grep -c '^+## \[' || true)
  foreign=$(
    git log --merges --pretty=%P "$RELEASE_BASE"..HEAD 2>/dev/null |
    while read -r _ second _; do
      [ -n "${second:-}" ] || continue
      if ! git merge-base --is-ancestor "$second" "$RELEASE_BASE" 2>/dev/null; then
        echo yes
        break
      fi
    done
  )
  if [ "$added" -eq 1 ]; then
    :
  elif [ "$added" -gt 1 ] && [ "$foreign" = yes ]; then
    :
  else
    echo "this pull request adds $added changelog headings" >&2
    exit 1
  fi
fi

releaselog="$root/RELEASELOG.md"
if [ -f "$releaselog" ]; then
  if grep -q '^## \[Unreleased\]' "$releaselog"; then
    echo "RELEASELOG.md still has [Unreleased]" >&2
    exit 1
  fi
  rel=$(grep -E '^## \[[0-9]+\.[0-9]+\.[0-9]+\]' "$releaselog" | head -n 1 || true)
  if [ -n "$rel" ]; then
    rel_version=$(printf '%s\n' "$rel" | sed -E 's/^## \[([0-9]+\.[0-9]+\.[0-9]+)\].*/\1/')
    newest=$(printf '%s\n%s\n' "$version" "$rel_version" | sort -t. -k1,1n -k2,2n -k3,3n | tail -n 1)
    if [ "$newest" != "$version" ]; then
      echo "RELEASELOG.md $rel_version is newer than VERSION $version" >&2
      exit 1
    fi
  fi
fi

echo "$version"
