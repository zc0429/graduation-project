"""Original-font inventory and staged thesis rendering on a hosted Windows VM.

Only metadata and legally embedded PDF subsets leave Windows. Font binaries are
never copied to the repository or uploaded as standalone workflow artifacts.
"""
from pathlib import Path
from io import BytesIO
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import fitz
from fontTools.ttLib import TTFont, TTCollection

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = {
    'SimSun': {'SimSun', '宋体'},
    'SimHei': {'SimHei', '黑体'},
    'Times New Roman': {'Times New Roman'},
}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def names(font):
    return sorted({n.toUnicode() for n in font['name'].names if n.nameID in {1, 16}})


def inventory(output):
    if os.name != 'nt':
        raise RuntimeError('Windows system-font inventory must execute on Windows')
    directory = Path(os.environ['WINDIR']) / 'Fonts'
    files = ['simsun.ttc', 'simhei.ttf', 'times.ttf', 'timesbd.ttf', 'timesi.ttf', 'timesbi.ttf']
    records = []
    for filename in files:
        path = directory / filename
        if not path.is_file():
            records.append({'file': str(path), 'exists': False})
            continue
        collection = TTCollection(path, lazy=True) if path.suffix.lower() == '.ttc' else None
        fonts = collection.fonts if collection else [TTFont(path, lazy=True)]
        for index, font in enumerate(fonts):
            records.append({'file': str(path), 'exists': True, 'index': index,
                            'family_names': names(font), 'version': font['name'].getDebugName(5),
                            'style': font['name'].getDebugName(2), 'sha256': digest(path),
                            'embedding_fsType': font['OS/2'].fsType})
        if collection:
            collection.close()
        else:
            fonts[0].close()
    available = {family: any(accepted.intersection(r.get('family_names', [])) for r in records)
                 for family, accepted in FAMILIES.items()}
    report = {'platform': sys.platform, 'source': 'GitHub-hosted Windows system Fonts directory',
              'license_scope': 'Use on this hosted Windows VM; no standalone font redistribution or Linux copying',
              'families_available': available, 'files': records,
              'all_originals_available': all(available.values()),
              'font_binaries_uploaded': False, 'microsoft_word_verified': False}
    write_json(output, report)
    print(json.dumps({'families_available': available, 'report': str(output)}, ensure_ascii=False))
    return 0 if report['all_originals_available'] else 2


def verify_pdf(path, output):
    """Verify installed originals actually draw text and are embedded in the PDF."""
    doc = fitz.open(path)
    fonts = {}
    for page in doc:
        for font in page.get_fonts():
            fonts[font[0]] = font
    embedded = []
    for xref, font in fonts.items():
        base_name, extension, kind, data = doc.extract_font(xref)
        family_names = []
        error = None
        if data:
            try:
                with TTFont(BytesIO(data)) as actual:
                    family_names = names(actual)
            except Exception as exc:
                error = str(exc)
        embedded.append({'xref': xref, 'pdf_name': font[3], 'extension': extension,
                         'embedded': bool(data), 'embedded_bytes': len(data),
                         'embedded_family_names': family_names, 'metadata_error': error})
    spans = [(i + 1, s) for i, page in enumerate(doc)
             for b in page.get_text('dict')['blocks'] if b['type'] == 0
             for line in b['lines'] for s in line['spans'] if s['text'].strip()]
    def family(name):
        name = name.split('+')[-1]
        return next((f for f, key in [('SimSun', 'SimSun'), ('SimHei', 'SimHei'),
                                     ('Times New Roman', 'TimesNewRoman')] if key in name), None)
    usage = {f: sum(family(s['font']) == f for _, s in spans) for f in FAMILIES}
    unknown = [{'page': p, 'font': s['font'], 'text': s['text'][:60]}
               for p, s in spans if family(s['font']) is None]
    chinese_wrong = [{'page': p, 'font': s['font'], 'text': s['text'][:60]}
                     for p, s in spans if re.search(r'[\u3400-\u9fff]', s['text'])
                     and family(s['font']) not in {'SimSun', 'SimHei'}]
    footer_wrong = [{'page': p, 'font': s['font'], 'text': s['text'], 'size': s['size']}
                    for p, s in spans if re.fullmatch(r'[IVX]+|\d+', s['text'].strip())
                    and s['bbox'][1] > doc[p - 1].rect.height - 55
                    and (family(s['font']) != 'SimSun' or abs(s['size'] - 9) > .05)]
    metadata_ok = all(r['embedded'] and family(r['pdf_name']) in FAMILIES
                      and FAMILIES[family(r['pdf_name'])].intersection(r['embedded_family_names'])
                      for r in embedded)
    passed = bool(embedded) and metadata_ok and all(usage.values()) and not (unknown or chinese_wrong or footer_wrong)
    report = {'pdf': str(path.relative_to(ROOT)), 'pdf_pages': len(doc), 'fonts': embedded,
              'used_text_spans': usage, 'unrecognized_fonts': unknown,
              'chinese_font_errors': chinese_wrong, 'page_number_font_errors': footer_wrong,
              'original_pdf_text_fonts_verified': bool(passed),
              'standalone_font_binaries_exported': False,
              'raster_figure_fonts_verified': False, 'microsoft_word_verified': False}
    write_json(output, report)
    if not passed:
        raise RuntimeError('Actual PDF originals, embedded metadata, or page-number fonts failed verification')
    return report


