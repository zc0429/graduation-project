#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
output="output/thesis/${THESIS_DELIVERY_ID:-thesis-align-reference1-20261113}"
if command -v libreoffice >/dev/null 2>&1 || command -v soffice >/dev/null 2>&1; then
  profile_dir="$(mktemp -d)"
  trap 'rm -r "$profile_dir"' EXIT
  office_cmd="$(command -v libreoffice || command -v soffice)"
  FONTCONFIG_FILE="$repo_root/scripts/cloud/fonts.conf" "$office_cmd" \
    "-env:UserInstallation=file://$profile_dir" --headless --convert-to pdf \
    --outdir "$repo_root/$output" "$repo_root/$output/毕业论文.docx"
  exit 0
fi
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -e FONTCONFIG_FILE=/work/scripts/cloud/fonts.conf -v "$repo_root:/work" \
  graduation-thesis-tools:20261112 \
  libreoffice -env:UserInstallation=file:///tmp/lo-thesis --headless --convert-to pdf \
  --outdir "/work/$output" "/work/$output/毕业论文.docx"
