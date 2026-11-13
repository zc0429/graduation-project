"""Render every delivered PDF page and four-page sheets for human visual inspection."""
from pathlib import Path
import csv,json,re
import pymupdf
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'docs/validation/thesis-audit-20261112'
pdf=pymupdf.open(ROOT/'output/thesis/thesis-audit-20261112/毕业论文.pdf')
local=ROOT/'.local/audit/pdf-pages';local.mkdir(parents=True,exist_ok=True)
proof=RUN/'page-proofs';proof.mkdir(parents=True,exist_ok=True)
rows=[]
for i,p in enumerate(pdf):
 path=local/f'page-{i+1:03}.png';p.get_pixmap(dpi=120,alpha=False).save(path)
 rows.append({'pdf_page':i+1,'orientation':'landscape' if p.rect.width>p.rect.height else 'portrait','characters':len(re.sub(r'\s','',p.get_text())),'images':len(p.get_images()),'first_lines':' / '.join(p.get_text().splitlines()[:4]),'proof_sheet':f'sheet-{i//4+1:02}.jpg'})
for k in range(0,len(pdf),4):
 sheet=Image.new('RGB',(1600,2240),'#d9d9d9');draw=ImageDraw.Draw(sheet)
 for j in range(4):
  if k+j>=len(pdf):break
  im=Image.open(local/f'page-{k+j+1:03}.png');im.thumbnail((780,1080))
  x=(j%2)*800+(800-im.width)//2;y=(j//2)*1120+30
  sheet.paste(im,(x,y));draw.text(((j%2)*800+15,(j//2)*1120+8),f'PDF PAGE {k+j+1}',fill='black')
 sheet.save(proof/f'sheet-{k//4+1:02}.jpg',quality=90)
with (RUN/'page-inventory.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
print('Rendered',len(pdf),'pages;',len(list(proof.glob('sheet-*.jpg'))),'sheets; all full resolution pages in',local)
