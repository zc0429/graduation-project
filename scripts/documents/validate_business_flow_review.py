"""Validate native editable flow diagrams and their actual SVG/PDF/PNG exports."""
from pathlib import Path
import functools, hashlib, http.server, itertools, json, math, runpy, threading, urllib.parse, xml.etree.ElementTree as ET
import fitz
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
M=runpy.run_path(str(ROOT/'scripts/documents/build_business_flow_review.py'))
OUT=M['OUT'];SCENES=M['SCENES'];sx=M['sx'];sy=M['sy'];scale=M['SCALE']*M['INSET']
EV=ROOT/'docs/validation/business-flow-review-20261111-r2'
EV.mkdir(exist_ok=True)
report={'baseline_dev':'4093a1cb77eca2f06b2924daf954a55860a7249b','pages':[], 'method':'Structure + native SVG browser glyph ink bounds (Canvas actualBoundingBox metrics, not font line boxes) + PDF text/page/ink bounds + PNG dimensions. Visual inspection documented separately.'}
M['structural_checks']()

def reach(s,k):
    seen=set();todo=[k]
    while todo:
        x=todo.pop()
        if x in seen:continue
        seen.add(x);todo += [e['target'] for e in s['edges'] if e['source']==x]
    return seen

def cross(a,b,c,d):
    if a[0]==b[0] and c[1]==d[1]:return min(c[0],d[0])<a[0]<max(c[0],d[0]) and min(a[1],b[1])<c[1]<max(a[1],b[1])
    if a[1]==b[1] and c[0]==d[0]:return min(a[0],b[0])<c[0]<max(a[0],b[0]) and min(c[1],d[1])<a[1]<max(c[1],d[1])
    return False

def direction(p,q,side,outward):
    dx,dy=q[0]-p[0],q[1]-p[1]
    sign={'l':-dx,'r':dx,'t':-dy,'b':dy}[side]
    return sign>0 if outward else sign<0

