"""Cache Word PAGEREF results from actual LibreOffice PDF heading destinations."""
from pathlib import Path
import json,re
import pymupdf
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'docs/validation/learning-delivery-20261112'
def norm(s):return re.sub(r'\s+','',s)
pdf=pymupdf.open(ROOT/'output/thesis/learning-delivery-20261112/毕业论文.pdf')
actual={norm(title):page for _,title,page in pdf.get_toc()}
entries=json.loads((RUN/'heading-keys.json').read_text());start=actual[norm('1 绪论')];result={}
for title,key,_ in entries:
 page=actual[norm(title)]
 result[key]='I' if key=='abstract_cn' else 'II' if key=='abstract_en' else str(page-start+1)
(RUN/'page-map.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('Mapped',len(result),'heading destinations; body starts at PDF page',start)
