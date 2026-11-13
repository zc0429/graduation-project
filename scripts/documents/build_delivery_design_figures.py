"""Update current design figure copies without rewriting their historical evidence."""
from pathlib import Path
import json
import pymupdf
from reportlab.pdfgen import canvas
import build_thesis_figures as r
from delivery_svg_fonts import embed
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/thesis/delivery-20261112/figures'
for key in ['5-1','6-5']:
 s=json.loads((ROOT/'docs/thesis/structure-20261112/figures/sources'/f'{key}.json').read_text())
 for op in s['ops']:
  if op['kind']=='text':
   op['text']=op['text'].replace('10 张物理表','11 张物理表').replace('embedding-3：1024 维','向量服务：1024 维').replace('embedding-3 生成题干向量','向量服务生成题干向量')
 (OUT/f'{key}.json').write_text(json.dumps(s,ensure_ascii=False,indent=2));(OUT/f'{key}.svg').write_text(embed(r.svg(s),s))
 tmp=OUT/f'{key}-crop.pdf';c=canvas.Canvas(str(tmp),pagesize=(r.WIDTH,s['height']));r.render(s,c);c.save()
 with pymupdf.open(tmp) as doc:doc[0].get_pixmap(dpi=300).save(OUT/f'{key}.png')
 tmp.unlink();c=canvas.Canvas(str(OUT/f'{key}.pdf'),pagesize=(595.2756,841.8898));r.render(s,c,dx=77.95,top=735);r.draw_text(c,300,760,s['caption'],10.5);c.save()
