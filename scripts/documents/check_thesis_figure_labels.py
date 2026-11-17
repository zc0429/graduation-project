"""Check actual SVG text ink bounds against visible stroked geometry.

Run on Linux with Playwright and Chromium. Canvas glyph metrics avoid treating
unused font ascender/descender space as printed text. All strokes are sampled at
<=0.75 SVG units, transformed to root coordinates and intersected with each
label's ink bounding rectangle plus 1 unit of clearance. Opaque white rects
painted after a stroke and before the label are respected as backing plates.
This checks the 20 committed border-polish diagrams; screenshots are separate.
"""
from pathlib import Path
import argparse, json, os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/thesis/border-polish-20261114/figures'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = args.output or ROOT / 'docs/validation' / os.environ['THESIS_DELIVERY_ID'] / 'figure-label-check.json'
    script = Path(__file__).with_name('thesis_figure_label_geometry.js').read_text(encoding='utf-8')
    records = []
    controls = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page = browser.new_page()
        for item in json.loads((BASE / 'manifest.json').read_text(encoding='utf-8')).values():
            path = BASE / item['file'].replace('.png', '.svg')
            page.set_content(path.read_text(encoding='utf-8'))
            page.evaluate('document.fonts.ready')
            result = page.evaluate(script)
            assert result['text_count'] > 0 and result['shape_count'] > 0 and result['segment_count'] > 0, item['number']
            result.update(number=item['number'], svg=str(path.relative_to(ROOT)))
            records.append(result)
            if item['number'] == '5.3':
                count = page.locator('[data-role="label-white-backing"]').count()
                assert count == 2, 'Both sequence labels need opaque backing'
                page.locator('[data-role="label-white-backing"]').evaluate_all('(nodes)=>nodes.forEach(n=>n.remove())')
                probe = page.evaluate(script)
                labels = [c['text'] for c in probe['collisions']]
                assert '事务保存 question + 5 条 review_plan' in labels
                assert '归属检查；创建或重置解析状态 0' in labels
                controls.append({'figure': '5.3', 'probe': 'Temporarily remove backing in browser memory',
                                 'detected_labels': labels, 'passed': True})
        browser.close()
    assert len(records) == 20
    collisions = sum(len(r['collisions']) for r in records)
    report = {'figure_count': 20, 'label_count': sum(r['text_count'] for r in records),
              'clearance_svg_units': 1, 'maximum_stroke_sample_step': 0.75,
              'bounds': 'Union of actual painted glyph bounds, measured with the SVG-resolved fonts',
              'white_backing_occlusion_checked': True, 'negative_controls': controls, 'collision_count': collisions,
              'all_checks_passed': collisions == 0, 'figures': records}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'figures'}, ensure_ascii=False))
    assert collisions == 0, [(r['number'], [c['text'] for c in r['collisions']]) for r in records if r['collisions']]


if __name__ == '__main__':
    main()
