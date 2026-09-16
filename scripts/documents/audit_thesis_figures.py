"""Recompute the repository baseline and verify manuscript figure/table links.
Read-only against application code, schema, original screenshots and experiment data.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from xml.etree import ElementTree as ET
import pymupdf

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/thesis/figures'


def baseline():
    schema_path=ROOT/'server/src/main/resources/db/schema.sql'
    sql=schema_path.read_text(encoding='utf-8')
    tables=[]
    for match in re.finditer(r'CREATE TABLE IF NOT EXISTS `(\w+)` \((.*?)\) ENGINE[^;]+;',sql,re.S):
        name,body=match.group(1,2);fields=[]
        unique=re.findall(r'UNIQUE KEY \w+ \((\w+)\)',body)
        for line in body.splitlines():
            m=re.match(r"\s*`?(\w+)`?\s+(BIGINT|VARCHAR\(\d+\)|TINYINT|INT|TEXT|DATETIME|DATE)\s+(.*?)\s+COMMENT '([^']*)'",line)
            if m:
                field,typ,constraint,comment=m.groups()
                if field=='id':constraint='PRIMARY KEY '+constraint
                if field in unique:constraint+=' UNIQUE'
                fields.append(dict(name=field,type=typ,constraint=constraint,comment=comment))
        tables.append(dict(name=name,fields=fields,line=sql[:match.start()].count('\n')+1,
                           indexes=re.findall(r'(?:UNIQUE )?KEY \w+ \([^)]+\)',body)))
    endpoints=[]
    for p in sorted((ROOT/'server/src/main/java/com/example/wrongbook/controller').glob('*.java')):
        s=p.read_text(encoding='utf-8');head,body=s.split('public class',1)
        base=re.search(r'@RequestMapping\("([^"]+)"\)',head).group(1)
        role=re.search(r'@RequireRole\(([^)]+)\)',head)
        default=re.findall(r'"(\w+)"',role.group(1)) if role else ['authenticated']
        for m in re.finditer(r'@(Get|Post|Put|Delete)Mapping(?:\("([^"]*)"\))?\s*(.*?)\bpublic\s+',body,re.S):
            method,path,annotations=m.groups();roles=re.search(r'@RequireRole\(([^)]+)\)',annotations)
            roles=re.findall(r'"(\w+)"',roles.group(1)) if roles else default
            path=base+(path or '')
            if path in ['/api/health','/api/auth/register','/api/auth/login']:roles=['public']
            endpoints.append(dict(method=method.upper(),path=path,roles=roles,source=p.relative_to(ROOT).as_posix(),
                                  line=s[:s.index(body)+m.start()].count('\n')+1))
    views=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'web/src/views').rglob('*.vue'))
    gate=ROOT/'docs/experiments/gate5'
    scores=list(csv.DictReader((gate/'manual/error-cause-review.csv').open(encoding='utf-8-sig',newline='')))
    ab=list(csv.DictReader((gate/'manual/rag-ab-review.csv').open(encoding='utf-8-sig',newline='')))
    key=json.loads((gate/'results/rag-ab-key.json').read_text(encoding='utf-8'))
    numbers=[int(r['manualScore']) for r in scores]
    preference=Counter(key[r['caseId']][r['preferred']] for r in ab)
    files=[schema_path,ROOT/'web/src/router/index.ts']+list((ROOT/'server/src/main/java/com/example/wrongbook/controller').glob('*.java'))
    return dict(audit_date='2026-09-16',head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                scope='当前工作区，不等同于 HEAD；未连接运行中数据库，未重跑历史业务测试。',tables=tables,endpoints=endpoints,views=views,
                gate5_manual=dict(count=len(scores),total=sum(numbers),mean=sum(numbers)/len(numbers),distribution=dict(Counter(numbers)),ab_count=len(ab),preferences=dict(preference)),
                source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files})


def verify(b):
    assert len(b['tables'])==10
    assert len(b['endpoints'])==36
    assert sum(e['roles']==['public'] for e in b['endpoints'])==3
    assert len(b['views'])==15
    assert b['gate5_manual']['total']==46 and b['gate5_manual']['preferences']=={'RAG_OFF':4,'RAG_ON':2}
    thesis=(ROOT/'docs/thesis/毕业论文.md').read_text(encoding='utf-8')
    for t in b['tables']:
        match=re.search(r'\*\*表 5\.\d+[^\n]*（'+t['name']+r'）\*\*\n(.*?)(?=\n\*\*表 |\n### )',thesis,re.S)
        assert match, t['name']
        names=re.findall(r'^\| ([a-z_]+) \|',match.group(1),re.M)
        assert names==[f['name'] for f in t['fields']],(t['name'],names)
        for f in t['fields']:
            assert f'| {f["name"]} | {f["type"]} | {f["constraint"]} |' in match.group(1)
    listed=set(re.findall(r'\| (GET|POST|PUT|DELETE) \| (/api/[^ |]+) \|',thesis))
    assert listed=={(e['method'],e['path']) for e in b['endpoints']}
    role_labels={('public',):'公开',('authenticated',):'登录用户',('student',):'学生',('admin',):'管理员',('student','teacher'):'学生、教师'}
    for endpoint in b['endpoints']:
        row=re.search(r'\| '+endpoint['method']+r' \| '+re.escape(endpoint['path'])+r' \| ([^\n]+)',thesis).group(1)
        assert '权限：'+role_labels[tuple(endpoint['roles'])] in row,endpoint
    assert '此处占位：图' not in thesis
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    for item in manifest:
        id=item['id'];caption=item['caption'];number=id.replace('-','.')
        assert f'**{caption}**' in thesis,caption
        assert len(re.findall(r'图\s*'+re.escape(number)+r'(?!\d)',thesis))>=2,caption
        assert f'figures/png/{id}.png' in thesis
        for ext in ['png','svg']:
            assert (OUT/ext/f'{id}.{ext}').is_file()
        assert (ROOT/'output/pdf/thesis-figures'/f'{id}.pdf').is_file()
        root=ET.parse(OUT/'svg'/f'{id}.svg').getroot()
        assert not list(root.iter('{http://www.w3.org/2000/svg}foreignObject'))
        for ev in item['evidence']:assert (ROOT/ev).exists(),ev
        for ss in item['screenshots']:
            assert hashlib.sha256((ROOT/ss['path']).read_bytes()).hexdigest()==ss['sha256']
    figures=re.findall(r'^\*\*图 (\d+)\.(\d+)',thesis,re.M)
    tables=re.findall(r'^\*\*表 (\d+)\.(\d+)',thesis,re.M)
    for kind,items in [('figure',figures),('table',tables)]:
        for chapter in {c for c,n in items}:
            nums=[int(n) for c,n in items if c==chapter]
            assert nums==list(range(1,len(nums)+1)),(kind,chapter,nums)
    for target in re.findall(r'!\[[^]]*\]\(([^)]+)\)',thesis):assert (ROOT/'docs/thesis'/target).exists()
    return dict(tables=len(tables),figures=len(figures),physical_tables=10,endpoints=36,public=3,authenticated=33,normal_views=14,fallback_views=1,
                schema_fields=sum(len(t['fields']) for t in b['tables']),original_screenshot_hashes='unchanged',figure_numbering='continuous',svg='well-formed; no foreignObject',business_tests='not rerun')


if __name__=='__main__':
    b=baseline();OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'fact-baseline.json').write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    r=verify(b)
    with pymupdf.open(ROOT/'output/pdf/thesis-figures/图表A4校样.pdf') as proof:
        bad=[]
        for page in proof:
            assert abs(page.rect.width-595.2756)<0.1 and abs(page.rect.height-841.8898)<0.1
            bad.extend((page.number+1,w) for w in page.get_text('words')
                       if w[0]<77.5 or w[2]>525.3 or w[1]<35 or w[3]>773)
        assert not bad,bad
        r.update(a4_proof_pages=len(proof),out_of_bounds_text=len(bad),visio='actual SVG import and VSDX validation TODO')
    (OUT/'verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False))
