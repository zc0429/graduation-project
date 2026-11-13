"""Revise figure 3.3 from retained vector sources; never overwrite PR1's artifacts."""
from pathlib import Path
import xml.etree.ElementTree as E
import json,hashlib
import pymupdf
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'docs/thesis/requirements-20261112/business-flow'
OUT=ROOT/'docs/thesis/thesis-audit-20261112/business-flow'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 slug='02-学习练习与复习'
 changes={'选择错题／知识点':'选择本人原题','或待复习任务':'或复习任务原题','查询本人原题／拓展题':'查询本人原题／拓展题','拓展题优先未练':'优先提供未练题','关联知识点／原题':'关联原题与知识点'}
 for name in [slug+'.svg',slug+'.drawio','业务流程图-三页可编辑.drawio']:
  text=(SRC/name).read_text()
  for a,b in changes.items():text=text.replace(a,b)
  (OUT/name).write_text(text)
 # Re-render vector text and connectors together; no screenshot retouching.
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1169,'height':827})
  page.set_content('<style>@page{size:A4 landscape;margin:0}body{margin:0}svg{width:297mm;height:210mm}</style>'+(OUT/(slug+'.svg')).read_text())
  page.evaluate('document.fonts.ready')
  page.pdf(path=str(OUT/(slug+'.pdf')),prefer_css_page_size=True,print_background=True)
  browser.close()
 with pymupdf.open(OUT/(slug+'.pdf')) as doc:
  assert len(doc)==1
  doc[0].get_pixmap(dpi=300).save(OUT/(slug+'.png'))
 report={'source_commit':'ed7d94c','changes':changes,'source_sha256':{n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in [slug+'.svg',slug+'.drawio','业务流程图-三页可编辑.drawio']},'note':'仅修正入口和原题/未练资源范围；分支、循环和平台先保存后提供保持。原PR1快照不变。'}
 (OUT/'provenance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