httpd=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(OUT)))
threading.Thread(target=httpd.serve_forever,daemon=True).start()
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1169,'height':827},device_scale_factor=1)
    for idx,s in enumerate(SCENES):
        nodes={n['id']:n for n in s['nodes']};issues=[]
        for e in s['edges']:
            if e.get('semantic_only'):continue
            assert direction(e['points'][0],e['points'][1],e['start'],True),(s['slug'],e['id'],'exit direction')
            assert direction(e['points'][-2],e['points'][-1],e['end'],False),(s['slug'],e['id'],'entry direction')
        for e,f in itertools.combinations(s['edges'],2):
            for a,b in zip(e['points'],e['points'][1:]):
                for c,d in zip(f['points'],f['points'][1:]):
                    assert not cross(a,b,c,d),(s['slug'],e['id'],f['id'],'cross')
        if idx==2:
            assert 'teacher' not in reach(s,'admin') and 'admin' not in reach(s,'teacher')
            assert 'teacher_process' not in reach(s,'admin_process') and 'admin_process' not in reach(s,'teacher_process')
        if idx==1:
            # Business route invariants: reading does not submit practice, both can loop, failure can exit.
            assert not any(e['source']=='learn' and e['target']=='record' for e in s['edges'])
            assert any(e['source']=='practice' and e['target']=='record' for e in s['edges'])
            assert 'select' in reach(s,'learn') and 'select' in reach(s,'record')
            assert 'end' in reach(s,'failure_out') and 'select' in reach(s,'failure_out')
            assert len([e for e in s['edges'] if e['target']=='finish'])==1
        xml=ET.parse(OUT/(s['slug']+'.drawio'));cells=xml.findall('.//mxCell')
        assert len([c for c in cells if c.get('edge')=='1'])==len([e for e in s['edges'] if not e.get('semantic_only')])
        assert all('endArrow=block' in c.get('style','') for c in cells if c.get('edge')=='1')
        svg=OUT/(s['slug']+'.svg');r=ET.parse(svg).getroot()
        assert not r.findall('.//{*}foreignObject')
        assert 'data:font/woff;base64,' in svg.read_text()
        page.goto(f'http://127.0.0.1:{httpd.server_port}/')
        svg_markup=svg.read_text().split('?>',1)[-1]
        page.set_content('<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;width:1169px;height:827px">'+svg_markup+'</body></html>')
        page.evaluate('document.fonts.ready')
        boxes=page.evaluate('''() => [...document.querySelectorAll('g[data-cell-id]')].map(g=>({id:g.dataset.cellId, text:[...g.querySelectorAll('text')].map(t=>{let cs=getComputedStyle(t),cv=document.createElement('canvas'),ctx=cv.getContext('2d');ctx.font=cs.fontStyle+' '+cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;let a=ctx.measureText(t.textContent),x=t.x.baseVal.getItem(0).value,y=t.y.baseVal.getItem(0).value;if(cs.textAnchor==='middle')x-=a.width/2;else if(cs.textAnchor==='end')x-=a.width;let m=t.getCTM(),p=new DOMPoint(x-a.actualBoundingBoxLeft,y-a.actualBoundingBoxAscent).matrixTransform(m),q=new DOMPoint(x+a.actualBoundingBoxRight,y+a.actualBoundingBoxDescent).matrixTransform(m);return {text:t.textContent,x:p.x,y:p.y,w:q.x-p.x,h:q.y-p.y}})})).filter(x=>x.text.length)''')
        for b in boxes:
            if b['id'] not in nodes:continue
            n=nodes[b['id']];x,y,w,h=sx(n['x']),sy(n['y']),n['w']*scale,n['h']*scale
            for t in b['text']:
                # Native renderer uses a half-pixel translation. Allow 1.5px raster rounding.
                if not (t['x']>=x-1.5 and t['x']+t['w']<=x+w+1.5 and t['y']>=y-1.5 and t['y']+t['h']<=y+h+1.5):issues.append({'node':n['id'],'text':t,'type':'text_rect'})
                if n['kind']=='decision':
                    for cx,cy in [(t['x'],t['y']),(t['x']+t['w'],t['y']),(t['x'],t['y']+t['h']),(t['x']+t['w'],t['y']+t['h'])]:
                        norm=abs(cx-(x+w/2))/(w/2)+abs(cy-(y+h/2))/(h/2)
                        if norm>1.02:issues.append({'node':n['id'],'type':'diamond_text','norm':round(norm,3)})
        page.screenshot(path=str(EV/f'after-svg-{idx+1}.png'),full_page=False)
        doc=fitz.open(OUT/(s['slug']+'.pdf'));assert len(doc)==1;p=doc[0]
        assert abs(p.rect.width-841.8898)<.01 and abs(p.rect.height-595.2756)<.01
        normalized=''.join(p.get_text().split())
        for n in s['nodes']:
            assert ''.join(n['text'].split()) in normalized,(s['slug'],n['id'],'PDF missing text')
        spans=[span for block in p.get_text('dict')['blocks'] if 'lines'in block for line in block['lines'] for span in line['spans']]
        min_font=min(t['size'] for t in spans)
        bounds=fitz.Rect(spans[0]['bbox'])
        for t in spans:bounds|=fitz.Rect(t['bbox'])
        assert min(bounds.x0,bounds.y0,p.rect.width-bounds.x1,p.rect.height-bounds.y1)>20,(s['slug'],'print margins',bounds)
        p.get_pixmap(dpi=160).save(EV/f'after-pdf-{idx+1}.png')
        im=Image.open(OUT/(s['slug']+'.png'));assert im.size==(3508,2481),(s['slug'],im.size)
        report['pages'].append({'page':s['slug'],'business_nodes':len(nodes),'visible_arrows':len([e for e in s['edges'] if not e.get('semantic_only')]),'one_start_one_end':True,'no_crossing_or_unrelated_node_intersection':True,'arrow_endpoint_directions':True,'native_svg_text_bounds_issues':issues,'pdf_pages':1,'a4_pt':list(p.rect)[2:],'smallest_pdf_font_pt':round(min_font,2),'text_bbox_pt':list(bounds),'png_pixels':list(im.size),'svg_embedded_fonts':True,'svg_foreign_objects':0})
    browser.close()
httpd.shutdown()
combined=fitz.open(OUT/'业务流程图-A4审阅版.pdf');assert len(combined)==3
report['combined_pdf_pages']=3
report['artifacts']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.suffix in ['.drawio','.svg','.png','.pdf','.json']}
report['passed']=not any(p['native_svg_text_bounds_issues'] for p in report['pages'])
(EV/'final-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='artifacts'},ensure_ascii=False,indent=2))
assert report['passed'],'Text boundary issues need correction'
