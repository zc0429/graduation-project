"""Render maintained JSON figure sources to plain SVG, 300 dpi PNG and PDF.

Usage: python -X utf8 scripts/documents/build_thesis_figures.py
Requires reportlab, pymupdf, Pillow. Coordinates are typographic points, top-left.
No model calls; screenshot pixels are clipped for document layout, never repainted.
"""
from pathlib import Path
import base64
import hashlib
import json
import math
import os
import re
from xml.sax.saxutils import escape

import pymupdf
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/thesis/figures'
OUT = ROOT / 'output/pdf/thesis-figures'
WIDTH = 446.4567  # A4 minus 27.5 mm left and 25 mm right
FONT = Path(os.environ.get('THESIS_SONG_FONT', 'C:/Windows/Fonts/simsun.ttc'))
LATIN = Path(os.environ.get('THESIS_LATIN_FONT', 'C:/Windows/Fonts/times.ttf'))
pdfmetrics.registerFont(TTFont('Song', str(FONT), subfontIndex=0))
pdfmetrics.registerFont(TTFont('Latin', str(LATIN)))


def runs(s):
    result = []
    for c in s:
        font = 'Latin' if ord(c) < 128 else 'Song'
        if result and result[-1][0] == font:
            result[-1] = (font, result[-1][1] + c)
        else:
            result.append((font, c))
    return result


def text_width(s, size):
    return sum(pdfmetrics.stringWidth(t, f, size) for f, t in runs(s))


def draw_text(c, x, y, value, size=9, anchor='middle'):
    if anchor == 'middle':
        x -= text_width(value, size) / 2
    elif anchor == 'end':
        x -= text_width(value, size)
    for f, t in runs(value):
        c.setFont(f, size)
        c.drawString(x, y, t)
        x += pdfmetrics.stringWidth(t, f, size)


def render(scene, c, dx=0, top=None):
    h = scene['height']
    top = h if top is None else top
    c.saveState()
    c.translate(dx, top-h)
    if scene.get('business_flow_slug'):
        from build_business_swimlanes import SCENES, draw
        business = next(item for item in SCENES if item['slug'] == scene['business_flow_slug'])
        c.scale(WIDTH / business['width'], WIDTH / business['width'])
        draw(business, c)
        c.restoreState()
        return
    c.setLineWidth(.7)
    for op in scene['ops']:
        k = op['kind']
        c.setStrokeColorRGB(.16,.16,.16)
        c.setFillColorRGB(1,1,1)
        if k == 'rect':
            c.setFillColorRGB(*op.get('fill',[1,1,1]))
            c.rect(op['x'], h-op['y']-op['h'], op['w'], op['h'], fill=1)
        elif k == 'ellipse':
            c.ellipse(op['x'],h-op['y']-op['h'],op['x']+op['w'],h-op['y'],fill=1)
        elif k == 'line':
            pts = op['points']; c.setDash([3,2] if op.get('dash') else [])
            path=c.beginPath();path.moveTo(pts[0][0],h-pts[0][1])
            for x,y in pts[1:]:path.lineTo(x,h-y)
            c.drawPath(path);c.setDash([])
            if op.get('arrow'):
                x,y=pts[-1];a,b=pts[-2];ang=math.atan2(y-b,x-a)
                p=c.beginPath();p.moveTo(x,h-y)
                for turn in [-.5,.5]:
                    p.lineTo(x-6*math.cos(ang+turn),h-y+6*math.sin(ang+turn))
                p.close();c.setFillColorRGB(1,1,1) if op['arrow']=='open' else c.setFillColorRGB(.16,.16,.16)
                c.drawPath(p,fill=1)
        elif k == 'text':
            c.setFillColorRGB(0,0,0)
            draw_text(c,op['x'],h-op['y'],op['text'],op.get('size',9),op.get('anchor','middle'))
        elif k == 'image':
            # Crop using a PDF clipping path. The original PNG is unchanged.
            p=ROOT/op['path']; im=Image.open(p);cx,cy,cw,ch=op['crop'];scale=op['w']/cw
            c.saveState();clip=c.beginPath();clip.rect(op['x'],h-op['y']-ch*scale,op['w'],ch*scale)
            c.clipPath(clip,stroke=0)
            c.drawImage(ImageReader(im),op['x']-cx*scale,h-op['y']-(im.height-cy)*scale,
                        width=im.width*scale,height=im.height*scale)
            c.restoreState()
    c.restoreState()


