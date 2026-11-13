"""Compact the reviewed logical DFDs for 157.5 mm thesis text width; preserve every flow."""
from copy import deepcopy
from pathlib import Path
import json,math,xml.etree.ElementTree as ET
import pymupdf
from delivery_svg_fonts import embed
from reportlab.pdfgen import canvas
import build_requirements_review as source
import build_thesis_figures as r
OUT=Path(__file__).resolve().parents[2]/'docs/thesis/delivery-20261112/figures'
S=r.WIDTH/1200

def main():
 for old in source.SCENES:
  if old['kind']!='dfd':continue
  s=deepcopy(old);ops=[]
  for n in s['nodes']:
   cy=(n['y']+n['h']/2)*1.0;n['h']=max(n['h']*1.0,60 if n['kind']=='store' else 0);n['y']=cy-n['h']/2
   if n['kind']=='store' and len(n['text'])>8:n['text']=n['text'].replace(' ','\n',1)
   lines=n['text'].split('\n')
   if n['kind']=='store':
    x,y,w,h=n['x']*S,n['y']*S,n['w']*S,n['h']*S
    ops.append(dict(kind='line',points=[(x+w,y),(x,y),(x,y+h),(x+w,y+h)]))
   else:ops.append(dict(kind='ellipse' if n['kind']=='process' else 'rect',x=n['x']*S,y=n['y']*S,w=n['w']*S,h=n['h']*S))
   for j,t in enumerate(lines):ops.append(dict(kind='text',x=(n['x']+n['w']/2)*S,y=(cy+(j-(len(lines)-1)/2)*28+8)*S,text=t,size=26*S))
  for e in s['edges']:
   e['points']=[(x,y*1.0) for x,y in e['points']];e['pos']=(e['pos'][0],e['pos'][1]*1.0)
   ops.append(dict(kind='line',points=[(x*S,y*S) for x,y in e['points']],arrow='closed'))
   t=e['label'];x,y=e['pos'];limit=7 if 700<x<950 else 8
   if 700<x<950:x-=15
   if len(t)>limit and '／' in t:
    left,right=t.split('／',1);lines=[left+'／',right]
   elif len(t)>limit:
    half=math.ceil(len(t)/2);lines=[t[:half],t[half:]]
   else:lines=[t]
   if len(lines)>1:
    horizontal=[(abs((a[0]+b[0])/2-x),a[1]) for a,b in zip(e['points'],e['points'][1:]) if abs(a[1]-b[1])<.01]
    if horizontal:
     line_y=min(horizontal)[1]
     if abs(y-line_y)<80:y+=-8 if y<line_y else 8
   e['pos']=(x,y);e['label']='\n'.join(lines)
   for j,t in enumerate(lines):ops.append(dict(kind='text',x=x*S,y=(y+(j-(len(lines)-1)/2)*28+7)*S,text=t,size=24*S))
  scene=dict(id=s['key'],caption=s['title'],height=1650*S,ops=ops)
  (OUT/(s['key']+'.json')).write_text(json.dumps(scene,ensure_ascii=False,indent=2))
  (OUT/(s['key']+'.svg')).write_text(embed(r.svg(scene),scene))
  tree=source.xml(s);cells=tree.find('.//root');cells.remove(next(c for c in cells if c.get('id')=='title'));model=tree.find('.//mxGraphModel');model.set('pageHeight','1140')
  for cell in tree.iter('mxCell'):
   style=cell.get('style','');style=style.replace('fontSize='+str(24*source.S),'fontSize='+str(26*source.S)).replace('fontSize='+str(20*source.S),'fontSize='+str(24*source.S));cell.set('style',style.replace('Noto Serif CJK SC','AR PL UMing CN'))
  ET.ElementTree(tree).write(OUT/(s['key']+'.drawio'),encoding='utf-8',xml_declaration=True)
  tmp=OUT/(s['key']+'-crop.pdf');c=canvas.Canvas(str(tmp),pagesize=(r.WIDTH,scene['height']));r.render(scene,c);c.save()
  with pymupdf.open(tmp) as d:d[0].get_pixmap(dpi=300).save(OUT/(s['key']+'.png'))
  tmp.unlink();c=canvas.Canvas(str(OUT/(s['key']+'.pdf')),pagesize=(595.2756,841.8898));r.render(scene,c,dx=77.95,top=720);r.draw_text(c,300,750,'图 '+s['key'].replace('-','.')+'　'+s['title'],10.5);c.save()
 # Existing balance checks remain authoritative because source/target/field sets are unchanged.
 (OUT/'dfd-balance.json').write_text(json.dumps(source.balance(),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
