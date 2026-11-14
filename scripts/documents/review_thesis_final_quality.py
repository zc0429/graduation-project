"""Recheck the final thesis against PR #8 without rerunning the system audit.

Run after exporting the selected delivery. Writes only its new validation folder.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import textwrap
from PIL import Image
import fitz

ROOT = Path(__file__).resolve().parents[2]
DELIVERY = os.environ.get('THESIS_DELIVERY_ID', 'thesis-final-quality-20261113')
RUN = ROOT / 'docs/validation' / DELIVERY
BASE = '21da287744a252e7ccae0aadbe5832336c8b3b27'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def norm(text):
    return re.sub(r'\s+', '', text)

def main():
    sys.path.insert(0, str(ROOT / 'scripts/documents'))
    from audit_reference1_alignment import inventory
    from validate_thesis_references import validate
    md = (ROOT / 'docs/thesis/毕业论文.md').read_text()
    before = subprocess.check_output(['git', 'show', BASE + ':docs/thesis/毕业论文.md'], cwd=ROOT, text=True)
    baseline = json.loads((RUN / 'baseline-files.json').read_text())
    allowed = {'AGENTS.md', 'docs/notes/进度记录.md', 'docs/notes/HANDOFF.md', 'docs/thesis/毕业论文.md'}
    protected = {p: h for p, h in baseline.items() if p not in allowed}
    changed = [p for p, h in protected.items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
    assert not changed, ('Protected input changed', changed)
    edits = json.loads((RUN / '修改前后对照.json').read_text())
    replay = before
    for edit in edits:
        assert replay.count(edit['before']) == 1, edit['id']
        replay = replay.replace(edit['before'], edit['after'])
    assert replay == md, 'Unrecorded manuscript change'
    # Keep the real excerpts, figures and bibliography intact.
    excerpts = json.loads((RUN / 'code-excerpts.json').read_text())
    pattern = r'^代码(7\.\d+)\s+([^\n]+)\n\n```[^\n]*\n(.*?)\n```'
    blocks = re.findall(pattern, md, re.M | re.S)
    assert len(blocks) == len(excerpts) == 31
    assert re.findall(pattern, before, re.M | re.S) == blocks
    code_rows = []
    for (number, title, code), record in zip(blocks, excerpts):
        source = ROOT / record['path']
        raw = '\n'.join(source.read_text().splitlines()[record['start_line']-1:record['end_line']])
        assert number == record['number'] and code == record['text']
        assert textwrap.dedent(raw).strip() == code.strip(), number
        assert sha(source) == record['source_sha256'], number
        code_rows.append(f"|7.{len(code_rows)+1}|{record['title']}|{record['path']}:{record['start_line']}—{record['end_line']}|逐行及SHA-256一致；正文保留|")
    figure_pattern = r'!\[([^]]*)\]\(([^)]+)\)\s*\n\n\*\*图\s+(\d+\.\d+)\s+([^*]+)\*\*'
    figures = re.findall(figure_pattern, md)
    assert len(figures) == 28 and figures == re.findall(figure_pattern, before)
    tables = re.findall(r'^\*\*表\s+(\d+\.\d+)\s+([^*]+)\*\*', md, re.M)
    assert len(tables) == 26
    assert tables == re.findall(r'^\*\*表\s+(\d+\.\d+)\s+([^*]+)\*\*', before, re.M)
    # Check prose references, including numeric ranges and consecutive lists.
    prose = re.sub(r'```.*?```', '', md, flags=re.S)
    prose = re.sub(r'^\*\*[图表].*$', '', prose, flags=re.M)
    prose = re.sub(r'^!\[.*$', '', prose, flags=re.M)
    mentions = {'图': set(), '表': set()}
    for kind in mentions:
        mentions[kind].update(re.findall(kind+r'\s*(\d+\.\d+)', prose))
        for start, end in re.findall(kind+r'\s*(\d+\.\d+)\s*(?:至|—|到)\s*(?:'+kind+r'\s*)?(\d+\.\d+)', prose):
            chapter, first = map(int, start.split('.')); last_chapter, last = map(int, end.split('.'))
            assert chapter == last_chapter
            mentions[kind].update(f'{chapter}.{i}' for i in range(first, last+1))
    # A grouped reference such as 图6.1、图6.2和图6.3 is picked up individually.
    for kind, numbers in [('图', [f[2] for f in figures]), ('表', [t[0] for t in tables])]:
        for chapter in sorted(set(n.split('.')[0] for n in numbers)):
            actual = [int(n.split('.')[1]) for n in numbers if n.startswith(chapter+'.')]
            assert actual == list(range(1, len(actual)+1)), (kind, chapter)
        assert set(numbers) <= mentions[kind], ('Missing prose reference', kind, set(numbers)-mentions[kind])
        assert mentions[kind] <= set(numbers), ('Undefined figure/table', kind, mentions[kind]-set(numbers))
    pdf = fitz.open(ROOT/'output/thesis'/DELIVERY/'毕业论文.pdf')
    page_text = [norm(p.get_text()) for p in pdf]
    def caption_pages(kind, number, title):
        needle = norm(kind+number+title)
        pages = [i+1 for i, t in enumerate(page_text) if needle in t]
        assert pages, (kind, number, title)
        return '、'.join(map(str, pages))
    fig_rows = []
    for _, target, number, title in figures:
        path = ROOT/'docs/thesis'/target
        assert sha(path) == baseline[str(path.relative_to(ROOT))]
        with Image.open(path) as im:
            size = f'{im.width}×{im.height}'
        pages = caption_pages('图', number, title)
        fig_rows.append(f'|{number}|{title}|{pages}|{size}；原图SHA-256不变|编号、正文引用、图题及来源保留；见逐页视觉记录|')
    table_rows=[]
    for number, title in tables:
        pages=caption_pages('表', number, title)
        table_rows.append(f'|{number}|{title}|{pages}|编号连续、正文有引用、PDF表题存在；单元格完整性见document-check.json|')
    refs = validate()
    records = json.loads((ROOT/'docs/references/reference-audit-20261113.json').read_text())['records']
    ref_rows = [f"|{r['number']}|{r['entry']}|首次引用顺序、题录源文件与BibTeX一致；沿用已核实元数据|" for r in records]
    lines = ['# 图、表、代码与参考文献逐项复核', '',
             '本轮检查编号、引用、来源、文本及导出完整性；系统事实沿用PR #8已核实结果，不将本脚本称为新的系统回归。页码均为PDF物理页。图像内容与来源的人工复核见逐页视觉记录。', '',
             '## 28幅图', '', '|图号|名称|PDF页|源图像素与保护|检查结论|', '|---|---|---|---|---|', *fig_rows, '',
             '## 26张正文逻辑表', '', '|表号|名称|PDF页|检查结论|', '|---|---|---|---|', *table_rows, '',
             '26为正文逻辑表数量；DOCX包含续表和附录索引，共30个物理表对象，不能混用两种计数。', '',
             '## 31段核心代码', '', '|代码|内容|实际文件与行号|检查结论|', '|---|---|---|---|', *code_rows, '',
             '31段共'+str(sum(r['end_line']-r['start_line']+1 for r in excerpts))+'行，源码、片段及标题与PR #8一致；不新增伪代码，正文保留核心逻辑，附录只提供来源索引。', '',
             '## 27篇参考文献', '', '|编号|题录|检查结论|', '|---|---|---|', *ref_rows, '',
             '中文22篇在前、外文5篇在后；首次引用1—27连续，2024—2026年23篇，按2025—2027已发表口径15篇。中文标点、外文作者国籍及超过3名作者的“等”沿用2027学校要求；正文上标与书签跳转由DOCX校验。原始元数据网络核验属于PR #7既有证据，本轮未重新逐篇联网检索。']
    (RUN/'图表代码文献逐项复核.md').write_text('\n'.join(lines)+'\n')
    chapters=[]
    for n in range(1,10):
        counts=[]
        for content in (before, md):
            part=re.search(r'^## '+str(n)+r' .*?(?=^## |\Z)', content, re.M|re.S)[0]
            part=re.sub(r'```.*?```', '', part, flags=re.S)
            part='\n'.join(l for l in part.splitlines() if not l.startswith(('|','!','**图','**表','代码7.','资料来源：')))
            counts.append(len(re.findall(r'[\u4e00-\u9fff]', part)))
        chapters.append({'chapter':n, 'before_prose_han':counts[0], 'after_prose_han':counts[1],
                         'figures':sum(f[2].startswith(f'{n}.') for f in figures), 'tables':sum(t[0].startswith(f'{n}.') for t in tables)})
    assert chapters[0]['after_prose_han']>=800
    assert 2000<=chapters[1]['after_prose_han']<=3000
    assert sum(x['after_prose_han'] for x in chapters)>12000
    assert sum(x['after_prose_han'] for x in chapters[2:8])>8000
    result={'baseline':BASE,'after':inventory(ROOT/'output/thesis'/DELIVERY/'毕业论文.pdf'),
            'recorded_edits':len(edits),'protected_files_checked':len(protected),'protected_changes':changed,
            'figures':len(figures),'logical_tables':len(tables),'actual_code_excerpts':len(excerpts),
            'references':refs,'chapter_prose_counts':chapters,
            'count_method':'Chinese characters outside code, tables, figure/table/code captions and source notes; headings retained; not Word word count',
            'new_system_tests_executed':False,'original_fonts_verified':False}
    (RUN/'quality-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='after'},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
