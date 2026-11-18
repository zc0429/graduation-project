"""Check eight delivered captures and the exact permitted manuscript changes."""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import os,sys,json,hashlib,subprocess,re
from PIL import Image
from docx import Document
from lxml import etree as E
import fitz
ROOT=Path(__file__).resolve().parents[3];RUN=ROOT/'docs/validation/thesis-screenshots-20261117'
BASE='bb7bc56e449ab8168fcb4cb87879e71b0a3ca41c'
sys.path.insert(0,str(ROOT/'scripts/documents'))
from check_thesis_border_polish import embedded_figures,pixels
ident=os.environ.get('THESIS_DELIVERY_ID','thesis-screenshots-20261117/local-preview')
preview=os.environ.get('THESIS_ALLOW_SUBSTITUTE_PREVIEW')=='1'
out=ROOT/'output/thesis'/ident;validation=ROOT/'docs/validation'/ident
pdf=fitz.open(out/('毕业论文-字体受限预览.pdf' if preview else '毕业论文.pdf'))
doc=Document(out/'毕业论文.docx');embedded=embedded_figures(doc)
provenance=json.loads((ROOT/'docs/thesis/align-reference1-20261113/screenshots/provenance.json').read_text());assert len(provenance)==8
page_map=json.loads((validation/'page-map.json').read_text());assert len(page_map)==177
norm=lambda s:re.sub(r'\s+','',s)
start=next(p for _,t,p in pdf.get_toc() if norm(t)=='1绪论');figures=[]
for p in provenance:
 n=p['number'];source=ROOT/'docs'/p['file'];im=Image.open(source).convert('RGB')
 assert hashlib.sha256(source.read_bytes()).hexdigest()==p['sha256']
 assert p['deviceScaleFactor']==2 and p['account']['nickname']==('胡韬' if n=='7.8' else '赵灿')
 blob,para=embedded[n];actual=Image.open(BytesIO(blob)).convert('RGB');assert actual.size==im.size and pixels(actual)==pixels(im),(n,'DOCX image pixels')
 assert not para._p.xpath('.//*[local-name()="srcRect"]')
 number=int(page_map['fig'+n.replace('.','_')])+start-1;pg=pdf[number-1]
 candidates=[x for x in pg.get_image_info(xrefs=True) if x['bbox'][1]>70 and abs(x['width']/x['height']-im.width/im.height)<.006]
 assert candidates,(n,'PDF image missing')
 item=min(candidates,key=lambda x:abs(x['width']/x['height']-im.width/im.height));rect=fitz.Rect(item['bbox']);assert rect.x0>=70 and rect.x1<=pg.rect.width-55 and rect.y1<=pg.rect.height-55,(n,number,list(rect),list(pg.rect))
 proof=validation/'screenshots-300dpi';proof.mkdir(exist_ok=True);pg.get_pixmap(dpi=300).save(proof/f'page-{number:03}.png')
 figures.append({'number':n,'pixels':list(im.size),'pdf_page':number,'pdf_bbox':list(rect),'docx_pixels_exact':True,'uncropped':True,'provenance_hash_verified':True})
source=ROOT/'docs/thesis/毕业论文.md';original=subprocess.check_output(['git','show',BASE+':docs/thesis/毕业论文.md'],cwd=ROOT).decode()
current=source.read_text();changes=json.loads((RUN/'source-description-changes.json').read_text())
for c in changes:
 assert current.count(c['new'])==1;current=current.replace(c['new'],c['old'])
assert current==original,'Manuscript changed beyond the three approved source descriptions'
# No historical source material/business files/diagram geometry was touched.
paths=subprocess.check_output(['git','ls-tree','-r','--name-only','-z',BASE],cwd=ROOT).decode().split('\0')
protected=[p for p in paths if p.startswith(('server/','web/','docs/materials/','docs/experiments/','docs/validation/','docs/thesis/border-polish-20261114/'))]
modified=[]
for p in protected:
 old=subprocess.check_output(['git','rev-parse',BASE+':'+p],cwd=ROOT).decode().strip()
 new=subprocess.check_output(['git','hash-object',str(ROOT/p)],cwd=ROOT).decode().strip()
 if old!=new:modified.append(p)
assert not modified,modified
# Backgrounds of every thesis table remain exactly the prior official values.
old=Document(ROOT/'output/thesis/thesis-windows-fonts-44078364436-1/毕业论文.docx')
def shading(d):return [[E.tostring(x) for x in t._tbl.xpath('.//*[local-name()="shd"]')] for t in d.tables]
assert shading(doc)==shading(old),'Table shading changed'
report={'passed':True,'figures':figures,'figure_count':8,'deviceScaleFactor':2,'source_description_changes':len(changes),'other_manuscript_text_exact':True,'protected_baseline_files':len(protected),'protected_changes':modified,'business_changes':[],'table_shading_unchanged':True,'pdf_pages':len(pdf),'toc_targets':177,'capture_date':'2026-11-17','system_commit':BASE}
(validation/'screenshot-delivery-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='figures'},ensure_ascii=False))
