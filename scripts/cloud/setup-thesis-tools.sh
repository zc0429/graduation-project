#!/usr/bin/env bash
# Reusable Debian/Ubuntu setup. Only open-source fonts; never copy Windows fonts.
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
packages=(fonts-noto-cjk fonts-liberation fonts-arphic-uming fontconfig libreoffice-writer poppler-utils python3-uno)
if [[ "$(id -u)" == 0 ]]; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y "${packages[@]}"
elif command -v sudo >/dev/null && sudo -n true 2>/dev/null; then
  if [[ -x /usr/local/bin/cloud-agent-packages ]]; then
    sudo -n /usr/local/bin/cloud-agent-packages update
    sudo -n /usr/local/bin/cloud-agent-packages install "${packages[@]}"
  else
    sudo -n apt-get update
    sudo -n apt-get install -y "${packages[@]}"
  fi
else
  # Rootless host fallback: package installation stays inside a disposable tools image.
  docker build -f "$repo_root/scripts/cloud/Dockerfile.thesis" -t graduation-thesis-tools:20261112 "$repo_root"
  tools_container="$(docker create graduation-thesis-tools:20261112)"
  trap 'docker rm "$tools_container" >/dev/null' EXIT
  font_dir="$HOME/.local/share/fonts/graduation-cloud"
  mkdir -p "$font_dir"
  docker cp "$tools_container:/usr/share/fonts/." "$font_dir/"
  fc-cache -f "$font_dir"
fi
mkdir -p "$repo_root/.local"
# AR PL UMing is TrueType-outline TTC, supported by the existing ReportLab renderer.
song_font="$(fc-match -f '%{file}' 'AR PL UMing CN')"
latin_font="$(fc-match -f '%{file}' 'Liberation Serif:style=Regular')"
[[ -f "$song_font" && -f "$latin_font" ]]
printf 'export THESIS_SONG_FONT=%q\nexport THESIS_LATIN_FONT=%q\n' "$song_font" "$latin_font" > "$repo_root/.local/thesis-fonts.env"
fc-match 'AR PL UMing CN'
fc-match 'Noto Serif CJK SC'
fc-match 'Liberation Serif'
printf '%s\n' 'Open-source substitutes configured; this does NOT establish original SimSun/Times New Roman availability.'