def render(office):
    delivery = os.environ['THESIS_DELIVERY_ID']
    if not re.fullmatch(r'thesis-windows-fonts-\d+-\d+', delivery):
        raise ValueError('Use a new workflow-run-specific delivery ID')
    run = ROOT / 'docs/validation' / delivery
    out = ROOT / 'output/thesis' / delivery
    run.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.pop('THESIS_ALLOW_SUBSTITUTE_PREVIEW', None)
    tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '-z', 'HEAD'], cwd=ROOT).decode('utf-8').split('\0')
    baseline = {p: digest(ROOT / p) for p in tracked if p}
    write_json(run / 'baseline-files.json', baseline)
    write_json(run / 'environment.json', {
        'sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'runner_os': os.environ.get('RUNNER_OS'), 'image_os': os.environ.get('ImageOS'),
        'image_version': os.environ.get('ImageVersion'), 'python': sys.version,
        'libreoffice': subprocess.check_output([str(office), '--version'], text=True).strip(),
        'github_run_id': os.environ.get('GITHUB_RUN_ID'), 'github_run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
        'microsoft_word_verified': False,
    })
    def command(label, args):
        result = subprocess.run([str(x) for x in args], cwd=ROOT, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding='utf-8', errors='replace', timeout=300)
        (run / (label + '.log')).write_text(result.stdout, encoding='utf-8')
        if result.returncode:
            raise RuntimeError(f'{label} failed with exit code {result.returncode}; see its retained log')
    def script(label, filename):
        command(label, [sys.executable, ROOT / 'scripts/documents' / filename])
    pdf = out / '毕业论文.pdf'
    try:
        previous = None
        stable = False
        for iteration in range(1, 6):
            script(f'build-{iteration}', 'build_thesis_delivery.py')
            with tempfile.TemporaryDirectory(prefix='thesis-office-') as temp:
                temp_path = Path(temp)
                command(f'export-{iteration}', [office, '-env:UserInstallation=' + (temp_path / 'profile').as_uri(),
                        '--headless', '--convert-to', 'pdf:writer_pdf_Export', '--outdir', temp_path,
                        out / '毕业论文.docx'])
                candidate = temp_path / '毕业论文.pdf'
                if not candidate.is_file():
                    raise RuntimeError('LibreOffice returned without creating a PDF')
                shutil.copy2(candidate, pdf)
            script(f'page-map-{iteration}', 'update_delivery_page_map.py')
            current = json.loads((run / 'page-map.json').read_text(encoding='utf-8'))
            if current == previous:
                stable = True
                break
            previous = current
        if not stable:
            raise RuntimeError('TOC page map did not stabilize after five exports')
        verify_pdf(pdf, run / 'actual-pdf-fonts.json')
        script('document-validation', 'validate_thesis_delivery.py')
        script('font-layout-validation', 'audit_thesis_font_layout.py')
        script('render', 'render_thesis_audit.py')
        # Artifact includes every 120dpi page so the cloud task can inspect the
        # actual Windows result without requesting a local Word installation.
        shutil.copytree(ROOT / '.local' / delivery / 'pdf-pages', run / 'pdf-pages', dirs_exist_ok=True)
        assert digest(ROOT / 'docs/thesis/毕业论文.md') == baseline['docs/thesis/毕业论文.md']
        write_json(run / 'workflow-result.json', {
            'original_pdf_text_fonts_verified': True, 'automated_layout_checks_passed': True,
            'toc_stable': True, 'toc_destinations': len(current), 'exports': iteration,
            'manuscript_unchanged': True, 'manual_visual_review_completed': False,
            'raster_figure_fonts_verified': False, 'microsoft_word_verified': False,
            'docx_sha256': digest(out / '毕业论文.docx'), 'pdf_sha256': digest(pdf),
        })
    except Exception as exc:
        if pdf.exists():
            pdf.rename(out / '毕业论文-原字体待复核.pdf')
        write_json(run / 'workflow-result.json', {'original_font_layout_accepted': False,
                   'error': str(exc), 'manuscript_unchanged': digest(ROOT / 'docs/thesis/毕业论文.md') == baseline['docs/thesis/毕业论文.md'],
                   'microsoft_word_verified': False})
        raise


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    probe = sub.add_parser('inventory')
    probe.add_argument('--output', type=Path, required=True)
    exporter = sub.add_parser('render')
    exporter.add_argument('--office', type=Path, required=True)
    check = sub.add_parser('verify-pdf')
    check.add_argument('--pdf', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'inventory':
        return inventory(args.output)
    if args.command == 'render':
        render(args.office)
    else:
        verify_pdf(args.pdf, args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
