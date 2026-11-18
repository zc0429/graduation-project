"""Render complete diagram geometry with measured ink bounds and safe padding.

Only writes new review derivatives. Retained JSON/SVGs and screenshots are read
only. Run on Linux with Chromium and Playwright; the DOCX renderer uses the
committed PNGs on Windows without substituting or re-cropping them.
"""
from pathlib import Path
from copy import deepcopy
from math import atan2,cos,sin,hypot
from xml.sax.saxutils import escape
import argparse,hashlib,json,re
from lxml import etree as E
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/thesis/border-polish-20261114/figures'
NS='http://www.w3.org/2000/svg'
PAD=24
SCALE=4
SOURCES={
 '3.5':'align-reference1-20261113/figures/3-5.json',
 '3.6':'align-reference1-20261113/figures/3-6.json',
 '3.7':'align-reference1-20261113/figures/3-7.json',
 '3.8':'align-reference1-20261113/figures/3-8.json',
 '3.9':'align-reference1-20261113/figures/3-9.json',
 '5.1':'delivery-20261112/figures/5-1.json',
 '5.2':'align-reference1-20261113/figures/5-2.json',
 '5.3':'align-reference1-20261113/figures/5-3.json',
 '5.4':'delivery-20261112/figures/6-5.json',
 '5.5':'structure-20261112/figures/sources/6-7.json',
 '5.6':'structure-20261112/figures/sources/6-8.json',
 '6.1':'structure-20261112/figures/sources/6-1.json',
 '6.2':'structure-20261112/figures/sources/6-2.json',
 '6.3':'structure-20261112/figures/sources/6-3.json',
 '6.4':'delivery-20261112/figures/6-9.json',
 '6.5':'structure-20261112/figures/sources/6-4.json',
}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def q(tag):return '{'+NS+'}'+tag

def text_element(x,y,value,size=9,anchor='middle'):
    # Guillemets belong to Latin typography, not the CJK font's fallback cmap.
    runs=[]
    for ch in value:
        family='Times New Roman' if ord(ch)<0x250 else 'Noto Serif CJK SC'
        if runs and runs[-1][0]==family:runs[-1]=(family,runs[-1][1]+ch)
        else:runs.append((family,ch))
    body=''.join(f'<tspan font-family="{f}">{escape(t)}</tspan>' for f,t in runs)
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" xml:space="preserve">{body}</text>'

def polyline(points,dash=False,width=.8,role='connector'):
    pts=' '.join(f'{x},{y}' for x,y in points)
    return f'<polyline data-role="{role}" points="{pts}" fill="none" stroke="#292929" stroke-width="{width}"'+(' stroke-dasharray="3 2"' if dash else '')+'/>'

def line_elements(op):
    points=[tuple(p) for p in op['points']]
    if not op.get('arrow'):return polyline(points,op.get('dash',False))
    x,y=points[-1];a,b=next(p for p in reversed(points[:-1]) if p!=(x,y))
    length=hypot(x-a,y-b);ux=(x-a)/length;uy=(y-b)/length
    open_head=op['arrow']=='open';head=10 if open_head else 6;half=4.5 if open_head else 2.6
    bx=x-ux*head;by=y-uy*head
    # Stop the shaft at the triangle's BASE, rather than drawing a dashed line
    # through its interior. A short solid tail physically joins the base.
    shaft=points[:-1]+[(bx,by)] if open_head else points
    s=polyline(shaft,op.get('dash',False),role='realization-shaft' if open_head else 'connector')
    if open_head:s+=polyline([(bx-ux*4,by-uy*4),(bx,by)],role='realization-base-join')
    tri=[(x,y),(bx-uy*half,by+ux*half),(bx+uy*half,by-ux*half)]
    s+=f'<polygon data-role="{"realization-triangle" if open_head else "arrowhead"}" points="'+ ' '.join(f'{u},{v}' for u,v in tri)+f'" fill="{"white" if open_head else "#292929"}" stroke="#292929" stroke-width=".8" stroke-linejoin="miter"/>'
    return s

