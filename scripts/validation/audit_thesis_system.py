"""Recompute review inventories without rewriting historical audit evidence."""
import hashlib
import json
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'docs/validation/thesis-system-consistency-20261113'
sys.path.insert(0, str(ROOT / 'scripts/documents'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from audit_thesis_figures import baseline
    from audit_current_thesis import normalize
    from build_requirements_review import balance
    from validate_thesis_references import validate
    facts = baseline()
    md = (ROOT / 'docs/thesis/毕业论文.md').read_text()
    sql = (ROOT / 'server/src/main/resources/db/schema.sql').read_text()
    tables = []
    for match in re.finditer(r'CREATE TABLE IF NOT EXISTS `(\w+)` \((.*?)\) ENGINE[^;]+;', sql, re.S):
        name, body = match.groups()
        columns = []
        for line in body.splitlines():
            field = re.match(r'\s*`?(\w+)`?\s+(BIGINT|VARCHAR\(\d+\)|CHAR\(\d+\)|TINYINT|INT|TEXT|DATETIME|DATE)\s+(.+)', line)
            if field:
                key, typ, rest = field.groups()
                columns.append({'name': key, 'type': typ, 'definition': normalize(rest.rstrip(',')),
                                'line': sql[:match.start()].count('\n') + body[:body.index(line)].count('\n') + 1})
        entity_path = next(p for p in (ROOT / 'server/src/main/java/com/example/wrongbook/entity').glob('*.java')
                           if f'@TableName("{name}")' in p.read_text())
        source = entity_path.read_text()
        entity_fields = re.findall(r'(?:private|public)\s+(?:Long|Integer|String|LocalDateTime|LocalDate|Boolean)\s+(\w+)\s*;', source)
        entity_fields = [re.sub(r'(?<!^)([A-Z])', r'_\1', x).lower() for x in entity_fields if x != 'practiced']
        assert entity_fields == [c['name'] for c in columns], (name, entity_fields, columns)
        mapper_path = ROOT / 'server/src/main/java/com/example/wrongbook/mapper' / (entity_path.stem + 'Mapper.java')
        assert 'BaseMapper<' + entity_path.stem + '>' in mapper_path.read_text()
        section = re.search(r'\*\*表 6\.\d+[^\n]*（' + name + r'）\*\*(.*?)(?=\n\*\*表|\n###|\n\*\*（11）)', md, re.S)
        assert section
        assert re.findall(r'^\| ([a-z_]+) \|', section[1], re.M) == entity_fields
        for c in columns:
            assert '| ' + c['name'] + ' | ' + c['type'] + ' |' in section[1]
        indexes = re.findall(r'(PRIMARY KEY|UNIQUE KEY \w+|KEY \w+)\s*\(([^)]+)\)', body)
        tables.append({'table': name, 'columns': columns, 'column_count': len(columns), 'indexes': indexes,
                       'entity': str(entity_path.relative_to(ROOT)), 'mapper': str(mapper_path.relative_to(ROOT)),
                       'foreign_keys': [], 'checks': []})
    endpoints = facts['endpoints']
    paper_endpoints = set(re.findall(r'\| (GET|POST|PUT|DELETE) \| (/api/[^ |]+) \|', md))
    assert paper_endpoints == {(e['method'], e['path']) for e in endpoints}
    for endpoint in endpoints:
        source = (ROOT / endpoint['source']).read_text().splitlines()
        block = '\n'.join(source[endpoint['line'] - 1:])
        signature = re.search(r'public\s+(.+?)\s*\{', block, re.S)[1]
        endpoint['signature'] = re.sub(r'\s+', ' ', signature)
        endpoint['dto'] = re.findall(r'\b(\w+Request)\b', signature)
        endpoint['validation'] = {name: (ROOT / 'server/src/main/java/com/example/wrongbook/dto' / (name + '.java')).read_text()
                                  for name in endpoint['dto']}
    excerpts_file = RUN / 'code-excerpts.json'
    if not excerpts_file.exists():
        excerpts_file.write_bytes((ROOT / 'docs/validation/thesis-align-reference1-20261113/code-excerpts.json').read_bytes())
    excerpts = json.loads(excerpts_file.read_text())
    for rec in excerpts:
        path = ROOT / rec['path']
        actual = textwrap.dedent('\n'.join(path.read_text().splitlines()[rec['start_line'] - 1:rec['end_line']]))
        assert actual == rec['text'] and actual in md, rec['number']
        assert digest(path) == rec['source_sha256'], rec['path']
    figures = []
    for match in re.finditer(r'!\[([^]]*)\]\(([^)]+)\)\s*\*\*图 (\d+\.\d+)\s*([^*]+)\*\*', md):
        alt, target, number, title = match.groups()
        path = ROOT / 'docs/thesis' / target
        assert path.is_file()
        figures.append({'number': number, 'caption': title.strip(), 'path': str(path.relative_to(ROOT)), 'sha256': digest(path)})
    assert len(figures) == 28
    logical_tables = re.findall(r'^\*\*表 (\d+\.\d+)\s*([^*]+)\*\*', md, re.M)
    assert len(logical_tables) == 26
    for kind, nums in [('figure', [f['number'] for f in figures]), ('table', [n for n, _ in logical_tables])]:
        for ch in set(n.split('.')[0] for n in nums):
            assert [int(n.split('.')[1]) for n in nums if n.startswith(ch + '.')] == list(range(1, 1 + sum(n.startswith(ch + '.') for n in nums))), kind
    dfd = balance()
    assert all(v['balanced'] for v in dfd.values())
    result = {'baseline': json.loads((RUN / 'baseline.json').read_text()), 'tables': tables, 'table_count': len(tables),
              'column_count': sum(t['column_count'] for t in tables), 'index_count_including_primary': sum(len(t['indexes']) for t in tables),
              'endpoints': endpoints, 'endpoint_count': len(endpoints), 'public': sum(e['roles'] == ['public'] for e in endpoints),
              'views': facts['views'], 'figures': figures, 'logical_tables': logical_tables,
              'code_excerpts': len(excerpts), 'excerpt_raw_lines': sum(r['end_line'] - r['start_line'] + 1 for r in excerpts),
              'dfd_balance': dfd, 'references': validate(), 'gate5_recalculated': facts['gate5_manual']}
    assert (result['table_count'], result['column_count'], result['index_count_including_primary'], result['endpoint_count']) == (11, 88, 20, 39)
    (RUN / 'inventory.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['table_count', 'column_count', 'index_count_including_primary', 'endpoint_count', 'public', 'code_excerpts', 'excerpt_raw_lines']}, ensure_ascii=False))
    # The actual PNGs used in the manuscript, not historical alternate exports.
    from PIL import Image, ImageOps, ImageDraw
    proofs = RUN / 'figure-proofs'
    proofs.mkdir(exist_ok=True)
    for start in range(0, len(figures), 4):
        sheet = Image.new('RGB', (1800, 1800), 'white')
        draw = ImageDraw.Draw(sheet)
        for j, fig in enumerate(figures[start:start + 4]):
            image = Image.open(ROOT / fig['path']).convert('RGB')
            image.thumbnail((880, 840))
            x, y = (j % 2) * 900, (j // 2) * 900
            sheet.paste(image, (x + (900 - image.width) // 2, y + 30 + (840 - image.height) // 2))
            draw.text((x + 15, y + 10), fig['number'] + ' - ' + Path(fig['path']).name, fill='black')
        sheet.save(proofs / f'{start // 4 + 1:02}.png')


if __name__ == '__main__':
    main()