def svg(scene):
    if scene.get('business_flow_slug'):
        source = ROOT/'docs/thesis/business-flow'/(scene['business_flow_slug']+'.svg')
        text = source.read_text(encoding='utf-8')
        return re.sub(r'width="1100" height="[0-9]+"',
                      f'width="157.5mm" height="{scene["height"]*25.4/72:.4f}mm"', text, count=1)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="157.5mm" height="{scene["height"]*25.4/72:.4f}mm" viewBox="0 0 {WIDTH} {scene["height"]}">',
         '<rect width="100%" height="100%" fill="white"/>']
    for i,o in enumerate(scene['ops']):
        k=o['kind']
        if k=='rect':
            color='#'+''.join(f'{round(v*255):02x}' for v in o.get('fill',[1,1,1]))
            out.append(f'<rect x="{o["x"]}" y="{o["y"]}" width="{o["w"]}" height="{o["h"]}" fill="{color}" stroke="#292929" stroke-width=".7"/>')
        elif k=='ellipse':
            out.append(f'<ellipse cx="{o["x"]+o["w"]/2}" cy="{o["y"]+o["h"]/2}" rx="{o["w"]/2}" ry="{o["h"]/2}" fill="white" stroke="#292929" stroke-width=".7"/>')
        elif k=='line':
            pts=o['points'];dash='stroke-dasharray="3 2"' if o.get('dash') else ''
            out.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="#292929" stroke-width=".7" {dash}/>')
            if o.get('arrow'):
                x,y=pts[-1];a,b=pts[-2];ang=math.atan2(y-b,x-a)
                p=[(x,y)]+[(x-6*math.cos(ang+t),y-6*math.sin(ang+t)) for t in [-.5,.5]]
                fill='white' if o['arrow']=='open' else '#292929'
                out.append(f'<polygon points="{" ".join(f"{a},{b}" for a,b in p)}" fill="{fill}" stroke="#292929" stroke-width=".7"/>')
        elif k=='text':
            out.append(f'<text x="{o["x"]}" y="{o["y"]}" font-family="Times New Roman, SimSun, serif" font-size="{o.get("size",9)}" text-anchor="{o.get("anchor","middle")}" fill="black">{escape(o["text"])}</text>')
        elif k=='image':
            p=ROOT/o['path'];im=Image.open(p);cx,cy,cw,ch=o['crop'];s=o['w']/cw
            b64=base64.b64encode(p.read_bytes()).decode()
            out.append(f'<defs><clipPath id="clip{i}"><rect x="{o["x"]}" y="{o["y"]}" width="{o["w"]}" height="{ch*s}"/></clipPath></defs>')
            out.append(f'<image x="{o["x"]-cx*s}" y="{o["y"]-cy*s}" width="{im.width*s}" height="{im.height*s}" clip-path="url(#clip{i})" xlink:href="data:image/png;base64,{b64}"/>')
    out.append('</svg>');return '\n'.join(out)