def from_ops(scene):
    ops=deepcopy(scene['ops']);parts=[]
    for o in ops:
        k=o['kind']
        if k=='rect':
            fill='#'+''.join(f'{round(v*255):02x}' for v in o.get('fill',[1,1,1]))
            parts.append(f'<rect x="{o["x"]}" y="{o["y"]}" width="{o["w"]}" height="{o["h"]}" fill="{fill}" stroke="#292929" stroke-width=".8"/>')
        elif k=='ellipse':parts.append(f'<ellipse cx="{o["x"]+o["w"]/2}" cy="{o["y"]+o["h"]/2}" rx="{o["w"]/2}" ry="{o["h"]/2}" fill="white" stroke="#292929" stroke-width=".8"/>')
        elif k=='line':parts.append(line_elements(o))
        elif k=='text':parts.append(text_element(o['x'],o['y'],o['text'],o.get('size',9),o.get('anchor','middle')))
        else:raise ValueError(('Unreviewed operation',k))
    return '<svg xmlns="'+NS+'" width="1200" height="1800" viewBox="-100 -100 1200 1800">'+''.join(parts)+'</svg>'

def usecase(scene):
    parts=[]
    for n in scene['nodes']:
        x,y,w,h=n['x'],n['y'],n['w'],n['h'];cx=x+w/2;cy=y+h/2
        if n['kind']=='boundary':parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="black" stroke-width="2"/>')
        elif n['kind']=='actor':
            parts.append(f'<circle cx="{cx}" cy="{y+15}" r="14" fill="white" stroke="black" stroke-width="1.5"/>')
            parts.extend([polyline(p,width=1.5) for p in [[(cx,y+29),(cx,y+70)],[(x,y+43),(x+w,y+43)],[(cx,y+70),(x,y+h)],[(cx,y+70),(x+w,y+h)]]])
            parts.append(text_element(cx,y+h+29,n['text'],24))
        else:
            assert n['kind']=='usecase';parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" fill="white" stroke="black" stroke-width="1.5"/>');parts.append(text_element(cx,cy+8,n['text'],24))
    for e in scene['edges']:parts.append(polyline(e['points'],width=1.3))
    return '<svg xmlns="'+NS+'" width="1200" height="1700" viewBox="0 0 1200 1700">'+''.join(parts)+'</svg>'

