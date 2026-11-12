"""Verify review artifacts and capture browser/PDF renders, without touching prior evidence."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,xml.etree.ElementTree as ET
import fitz
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
PACK=ROOT/'docs/thesis/requirements-20261112'
OUT=ROOT/'docs/validation/requirements-20261112'
S=827/1200
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def crosses(a,b,r):
    # Segment/rectangle interior intersection; a 1px inset avoids boundary-only contacts.
    x,y,w,h=r;lo,hi=0,1;dx=b[0]-a[0];dy=b[1]-a[1]
    for p,q in [(-dx,a[0]-x-1),(dx,x+w-1-a[0]),(-dy,a[1]-y-1),(dy,y+h-1-a[1])]:
        if abs(p)<1e-9:
            if q<0:return False
        elif p<0:lo=max(lo,q/p)
        else:hi=min(hi,q/p)
    return lo<hi and hi>0 and lo<1

def main(chromium):
    baseline=json.loads((OUT/'baseline.json').read_text());allowed={'docs/thesis/毕业论文.md','docs/notes/HANDOFF.md','docs/notes/进度记录.md'}
    changed=[f for f,h in baseline['files'].items() if not (ROOT/f).exists() or sha(ROOT/f)!=h]
    assert set(changed)<=allowed,changed
    main=(ROOT/'docs/thesis/毕业论文.md').read_text()
    old=subprocess.check_output(['git','show',baseline['dev']+':docs/thesis/毕业论文.md'],cwd=ROOT).decode()
    assert main[main.index('## 参考文献'):]==old[old.index('## 参考文献'):], 'References/acknowledgments changed'
    chapter=main[main.index('## 3 系统需求分析'):main.index('## 4 系统概要设计')]
    standalone=(PACK/'第3章-需求分析审阅稿.md').read_text().split('## 3 系统需求分析',1)[1]
    assert chapter.split('## 3 系统需求分析',1)[1].replace('requirements-20261112/','')==standalone
    links=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',main)
    assert all((ROOT/'docs/thesis'/p).exists() for p in links),[p for p in links if not (ROOT/'docs/thesis'/p).exists()]
    assert len(re.findall(r'\*\*图 3\.\d+\s',chapter))==9
    assert '†' not in chapter
    copy=[]
    for p in (PACK/'business-flow').iterdir():
        if p.suffix not in {'.drawio','.svg','.png','.pdf'}:continue
        src='docs/thesis/business-flow/review-20261111/'+p.name
        content=subprocess.check_output(['git','show',baseline['review_pr1']+':'+src],cwd=ROOT)
        assert p.read_bytes()==content,p
        copy.append({'source':src,'copy':str(p.relative_to(ROOT)),'sha256':sha(p)})
    assert len(copy)==14
    (OUT/'business-flow-provenance.json').write_text(json.dumps({'commit':baseline['review_pr1'],'files':copy},ensure_ascii=False,indent=2)+'\n')
    scenes=json.loads((PACK/'figures/diagrams.json').read_text());report=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=chromium,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':827,'height':1169},device_scale_factor=1)
        for s in scenes:
            key=s['key'];pdf=fitz.open(PACK/'figures'/f'{key}.pdf')
            assert len(pdf)==1 and abs(pdf[0].rect.width-595.27559)<.1 and abs(pdf[0].rect.height-841.88976)<.1
            pdf[0].get_pixmap(dpi=105).save(OUT/f'{key}-pdf.png')
            cells=ET.parse(PACK/'figures'/f'{key}.drawio').findall('.//mxCell')
            edges=[c for c in cells if c.get('edge')=='1'];ids={c.get('id') for c in cells}
            assert len(edges)==len(s['edges']) and all(c.get('source') in ids and c.get('target') in ids for c in edges)
            ns={n['id']:n for n in s['nodes']}
            for n in s['nodes']:
                if n['kind']=='process':
                    assert any(e['source']==n['id'] for e in s['edges']) and any(e['target']==n['id'] for e in s['edges'])
            if s['kind']=='dfd':
                assert all(ns[e['source']]['kind']=='process' or ns[e['target']]['kind']=='process' for e in s['edges'])
            page.set_content('<style>body{margin:0}</style>'+re.sub(r'<\?xml[^>]*>', '', (PACK/'figures'/f'{key}.svg').read_text()));page.evaluate('document.fonts.ready');page.screenshot(path=str(OUT/f'{key}-svg.png'))
            textboxes=page.evaluate('''() => [...document.querySelectorAll('g[data-cell-id]')].filter(g=>g.dataset.cellId!=='0'&&g.dataset.cellId!=='1').map(g=>{const ts=[...g.querySelectorAll('text')];if(!ts.length)return null;const rs=ts.map(t=>t.getBoundingClientRect());const x=Math.min(...rs.map(r=>r.x)),y=Math.min(...rs.map(r=>r.y));return {id:g.dataset.cellId,text:ts.map(t=>t.textContent).join(''),rect:[x,y,Math.max(...rs.map(r=>r.right))-x,Math.max(...rs.map(r=>r.bottom))-y]}}).filter(Boolean)''')
            issues=[]
            for t in textboxes:
                x,y,w,h=t['rect']
                if x<0 or y<0 or x+w>827 or y+h>1169:issues.append(['page',t['id']])
                if t['id'] in ns and ns[t['id']]['kind'] not in ['actor','boundary']:
                    n=ns[t['id']]
                    if x<n['x']*S-1 or y<n['y']*S-1 or x+w>(n['x']+n['w'])*S+1 or y+h>(n['y']+n['h'])*S+1:issues.append(['node-overflow',t['id']])
                for e in s['edges']:
                    if t['id'] in [e['source'],e['target']]:continue
                    pts=[(x*S,y*S) for x,y in e['points']]
                    if any(crosses(a,b,t['rect']) for a,b in zip(pts,pts[1:])):issues.append(['line-through-text',e['id'],t['id']])
            for i,t in enumerate(textboxes):
                x,y,w,h=t['rect']
                for u in textboxes[i+1:]:
                    a,b,c,d=u['rect']
                    if min(x+w,a+c)-max(x,a)>1 and min(y+h,b+d)-max(y,b)>1:issues.append(['text-overlap',t['id'],u['id']])
            report.append({'figure':key,'nodes':len(ns),'edges':len(edges),'text_boxes':textboxes,'issues':issues,'pdf_points':[pdf[0].rect.width,pdf[0].rect.height]})
        browser.close()
    for i,p in enumerate(sorted((PACK/'business-flow').glob('0*.pdf')),2):
        pdf=fitz.open(p);pdf[0].get_pixmap(dpi=105).save(OUT/f'3-{i}-business-pdf.png')
    result={'protected_original_files':len(baseline['files'])-len(changed),'allowed_modified_originals':changed,'references_preserved':True,'business_snapshot_files':len(copy),'diagrams':report,'note':'Geometric checks and screenshots support, but do not replace, visual review; no application or real-model tests executed.'}
    (OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    issues=[(r['figure'],r['issues']) for r in report if r['issues']]
    print(json.dumps({'figures':len(report),'issues':issues,'protected_original_files':result['protected_original_files']},ensure_ascii=False))
    assert not issues
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--chromium',default='/usr/bin/chromium');args=parser.parse_args();main(args.chromium)
