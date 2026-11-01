"""Rebuild only the five figures changed for the 2026-10-26 advisor update.

Run build_business_swimlanes.py first. Original screenshot figures are untouched.
Font paths can be set through THESIS_SONG_FONT and THESIS_LATIN_FONT.
"""
from pathlib import Path
import argparse
import os
import json

ROOT = Path(__file__).resolve().parents[2]
if os.name != 'nt':
    os.environ.setdefault('THESIS_SONG_FONT', str(Path.home()/'.local/share/fonts/NotoSerifSC.ttf'))
    os.environ.setdefault('THESIS_LATIN_FONT', '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf')

import build_thesis_figures as figures
import pymupdf
from reportlab.pdfgen import canvas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ids', nargs='+', default=['3-2', '3-3', '3-4', '4-1', '5-2'])
    parser.add_argument('--proof-name', default='导师意见落实-图示校样-20261026.pdf')
    args = parser.parse_args()
    ids = args.ids
    manifest_path = figures.BASE/'manifest.json'
    manifest = {item['id']: item for item in json.loads(manifest_path.read_text(encoding='utf-8'))}
    proof_path = ROOT/'output/pdf'/args.proof_name
    proof = pymupdf.open()
    for name in ids:
        scene = json.loads((figures.BASE/'sources'/f'{name}.json').read_text(encoding='utf-8'))
        if scene.get('business_flow_slug'):
            from build_business_swimlanes import SCENES
            business = next(item for item in SCENES if item['slug'] == scene['business_flow_slug'])
            scene['height'] = business['height'] * figures.WIDTH / business['width']
            (figures.BASE/'sources'/f'{name}.json').write_text(
                json.dumps(scene, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        for op in scene['ops']:
            if op['kind'] == 'text':
                width = figures.text_width(op['text'], op.get('size', 9))
                left = op['x'] - width / 2
                assert left >= 0 and left + width <= figures.WIDTH, (name, op)
        (figures.BASE/'svg'/f'{name}.svg').write_text(figures.svg(scene), encoding='utf-8')
        target = figures.OUT/f'{name}.pdf'
        target.parent.mkdir(parents=True, exist_ok=True)
        output = canvas.Canvas(str(target), pagesize=(figures.WIDTH, scene['height']))
        figures.render(scene, output)
        output.save()
        with pymupdf.open(target) as doc:
            doc[0].get_pixmap(dpi=300).save(figures.BASE/'png'/f'{name}.png')
            page = proof.new_page(width=595.2756, height=841.8898)
            page.show_pdf_page(pymupdf.Rect(74, 45, 74+figures.WIDTH, 45+scene['height']), doc, 0)
        manifest[name] = dict(id=name, caption=scene['caption'], evidence=scene['evidence'],
                              height_pt=scene['height'], width_mm=157.5, png_dpi=300, screenshots=[])
    proof.save(proof_path)
    manifest_path.write_text(json.dumps(sorted(manifest.values(), key=lambda item: [int(n) for n in item['id'].split('-')]),
                                        ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Updated:', ', '.join(ids), '; A4 proof pages:', len(proof))


if __name__ == '__main__':
    main()
