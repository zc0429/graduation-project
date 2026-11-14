"""Reproduce review derivatives on Linux with Chromium; originals remain unchanged."""
from pathlib import Path
from lxml import etree as E
from PIL import Image
import re,json,hashlib
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2];out=root/'docs/thesis/final-master-20261114/figures';out.mkdir(parents=True,exist_ok=True);manifest={}
for n in [1,2,3]:
 src=root/f'docs/thesis/align-reference1-20261113/business-flow/3-{n}.svg';r=E.fromstring(src.read_bytes());texts_before=[x.text for x in r.iter() if E.QName(x).localname=='text'];title=r.xpath('//*[@data-cell-id="title"]')[0];title.getparent().remove(title)
 sx=.70;sy=1.25
 for e in r.iter():
  tag=E.QName(e).localname
  for a in ['x','x1','x2','cx','width','rx']:
   if a in e.attrib and e is not r and re.fullmatch(r'[\d.]+',e.get(a)):e.set(a,str(float(e.get(a))*sx))
  for a in ['y','y1','y2','cy','height','ry']:
   if a in e.attrib and e is not r and re.fullmatch(r'[\d.]+',e.get(a)):e.set(a,str(float(e.get(a))*sy))
  if 'd' in e.attrib:
   k=[0]
   def coord(m):
    v=float(m[0])*(sx if k[0]%2==0 else sy);k[0]+=1;return f'{v:.3f}'
   e.set('d',re.sub(r'-?\d+(?:\.\d+)?',coord,e.get('d')))
 # Coordinates only; text is rewrapped inside each node without changing its wording.
 for cell in r.xpath('//*[@data-cell-id]'):
  cid=cell.get('data-cell-id');ts=cell.xpath('.//*[local-name()="text"]')
  if not ts or cid in ['0','1'] or cid.startswith('lane'):continue
  if cid.startswith('e'):continue
  parent=ts[0].getparent();content=[x.text or '' for x in ts];x=float(ts[0].get('x'));ys=[float(x.get('y')) for x in ts];center=(min(ys)+max(ys))/2
  wrapped=[]
  for line in content:
   if len(line)>10:
    cut=(len(line)+1)//2
    if line[cut] in '、，。；：':cut+=1
    wrapped.extend([line[:cut],line[cut:]])
   else:wrapped.append(line)
  for t in ts:parent.remove(t)
  size=min(float(parent.get('font-size','16').removesuffix('px')),16)
  parent.set('font-size',str(size)+'px')
  for j,line in enumerate(wrapped):
   t=E.SubElement(parent,'{http://www.w3.org/2000/svg}text',x=str(x),y=str(center+(j-(len(wrapped)-1)/2)*18));t.text=line
 # Crop title/outer whitespace only; all lanes, edges and endpoint IDs retained.
 r.set('width','716');r.set('height','880');r.set('viewBox','58 94 712 874')
 target=out/f'3-{n}.svg';target.write_bytes(E.tostring(r));manifest[f'align-reference1-20261113/business-flow/3-{n}.png']={'file':f'3-{n}.png','source':str(src.relative_to(root)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'removed':['internal figure title'],'transform':{'x':sx,'y':sy},'text_content_unchanged_except_title':''.join(''.join(x.text or '' for x in r.iter() if E.QName(x).localname=='text').split())==''.join(''.join(texts_before[1:]).split())}
 # True text-order check independent of header gaps and wrapping.
 assert manifest[f'align-reference1-20261113/business-flow/3-{n}.png']['text_content_unchanged_except_title']
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':716,'height':880},device_scale_factor=3)
 for n in [1,2,3]:
  page.set_content('<style>body{margin:0;background:white}svg{display:block}</style>'+(out/f'3-{n}.svg').read_text());page.evaluate('document.fonts.ready');page.screenshot(path=str(out/f'3-{n}.png'))
 browser.close()
for n in range(2,7):
 src=root/f'docs/thesis/structure-20261112/figures/sources/7-{n}.json';scene=json.loads(src.read_text());ops=[op for op in scene['ops'] if op['kind']=='image'];width=1600;pieces=[]
 for op in ops:
  cx,cy,cw,ch=op['crop'];raw=Image.open(root/op['path']).convert('RGB').crop((cx,cy,cx+cw,cy+ch));w=round(op['w']/446.4567*width);pieces.append(raw.resize((w,round(ch*w/cw)),Image.Resampling.LANCZOS))
 canvas=Image.new('RGB',(width,sum(im.height for im in pieces)+16*(len(pieces)-1)),'white');y=0
 for im in pieces:canvas.paste(im,((width-im.width)//2,y));y+=im.height+16
 canvas.save(out/f'7-{n+2}.png');manifest[f'structure-20261112/figures/png/7-{n}.png']={'file':f'7-{n+2}.png','source':str(src.relative_to(root)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'retained_image_ops':ops,'removed':'editorial subtitle text outside screenshot crops; screenshot UI unmodified'}
# Remove the redundant generic title above 3.4; retain the system boundary.
src=root/'docs/thesis/requirements-20261112/figures/3-1.png';im=Image.open(src).convert('RGB');im.crop((0,round(im.height*.05),im.width,im.height)).save(out/'3-4.png')
manifest['requirements-20261112/figures/3-1.png']={'file':'3-4.png','source':str(src.relative_to(root)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'removed':'top 5% generic figure title / whitespace; actor and system-boundary pixels retained'}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('created',len(manifest),'derived figures; originals unchanged')