def table_proofs(c):
    """Typeset semantic Markdown tables at school-required 10.5 pt on A4."""
    source=(ROOT/'docs/thesis/毕业论文.md').read_text(encoding='utf-8')
    style=ParagraphStyle('cell',fontName='Song',fontSize=10.5,leading=13.5,wordWrap='LTR',splitLongWords=False)
    count=0
    for m in re.finditer(r'^\*\*(表 \d+\.\d+[^\n]+)\*\*\n\n((?:\|[^\n]+\n)+)',source,re.M):
        title,raw=m.groups();raw_rows=[]
        for row in raw.strip().splitlines():
            cells=[v.strip().replace('`','') for v in row.strip('|').split('|')]
            if all(re.fullmatch(r'[-: ]+',v) for v in cells):continue
            raw_rows.append(cells)
        n=len(raw_rows[0])
        if title.startswith('表 5.11'):widths=[58,48,177,WIDTH-283]
        elif title.startswith('表 5.'):widths=[98,84,134,WIDTH-316]
        elif title.startswith('表 6.1'):widths=[75,119,160,WIDTH-354]
        elif n==3:widths=[95,167,WIDTH-262]
        elif n==4:widths=[35,90,240,WIDTH-365]
        else:widths=[WIDTH/n]*n
        rows=[]
        for cells in raw_rows:
            rendered=[]
            for cell,width in zip(cells,widths):
                # Explicit measured wrapping preserves identifiers and SQL types.
                lines=[];current=''
                for token in re.findall(r"'[A-Za-z0-9_]+'|[0-9]+\.[0-9]+|[A-Za-z0-9_]+(?:\([0-9]+\))?|.",cell):
                    if current and text_width(current+token,10.5)>width-8.5:
                        if token in '，。；：）】、)' and len(current)>1:
                            tail=re.search(r'[A-Za-z0-9_]+$|.$',current).group()
                            head=current[:-len(tail)].rstrip()
                            if head:lines.append(head)
                            current=tail+token
                        else:
                            lines.append(current.rstrip());current=token.lstrip()
                    else:current+=token
                    assert text_width(current,10.5)<=width-8+.1,(title,cell,current,width)
                if current:lines.append(current.rstrip())
                markup='<br/>'.join(''.join(f'<font name="{f}">{escape(t)}</font>' for f,t in runs(ln)) for ln in lines)
                rendered.append(Paragraph(markup,style))
            rows.append(rendered)
        t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Song'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                              ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
                              ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
                              ('LINEABOVE',(0,0),(-1,0),1.5,'black'),('LINEBELOW',(0,0),(-1,0),1,'black'),
                              ('LINEBELOW',(0,-1),(-1,-1),1.5,'black')]))
        parts=[t];page=0
        while parts:
            chunk=parts.pop(0);w,h=chunk.wrap(WIDTH,640)
            if h>640:
                split=chunk.split(WIDTH,640)
                if not split:raise ValueError(f'Table row cannot fit: {title}')
                chunk=split[0];parts=split[1:]+parts;w,h=chunk.wrap(WIDTH,640)
            draw_text(c,77.95,787,'三线表校样：正文宽度 157.5 mm；宋体 / Times New Roman 五号',9,'start')
            draw_text(c,301.18,759,('续' if page else '')+title,10.5)
            chunk.drawOn(c,77.95,740-h)
            c.setLineWidth(1.5);c.line(77.95,740-h,77.95+WIDTH,740-h)
            draw_text(c,77.95,720-h,'资料来源与限定条件见正文对应表后的说明。',10.5,'start')
            c.showPage();count+=1;page+=1
    return count


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    (BASE/'svg').mkdir(parents=True,exist_ok=True);(BASE/'png').mkdir(parents=True,exist_ok=True)
    qa=ROOT/'tmp/diagram-audit';qa.mkdir(parents=True,exist_ok=True)
    scenes=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((BASE/'sources').glob('*.json'))]
    proof=canvas.Canvas(str(OUT/'图表A4校样.pdf'),pagesize=(595.2756,841.8898))
    manifest=[]
    for s in scenes:
        name=s['id'];assert s['height']<=630
        for o in s['ops']:
            if o['kind']=='text':
                assert o.get('size',9)>=9,(name,o)
                w=text_width(o['text'],o.get('size',9));anchor=o.get('anchor','middle')
                l=o['x']-(w/2 if anchor=='middle' else w if anchor=='end' else 0)
                assert l>=-0.1 and l+w<=WIDTH+.1,(name,o,l,w)
        (BASE/'svg'/f'{name}.svg').write_text(svg(s),encoding='utf-8')
        target=OUT/f'{name}.pdf';c=canvas.Canvas(str(target),pagesize=(WIDTH,s['height']))
        render(s,c);c.save()
        d=pymupdf.open(target);d[0].get_pixmap(dpi=300).save(BASE/'png'/f'{name}.png');d.close()
        proof.setFont('Song',10.5);proof.drawString(77.95,787,f'第 {name.split("-")[0]} 章图表校样  |  正文宽度 157.5 mm')
        render(s,proof,77.95,765)
        draw_text(proof,301.18,765-s['height']-21,s['caption'],10.5)
        note=s.get('note','图源按代码与数据库结构绘制；图题由正文管理。')
        for j,line in enumerate(note.split('\n')):draw_text(proof,77.95,765-s['height']-41-j*13,line,9,'start')
        proof.showPage()
        images=[{'path':o['path'],'crop':o['crop'],'sha256':hashlib.sha256((ROOT/o['path']).read_bytes()).hexdigest()} for o in s['ops'] if o['kind']=='image']
        manifest.append({'id':name,'caption':s['caption'],'evidence':s['evidence'],'height_pt':s['height'],'width_mm':157.5,'png_dpi':300,'screenshots':images})
    table_pages=table_proofs(proof)
    proof.save()
    (BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    d=pymupdf.open(OUT/'图表A4校样.pdf')
    for i,page in enumerate(d):page.get_pixmap(dpi=110).save(qa/f'proof-{i+1:02}.png')
    print(f'Rendered {len(scenes)} figures, SVG + PNG + PDF, {table_pages} table pages, {len(d)} A4 proof pages.')


if __name__=='__main__':main()
