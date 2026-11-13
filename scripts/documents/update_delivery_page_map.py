"""Cache Word PAGEREF results from actual LibreOffice PDF heading destinations."""
from pathlib import Path
import json,re,os
import pymupdf
ROOT=Path(__file__).resolve().parents[2];DELIVERY=os.environ.get('THESIS_DELIVERY_ID','thesis-align-reference1-20261113');RUN=ROOT/'docs/validation'/DELIVERY
def norm(s):return re.sub(r'\s+','',s)
pdf_name='毕业论文-字体受限预览.pdf' if os.environ.get('THESIS_ALLOW_SUBSTITUTE_PREVIEW')=='1' else '毕业论文.pdf'
pdf=pymupdf.open(ROOT/'output/thesis'/DELIVERY/pdf_name)
actual={norm(title):page for _,title,page in pdf.get_toc()}
entries=json.loads((RUN/'heading-keys.json').read_text());start=actual[norm('1 绪论')];result={}
for title,key,_ in entries:
 page=actual[norm(title)]
 result[key]='I' if key=='abstract_cn' else 'II' if key=='abstract_en' else str(page-start+1)
(RUN/'page-map.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('Mapped',len(result),'heading destinations; body starts at PDF page',start)
