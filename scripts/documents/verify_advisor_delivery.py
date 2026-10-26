"""Read-only checks, then write this run's evidence (no model/network calls)."""
from pathlib import Path
import json
import re
import subprocess
import xml.etree.ElementTree as ET

import pymupdf
from PIL import Image
import audit_thesis_figures as thesis_audit
import build_business_swimlanes as business

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'docs/thesis/business-flow'
OUT = ROOT/'docs/validation/advisor-20261026/document-check.json'


def git_bytes(ref, path):
    return subprocess.check_output(['git', 'show', f'{ref}:{path}'], cwd=ROOT)


def main():
    business.validate()
    combined = ET.parse(BASE/'业务流程图.drawio').getroot()
    assert len(combined) == 3
    for diagram, scene in zip(combined, business.SCENES):
        cells = diagram.findall('.//mxCell')
        nodes = {cell.attrib['id'] for cell in cells if cell.attrib.get('vertex') == '1'}
        for cell in cells:
            if cell.attrib.get('edge') == '1':
                assert cell.attrib['source'] in nodes and cell.attrib['target'] in nodes
        assert len(diagram.findall('.//mxCell[@edge="1"]')) == len(scene['edges'])
        assert len(ET.parse(BASE/(scene['slug']+'.drawio')).getroot()) == 1
        for index, node in enumerate(scene['nodes']):
            lane_width = 1020 / len(scene['lanes'])
            assert node['x'] >= 40+node['lane']*lane_width
            assert node['x']+node['w'] <= 40+(node['lane']+1)*lane_width
            for other in scene['nodes'][index+1:]:
                overlap = (max(node['x'], other['x']) < min(node['x']+node['w'], other['x']+other['w'])
                           and max(node['y'], other['y']) < min(node['y']+node['h'], other['y']+other['h']))
                assert not overlap, (node['id'], other['id'])
        with Image.open(BASE/(scene['slug']+'.png')) as image:
            assert image.width >= 2480 and image.height >= 3508
            assert abs(image.info['dpi'][0]-300) < 1
        ET.parse(BASE/(scene['slug']+'.svg'))
        with pymupdf.open(BASE/(scene['slug']+'.pdf')) as doc:
            assert len(doc) == 1 and abs(doc[0].rect.width-595.2756) < .1
    assert business.SCENES[0]['lanes'] == ['学生', '学习平台', 'AI 服务']

    # Retain the latest complete thesis reference set; do not re-review the passed opening report.
    path = 'docs/thesis/毕业论文.md'
    thesis = (ROOT/path).read_text(encoding='utf-8')
    frozen = git_bytes('29ae335', path).decode('utf-8')
    references = lambda text: re.findall(r'^\[(\d+)\] (.+)$', text, re.M)
    assert len(references(thesis)) == 20 and references(thesis) == references(frozen)
    assert not re.search(r'glm-\d|GLM-\d', thesis)
    for target in re.findall(r'!\[[^]]*\]\(([^)]+)\)', thesis):
        assert (ROOT/'docs/thesis'/target).is_file(), target
    facts = thesis_audit.baseline()
    checks = thesis_audit.verify(facts)

    preserved = ['server/src/main/resources/db/schema.sql',
                 'docs/validation/live-glm-validation.md', 'docs/validation/image-question-recognition.md',
                 'docs/validation/embedding-rebuild.md', 'docs/validation/real-ai-e2e.md']
    tracked = subprocess.check_output(['git', '-c', 'core.quotepath=false', 'ls-files'], cwd=ROOT, text=True).splitlines()
    preserved += [path for path in tracked if path.startswith(('docs/experiments/gate5/', 'docs/thesis/screenshots/real-glm/'))]
    for path in preserved:
        assert (ROOT/path).read_bytes() == git_bytes('aae3784', path), path
    changed = subprocess.check_output(['git', '-c', 'core.quotepath=false', 'diff', '--name-only'], cwd=ROOT, text=True).splitlines()
    assert not any('开题报告' in path or path.startswith('docs/materials/') for path in changed)

    proof = ROOT/'output/pdf/导师意见落实-图示校样-20261026.pdf'
    with pymupdf.open(proof) as doc:
        assert len(doc) == 5
        for page in doc:
            assert '\ufffd' not in page.get_text()
            for word in page.get_text('words'):
                assert 0 <= word[0] < word[2] <= page.rect.width
                assert 0 <= word[1] < word[3] <= page.rect.height
        min_font = min(span['size'] for page in list(doc)[:3]
                       for block in page.get_text('dict')['blocks'] if 'lines' in block
                       for line in block['lines'] for span in line['spans'])
        assert min_font >= 9, min_font
    checks.pop('business_tests', None)  # That field belongs to the older standalone figure audit.
    result = dict(date='2026-10-26', **checks, editable_xml_pages=3, per_diagram_exports=4,
                  a4_changed_figure_proof_pages=5, swimlane_min_font_pt_at_157_5mm=round(min_font, 2),
                  preserved_historical_files=len(preserved), opening_report='unchanged; not re-reviewed',
                  latest_reference_count=20, node_overlap=0,
                  drawio_application_open='not verified', full_thesis_docx_pdf='not regenerated',
                  real_glm_network='not executed: no key')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
