"""Final thesis acceptance checks against actual exported PDF, not named styles."""
from pathlib import Path
from zipfile import ZipFile
import json,os,re,hashlib,textwrap,csv
import fitz
from docx import Document
from lxml import etree
ROOT=Path(__file__).resolve().parents[2]
DELIVERY=os.environ['THESIS_DELIVERY_ID'];RUN=ROOT/'docs/validation'/DELIVERY;OUT=ROOT/'output/thesis'/DELIVERY
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def norm(s):return re.sub(r'[\s\u200b\u00ad]+','',s)
def main():
 pdfname='毕业论文-字体受限预览.pdf' if os.environ.get('THESIS_ALLOW_SUBSTITUTE_PREVIEW')=='1' else '毕业论文.pdf'
 pdf=fitz.open(OUT/pdfname);md=(ROOT/'docs/thesis/毕业论文.md').read_text(encoding='utf-8');doc=Document(OUT/'毕业论文.docx')
 errors=[]
 def check(ok,detail):
  if not ok:errors.append(detail)
 texts=[p.get_text() for p in pdf];hits=[]
 for i,text in enumerate(texts):
  hits.extend({'page':i+1,'term':m[0]} for m in re.finditer('暂定|待导师|认可|倒写|取消|缺少 release|白名单|资料来源：',text))
 check(not hits,{'sensitive_hits':hits})
 landscape=[]
 for i,p in enumerate(pdf):
  if p.rect.width>p.rect.height:landscape.append(i+1)
  check(abs(p.rect.width-595.3)<.15 and abs(p.rect.height-841.9)<.15,{'non_portrait_a4':i+1})
 check(not landscape,{'landscape':landscape})
 toc=pdf.get_toc();start=next(p for _,t,p in toc if norm(t)=='1绪论')
 mapping=json.loads((RUN/'page-map.json').read_text(encoding='utf-8'))
 # Verify printed entries in all three lists, in addition to link destinations.
 with ZipFile(OUT/'毕业论文.docx') as z:
  tree=etree.fromstring(z.read('word/document.xml'));field_text=tree.xpath('//w:instrText/text()',namespaces=NS)
  check(any('TOC \\f T' in x for x in field_text),'Missing automatic table list field')
  check(any('TOC \\f F' in x for x in field_text),'Missing automatic figure list field')
  check(len(tree.xpath('//w:fldSimple[starts-with(@w:instr,"TC ")]',namespaces=NS))==57,'Expected 29 table and 28 figure TC caption fields')
  check(len(tree.xpath('//w:instrText[contains(.,"SEQ ")]',namespaces=NS))==57,'Expected 57 automatic SEQ caption fields')
 entries=json.loads((RUN/'heading-keys.json').read_text(encoding='utf-8'))+json.loads((RUN/'list-keys.json').read_text(encoding='utf-8'))
 list_checks=[]
 for title,key,level in entries:
  if key.startswith(('fig','tab')):
   candidates=[i+1 for i,t in enumerate(texts) if i+1>=start and norm(title) in norm(t)]
   actual=str(candidates[0]-start+1) if candidates else None
  else:
   page=next(p for _,t,p in toc if norm(t)==norm(title));actual='I' if key=='abstract_cn' else 'II' if key=='abstract_en' else str(page-start+1)
  expected=norm(title)+str(actual)
  pages=[i+1 for i,t in enumerate(texts[:start-1]) if expected in re.sub(r'[.．·…]{2,}','',norm(t))]
  check(actual==mapping.get(key) and bool(pages),{'directory_mismatch':title,'actual':actual,'cache':mapping.get(key),'list_pages':pages})
  list_checks.append({'title':title,'printed_page':actual,'list_pdf_pages':pages})
 # Main TOC ends immediately before the table-list heading.
 table_heading=next((i for i,t in enumerate(texts) if norm('表 目 录') in norm(t)),None)
 check(table_heading is not None,'Table-list heading absent')
 main_toc_pages=table_heading-1 if table_heading is not None else None
 check(main_toc_pages is not None and 3<=main_toc_pages<=4,{'main_toc_pages':main_toc_pages})
 # A physical table chunk is explicitly kept together, starts with the proper
 # caption, repeats its header, and has every cell on the same actual PDF page.
 chunks=json.loads((RUN/'table-chunks.json').read_text(encoding='utf-8'));table_checks=[];cursor=start
 for chunk in chunks:
  cap=chunk['caption'];minimum=cursor+1 if chunk['chunk_index'] else cursor
  candidates=[i+1 for i,t in enumerate(texts) if i+1>=minimum and norm(cap) in norm(t)]
  if not candidates:
   errors.append({'table_caption_missing':cap,'after':minimum});continue
  page=candidates[0];cursor=page;pt=norm(texts[page-1]);missing=[cell for row in [chunk['headers']]+chunk['rows'] for cell in row if norm(cell) not in pt]
  check(not missing,{'table_chunk_overflow':cap,'page':page,'missing_cells':missing})
  header_ok=all(norm(x) in pt for x in chunk['headers']);check(header_ok,{'header_missing':cap,'page':page})
  if chunk['chunk_index']:
   lines=[(l['bbox'][1],''.join(s['text'] for s in l['spans'])) for b in pdf[page-1].get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] if 72<l['bbox'][1]<pdf[page-1].rect.height-60]
   first=min(lines)[1] if lines else ''
   check(norm(cap)==norm(first),{'continuation_not_at_page_top':cap,'page':page,'first_line':first})
  table_checks.append({'caption':cap,'pdf_page':page,'rows':len(chunk['rows']),'all_cells_on_page':not missing,'repeated_header':header_ok})
 # No isolated English plural caused by character-level wrapping in tables.
 broken=[]
 for i,p in enumerate(pdf):
  for b in p.get_text('dict')['blocks']:
   if b['type']!=0:continue
   for l in b['lines']:
    text=''.join(s['text'] for s in l['spans']).strip()
    if text=='s':broken.append(i+1)
 check(not broken,{'isolated_plural_s_pages':broken})
 # All source excerpts and source hashes must remain exactly the audited ones.
 excerpts=json.loads((ROOT/'docs/validation/thesis-final-quality-20261113/code-excerpts.json').read_text(encoding='utf-8'))
 source_checks=[];body=norm(''.join(p.get_text(clip=fitz.Rect(0,72,p.rect.width,p.rect.height-60)) for p in pdf))
 for rec in excerpts:
  p=ROOT/rec['path'];source_lines=p.read_text(encoding='utf-8').splitlines()
  window=[l.strip() for l in source_lines[rec['start_line']-1:rec['end_line']]]
  printed=[l.strip() for l in rec['text'].split('\n') if '……' not in l and l.strip()]
  it=iter(window);subsequence=all(any(l==w for w in it) for l in printed)
  good=hashlib.sha256(p.read_bytes()).hexdigest()==rec['source_sha256'] and subsequence and rec['text'] in md and norm(rec['text']) in body
  check(good,{'source_code_changed_or_lost':rec['number']});source_checks.append({'number':rec['number'],'exact':good})
 codes=[p for p in doc.paragraphs if p.style.name=='Thesis Code'];check(len(codes)==237,{'code_lines':len(codes)})
 for p in codes:
  check(abs(p.paragraph_format.line_spacing.pt-12.5)<.01,'Code leading mismatch')
  for r in p.runs:
   check(r.font.name=='Courier New' and r.font.size.pt==9.5,{'code_style':p.text[:60]})
  check(bool(p._p.xpath('./w:pPr/w:shd[@w:fill="F8F9FA"]')),'Code shading absent')
 result={'pdf_file':pdfname,'pdf_pages':len(pdf),'sensitive_match_count':len(hits),'sensitive_hits':hits,'landscape_pages':landscape,'all_portrait_a4':not landscape,'main_toc_pages':main_toc_pages,'directory_entries':len(list_checks),'directory_checks':list_checks,'table_chunks':table_checks,'isolated_plural_s_pages':broken,'exact_code_excerpts':source_checks,'code_paragraphs':len(codes),'code_font':'Courier New 9.5pt / Chinese SimSun; exact 12.5pt leading','figures':28,'body_tables':27,'appendix_tables':2,'references':27,'errors':errors,'automated_checks_passed':not errors,'visual_review':'All-page rendering and human visual inspection are separate; this script does not certify image text or visual quality.','microsoft_word_verified':False}
 (RUN/'master-final-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k not in {'directory_checks','table_chunks','exact_code_excerpts'}},ensure_ascii=False))
 assert not errors,errors
if __name__=='__main__':main()
