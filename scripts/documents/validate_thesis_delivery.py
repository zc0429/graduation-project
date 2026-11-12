"""Check current DOCX/PDF structure and pagination; visual review remains a separate step."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from docx import Document
from docx.oxml.ns import qn
import hashlib,json,re,subprocess
import pymupdf
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'docs/validation/learning-delivery-20261112';OUT=ROOT/'output/thesis/learning-delivery-20261112'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def norm(s):return re.sub(r'\s+','',s)
def main():
 md=(ROOT/'docs/thesis/毕业论文.md').read_text();opening=(ROOT/'docs/thesis/开题报告.md').read_text()
 refs=re.findall(r'^\[(\d+)\]\s*(.+)$',md,re.M);assert len(refs)==20 and refs==re.findall(r'^\[(\d+)\]\s*(.+)$',opening,re.M)
 chapters=re.findall(r'^## ([1-9]) (.+)$',md,re.M);assert [n for n,_ in chapters]==list('123456789')
 for target in re.findall(r'!\[[^]]*\]\(([^)]+)\)',md):assert (ROOT/'docs/thesis'/target).is_file(),target
 d=Document(OUT/'毕业论文.docx')
 for sec in d.sections:
  for name,expected in [('left_margin',2.75),('right_margin',2.5),('top_margin',2.5),('bottom_margin',2.5),('header_distance',1.5),('footer_distance',1.5)]:assert abs(getattr(sec,name).cm-expected)<.01,(name,getattr(sec,name).cm)
 chapter_xml=[]
 for i,p in enumerate(d.paragraphs):
  if p.style.name=='Heading 1' and re.match(r'^[1-9] ',p.text):
   br=d.paragraphs[i-1]._p.xpath('.//w:br[@w:type="page"]');assert br,('Missing Ctrl+Enter page break',p.text)
   assert p.runs[-1].font.size.pt==14,p.text
   chapter_xml.append(p.text)
 assert len(chapter_xml)==9
 for table in d.tables:
  assert table.rows[0]._tr.xpath('./w:trPr/w:tblHeader')
  assert all(row._tr.xpath('./w:trPr/w:cantSplit') for row in table.rows)
  assert table._tbl.xpath('./w:tblPr/w:tblBorders/w:insideV[@w:val="nil"]')
 with ZipFile(OUT/'毕业论文.docx') as z:
  tree=E.fromstring(z.read('word/document.xml'));bookmarks=set(tree.xpath('//w:bookmarkStart/@w:name',namespaces=ns));links=set(tree.xpath('//w:hyperlink/@w:anchor',namespaces=ns));assert not links-bookmarks,links-bookmarks
  assert tree.xpath('//w:instrText[contains(.,"TOC")]',namespaces=ns)
  assert tree.xpath('//w:pgNumType[@w:fmt="upperRoman"]',namespaces=ns)
  assert tree.xpath('//w:pgNumType[@w:fmt="decimal"]',namespaces=ns)
  # Original template headers and images remain intact; footer centering is separately checked visually.
  tpl=next((ROOT/'docs/materials/27届毕业设计学校通知和模板').rglob('*正文模板.docx'))
  with ZipFile(tpl) as original:
   for name in original.namelist():
    if re.fullmatch(r'word/header\d+\.xml',name):assert original.read(name)==z.read(name),name
 pdf=pymupdf.open(OUT/'毕业论文.pdf');toc={norm(t):page for _,t,page in pdf.get_toc()};start=toc[norm('1 绪论')]
 mapping=json.loads((RUN/'page-map.json').read_text());entries=json.loads((RUN/'heading-keys.json').read_text())
 for title,key,_ in entries:
  actual='I' if key=='abstract_cn' else 'II' if key=='abstract_en' else str(toc[norm(title)]-start+1)
  assert mapping[key]==actual,(title,mapping[key],actual)
 full_text=norm(''.join(page.get_text() for page in pdf))
 missing_cells=[]
 for table in d.tables:
  for row in table.rows:
   for cell in row.cells:
    text=norm(cell.text)
    if text and text not in full_text:missing_cells.append(cell.text)
 assert not missing_cells,('PDF missing table content',missing_cells)
 bounds=[];chapter_pages=[]
 for n,title in chapters:
  page=toc[norm(n+' '+title)];chapter_pages.append({'chapter':n,'pdf_page':page,'body_page':page-start+1})
  lines=[x.strip() for x in pdf[page-1].get_text().splitlines() if x.strip() and not re.fullmatch(r'[IVX0-9]+',x.strip())]
  assert norm(lines[0])==norm(n+' '+title),(n,lines[:2])
 for i,page in enumerate(pdf):
  assert min(abs(page.rect.width-595.3),abs(page.rect.height-595.3))<.1
  assert '\ufffd' not in page.get_text()
  if i>=start-1:assert str(i-start+2) in page.get_text().splitlines()[:3],('body page number',i+1)
  for block in page.get_text('dict')['blocks']:
   if block['type']!=0:continue
   for line in block['lines']:
    for span in line['spans']:
     x0,y0,x1,y1=span['bbox']
     if x0<0 or y0<0 or x1>page.rect.width+.1 or y1>page.rect.height+.1:bounds.append([i+1,span['text'],span['bbox']])
 assert not bounds,bounds
 fonts=subprocess.check_output(['pdffonts',str(OUT/'毕业论文.pdf')],text=True);(RUN/'pdf-fonts.txt').write_text(fonts)
 assert 'NotoSerifCJKsc' in fonts and 'LiberationSerif' in fonts
 result={'template_sha256':hashlib.sha256(tpl.read_bytes()).hexdigest(),'chapters':chapter_pages,'true_chapter_page_breaks':9,'pdf_pages':len(pdf),'landscape_pages':[i+1 for i,p in enumerate(pdf) if p.rect.width>p.rect.height],'references':20,'figure_count':len(re.findall(r'^\*\*图 ',md,re.M)),'table_count':len(re.findall(r'^\*\*表 ',md,re.M)),'toc_destinations':len(entries),'docx_tables_including_continuations':len(d.tables),'page_bounds_errors':bounds,'original_fonts_verified':False,'visual_review':'Separate manual rendering review; this script does not certify visual quality.'}
 (RUN/'document-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
