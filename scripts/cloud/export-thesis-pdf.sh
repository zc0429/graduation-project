#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
output="output/thesis/${THESIS_DELIVERY_ID:-thesis-align-reference1-20261113}"
run="docs/validation/${THESIS_DELIVERY_ID:-thesis-align-reference1-20261113}"
python_cmd="${THESIS_PYTHON:-$repo_root/.local/audit-venv/bin/python}"
preview="${THESIS_ALLOW_SUBSTITUTE_PREVIEW:-0}"
font_config="$repo_root/scripts/cloud/fonts-original.conf"
check_args=(--report "$repo_root/$run/font-preflight.json")
if [[ "$preview" == 1 ]]; then
  check_args+=(--preview)
  font_config="$repo_root/scripts/cloud/fonts.conf"
fi
# Inspect metadata, not just fc-match's success exit code (fallbacks also match).
FONTCONFIG_FILE="$repo_root/scripts/cloud/fonts-original.conf" \
  "$python_cmd" "$repo_root/scripts/documents/check_thesis_fonts.py" "${check_args[@]}"
# Stage the conversion so previews never overwrite an existing formal PDF, and
# reject actual renderer fallbacks before publishing a file under a formal name.
mkdir -p "$repo_root/.local" "$repo_root/$output"
export_dir="$(mktemp -d "$repo_root/.local/thesis-pdf.XXXXXX")"
profile_dir="$(mktemp -d)"
trap 'rm -r "$profile_dir" "$export_dir"' EXIT
if [[ "${THESIS_PDF_BACKEND:-auto}" != docker ]] && \
   { command -v libreoffice >/dev/null 2>&1 || command -v soffice >/dev/null 2>&1; }; then
  office_cmd="$(command -v libreoffice || command -v soffice)"
  FONTCONFIG_FILE="$font_config" "$office_cmd" \
    "-env:UserInstallation=file://$profile_dir" --headless --convert-to pdf \
    --outdir "$export_dir" "$repo_root/$output/毕业论文.docx"
else
  font_args=()
  if [[ -n "${THESIS_FONT_DIR:-}" ]]; then
    font_args=(-v "$THESIS_FONT_DIR:/usr/local/share/fonts/thesis-originals:ro")
  fi
  docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
    -e FONTCONFIG_FILE="/work/scripts/cloud/$(basename "$font_config")" \
    -v "$repo_root:/work" "${font_args[@]}" \
    graduation-thesis-tools:20261112 \
    libreoffice -env:UserInstallation=file:///tmp/lo-thesis --headless --convert-to pdf \
    --outdir "/work/${export_dir#"$repo_root/"}" "/work/$output/毕业论文.docx"
fi
render_check=(--pdf "$export_dir/毕业论文.pdf" --report "$repo_root/$run/pdf-font-render-check.json")
if [[ "$preview" == 1 ]]; then render_check+=(--preview); fi
FONTCONFIG_FILE="$repo_root/scripts/cloud/fonts-original.conf" \
  "$python_cmd" "$repo_root/scripts/documents/check_thesis_fonts.py" "${render_check[@]}"
if [[ "$preview" == 1 ]]; then
  mv -- "$export_dir/毕业论文.pdf" "$repo_root/$output/毕业论文-字体受限预览.pdf"
  printf '%s\n' 'FONT-LIMITED PREVIEW ONLY: inspect font-preflight.json and actual PDF fonts; Microsoft Word layout has not been verified.'
else
  mv -- "$export_dir/毕业论文.pdf" "$repo_root/$output/毕业论文.pdf"
fi
