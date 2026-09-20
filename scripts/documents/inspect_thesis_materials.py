"""Read-only extraction of school source documents for the 2026-09-20 audit."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import hashlib, json
from docx import Document

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/notes/thesis-run-20260920'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def main():
    files = list((ROOT/'docs/materials/27届毕业设计学校通知和模板').rglob('*.docx'))
    inventory=[]
    for p in files:
        if not any(x in p.name for x in ['正文模板', '撰写规范']): continue
        with ZipFile(p) as z:
            tree=etree.fromstring(z.read('word/document.xml'))
            paragraphs=[''.join(x.itertext()) for x in []]
            paragraphs=[''.join(x.xpath('.//w:t/text()',namespaces=NS)) for x in tree.xpath('//w:p',namespaces=NS)]
            stem='TEMPLATE' if '正文模板' in p.name else 'SCHOOL-REQUIREMENTS'
            (OUT/(stem+'-TEXT.txt')).write_text('\n'.join(paragraphs),encoding='utf-8')
            doc=Document(p)
            record=dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                sections=[dict(width=s.page_width.cm,height=s.page_height.cm,left=s.left_margin.cm,right=s.right_margin.cm,top=s.top_margin.cm,bottom=s.bottom_margin.cm,header=s.header_distance.cm,footer=s.footer_distance.cm) for s in doc.sections],
                paragraphs=[dict(index=i,style=x.style.name,text=x.text,xml=x._p.xml) for i,x in enumerate(doc.paragraphs)],
                parts={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()})
            (OUT/(stem+'-STRUCTURE.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
            inventory.append({k:record[k] for k in ['path','sha256','sections']})
    print(json.dumps(inventory,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