def swimlane(path):
    # This complete retained SVG still contains the previously clipped lines.
    # Its old viewport is ignored; it is never used as a pixel crop boundary.
    r=E.fromstring(path.read_bytes())
    for e in list(r.iter()):
        if E.QName(e).localname=='rect' and e.get('width')=='100%' and e.get('height')=='100%' and e.get('stroke') in {None,'none'}:
            e.getparent().remove(e)
    for e in r.iter():
        if 'stroke-width' in e.attrib:e.set('stroke-width','1.6')
    coords=[]
    for lane in r.xpath('//*[@data-cell-id="lane0" or @data-cell-id="lane1" or @data-cell-id="lane2"]'):
        for p in lane.xpath('.//*[local-name()="path"]'):
            nums=list(map(float,re.findall(r'-?\d+(?:\.\d+)?',p.get('d'))))
            coords.extend(zip(nums[::2],nums[1::2]))
    # The lanes' geometry has a retained translate(0.5,0.5).
    x0=min(x for x,y in coords)+.5;x1=max(x for x,y in coords)+.5
    y0=min(y for x,y in coords)+.5;y1=max(y for x,y in coords)+.5
    frame=E.SubElement(r,q('rect'),x=str(x0),y=str(y0),width=str(x1-x0),height=str(y1-y0),fill='none',stroke='black',**{'stroke-width':'1.6','data-role':'closed-outer-frame'})
    r.set('width','1400');r.set('height','1800');r.set('viewBox','-100 -100 1400 1800')
    return E.tostring(r).decode(),{'x':x0,'y':y0,'w':x1-x0,'h':y1-y0,'stroke_width':1.6}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--figures',nargs='+',help='Only rebuild these figure numbers; retain other manifest records and files')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    md=(ROOT/'docs/thesis/毕业论文.md').read_text(encoding='utf-8')
    targets={}
    for m in re.finditer(r'!\[[^\]]*\]\(([^)]+)\)\s*\n\s*\*\*图 (\d+\.\d+)',md):targets[m[2]]=m[1]
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8')) if args.figures else {}
    if args.figures:assert set(args.figures)<=set(targets),args.figures
    checks=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1400,'height':1800},device_scale_factor=SCALE)
        for number,target in targets.items():
            if number.startswith('7.'):continue
            if args.figures and number not in args.figures:continue
            frame=None
            if number in {'3.1','3.2','3.3'}:
                source=ROOT/'docs/thesis/final-master-20261114/figures'/(number.replace('.','-')+'.svg');svg,frame=swimlane(source)
            elif (ROOT/'docs/thesis/final-master-20261114/figures'/(number.replace('.','-')+'.svg')).is_file():
                source=ROOT/'docs/thesis/final-master-20261114/figures'/(number.replace('.','-')+'.svg')
                svg=source.read_text(encoding='utf-8')
            elif number=='3.4':
                source=ROOT/'docs/thesis/requirements-20261112/figures/diagrams.json';scene=next(s for s in json.loads(source.read_text()) if s['key']=='3-1');svg=usecase(scene)
            else:
                source=ROOT/'docs/thesis'/SOURCES[number];scene=json.loads(source.read_text());svg=from_ops(scene)
            page.set_content('<style>html,body{margin:0;background:white}svg{display:block;background:white}</style>'+svg)
            page.evaluate('document.fonts.ready')
            # getBBox includes full text ascenders/descenders, even outside the
            # legacy page height, fixing the half-clipped 08:00 label in 5.6.
            info=page.evaluate('''() => {
              const svg=document.querySelector('svg'); const b=svg.getBBox();
              const pad=24; const x=b.x-pad,y=b.y-pad,w=Math.ceil(b.width+2*pad),h=Math.ceil(b.height+2*pad);
              svg.setAttribute('viewBox',`${x} ${y} ${w} ${h}`);svg.setAttribute('width',w);svg.setAttribute('height',h);
              return {viewBox:[x,y,w,h],ink:[b.x,b.y,b.width,b.height],texts:[...svg.querySelectorAll('text')].map(t=>t.textContent),rectangles:[...svg.querySelectorAll('rect')].map(r=>({x:+r.getAttribute('x'),y:+r.getAttribute('y'),w:+r.getAttribute('width'),h:+r.getAttribute('height')}))};
            }''')
            w,h=info['viewBox'][2:];page.set_viewport_size({'width':w,'height':h})
            name=number.replace('.','-');png=OUT/(name+'.png');page.screenshot(path=str(png))
            # Preserve complete measured SVG as the source for the exact PNG.
            rendered=page.locator('svg').evaluate('(s)=>s.outerHTML');(OUT/(name+'.svg')).write_text(rendered,encoding='utf-8')
            im=Image.open(png).convert('RGB');im.save(png,dpi=(300,300));box=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox();assert box
            margins=[box[0],box[1],im.width-box[2],im.height-box[3]];assert min(margins)>=80 and max(margins)<=128,(number,margins)
            if number=='6.5':
                rr=E.fromstring(rendered.encode());assert len(rr.xpath('//*[@data-role="realization-triangle"]'))==1
                assert '«interface» LlmClient' in info['texts'] and not any('<<<<' in s for s in info['texts'])
            if number=='5.6':assert '每日 08:00 扫描' in info['texts']
            record={'number':number,'file':png.name,'source':str(source.relative_to(ROOT)),'source_sha256':digest(source),'png_sha256':digest(png),'svg_sha256':digest(OUT/(name+'.svg')),'padding_svg_units':PAD,'raster_scale':SCALE,'pixel_size':list(im.size),'actual_white_margins_px':margins,'viewBox':info['viewBox'],'rectangles':info['rectangles'],'closed_outer_frame':frame,'text_content':info['texts'],'semantics':'Original nodes, edges and labels retained; frame/padding and vector arrowheads repaired.'}
            if source.suffix=='.svg':
                original=E.fromstring(svg.encode())
                assert info['texts']==[''.join(t.itertext()) for t in original.iter(q('text'))]
            elif number not in {'3.1','3.2','3.3','3.4'}:assert info['texts']==[o['text'] for o in scene['ops'] if o['kind']=='text']
            manifest[target]=record;checks.append({'number':number,'margins_px':margins,'pixel_size':list(im.size)})
        browser.close()
    assert len(manifest)==20
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False))
if __name__=='__main__':main()
