"""Audit effective OOXML fonts, actual PDF fonts, and protected PR #9 inputs."""
from pathlib import Path
from zipfile import ZipFile
import csv,hashlib,json,os,re
from lxml import etree as E
import fitz

ROOT=Path(__file__).resolve().parents[2]
DELIVERY=os.environ.get('THESIS_DELIVERY_ID','thesis-font-layout-20261113')
RUN=ROOT/'docs/validation'/DELIVERY
OUT=ROOT/'output/thesis'/DELIVERY
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W='{'+NS['w']+'}'

def norm(s):return re.sub(r'[\s\u200b\u00ad]+','',s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def properties(rpr):
    if rpr is None:return {}
    result={}
    for x in rpr:
        name=E.QName(x).localname
        if name=='rFonts':result.update({E.QName(k).localname:v for k,v in x.attrib.items()})
        elif name in {'sz','b'}:result[name]=x.get(W+'val','1')
    return result

def main():
    baseline=json.loads((RUN/'baseline-files.json').read_text())
    allowed={'AGENTS.md','docs/notes/进度记录.md','docs/notes/HANDOFF.md',
             'scripts/cloud/export-thesis-pdf.sh','scripts/cloud/fonts.conf',
             'scripts/documents/build_thesis_delivery.py','scripts/documents/validate_thesis_delivery.py',
             'scripts/documents/render_thesis_audit.py','scripts/documents/update_delivery_page_map.py',
             'docs/thesis/毕业论文.md','docs/references/gb7714-list.md',
             '.github/workflows/thesis-windows-fonts.yml',
             'scripts/documents/thesis_windows_cloud.py','scripts/documents/audit_thesis_font_layout.py',
             'scripts/documents/validate_thesis_references.py'}
    protected={p:h for p,h in baseline.items() if p not in allowed}
    changed=[p for p,h in protected.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    assert not changed,changed
    with ZipFile(OUT/'毕业论文.docx') as z:
        styles=E.fromstring(z.read('word/styles.xml'))
        by_id={s.get(W+'styleId'):s for s in styles.findall('w:style',NS)}
        defaults=properties(styles.find('w:docDefaults/w:rPrDefault/w:rPr',NS))
        def style_props(sid,seen=()):
            assert sid not in seen,('Style cycle',sid)
            s=by_id[sid];base=s.find('w:basedOn',NS)
            result=style_props(base.get(W+'val'),seen+(sid,)) if base is not None else dict(defaults)
            result.update(properties(s.find('w:rPr',NS)));return result
        def effective(run,p):
            sid=p.find('w:pPr/w:pStyle',NS)
            sid=sid.get(W+'val') if sid is not None else '1'
            result=style_props(sid)
            rstyle=run.find('w:rPr/w:rStyle',NS)
            if rstyle is not None:result.update(style_props(rstyle.get(W+'val')))
            result.update(properties(run.find('w:rPr',NS)))
            return result
        style_checks=[]
        expected={'Normal':(12,'宋体'),'heading 1':(14,'黑体'),'heading 2':(12,'黑体'),
                  'heading 3':(12,'黑体'),'Title':(18,'黑体'),
                  'TOC 1':(14,'黑体'),'TOC 2':(12,'黑体'),'TOC 3':(12,'黑体'),
                  'Thesis Code':(9.5,'宋体'),'footer':(9,'宋体')}
        for sid,s in by_id.items():
            name=s.find('w:name',NS).get(W+'val')
            if name not in expected:continue
            size,east=expected[name];props=style_props(sid)
            assert props['eastAsia']==east and props['sz']==str(int(size*2)),(name,props)
            assert props['ascii']==props['hAnsi']==('宋体' if name=='footer' else 'Courier New' if name=='Thesis Code' else 'Times New Roman'),(name,props)
            assert not any(k.endswith('Theme') for k in props),(name,props)
            style_checks.append({'style':name,'effective':props})
        assert len(style_checks)==len(expected)
        tree=E.fromstring(z.read('word/document.xml'))
        paragraphs=tree.findall('w:body/w:p',NS)
        for p in paragraphs[:6]:
            if p.xpath('.//w:drawing|.//w:pict',namespaces=NS):
                spacing=p.find('w:pPr/w:spacing',NS)
                assert spacing is not None and spacing.get(W+'lineRule')=='auto','Cover emblem could be clipped by fixed body leading'
        header_style=next(s for s in by_id.values() if s.find('w:name',NS).get(W+'val')=='header')
        assert header_style.find('w:pPr/w:spacing',NS).get(W+'lineRule')=='auto'
        title=next(p for p in paragraphs if norm(''.join(p.xpath('.//w:t/text()',namespaces=NS)))==norm('基于智谱GLM模型的AI错题分析与学习推荐系统设计与实现'))
        assert title.find('w:pPr/w:jc',NS).get(W+'val')=='center'
        for run in title.findall('w:r',NS):
            if not run.xpath('./w:t',namespaces=NS):continue
            props=effective(run,title);assert props['sz']=='36' and props['b']=='1' and props['eastAsia']=='黑体',props
        heading_checks=[]
        for p in paragraphs:
            text=''.join(p.xpath('.//w:t/text()',namespaces=NS))
            sid=p.find('w:pPr/w:pStyle',NS)
            if sid is None or by_id[sid.get(W+'val')].find('w:name',NS).get(W+'val') not in {'heading 1','heading 2','heading 3'}:continue
            if not re.match(r'^[1-9](?:\.\d+){0,2}\s+\S',text):continue
            level=len(text.split()[0].split('.'));size='28' if level==1 else '24'
            for run in p.findall('w:r',NS):
                if not run.xpath('./w:t',namespaces=NS):continue
                props=effective(run,p)
                assert props['sz']==size and props['eastAsia']=='黑体',(text,props)
                assert props['ascii']==props['hAnsi']=='Times New Roman'
            heading_checks.append(text)
        # Match ordinary manuscript paragraphs, excluding code, tables and headings.
        md=(ROOT/'docs/thesis/毕业论文.md').read_text()
        from build_thesis_delivery import plain
        prose={};inside_code=False
        for line in md[md.index('## 1 '):].splitlines():
            if line.startswith('```'):inside_code=not inside_code;continue
            if inside_code or not line.strip() or line.startswith(('#','|','!','>','---','**图','**表')):continue
            prose[norm(plain(line))]=21 if re.match(r'^代码\s*7\.\d+',plain(line)) or line.startswith('资料来源') or re.match(r'^\[\d+\]',line) else 24
        checked=0
        for p in paragraphs:
            text=norm(''.join(p.xpath('.//w:t/text()',namespaces=NS)))
            if text not in prose:continue
            for run in p.findall('w:r',NS):
                if not run.xpath('./w:t',namespaces=NS):continue
                props=effective(run,p)
                assert props['sz']==str(prose[text]) and props['eastAsia']==('黑体' if text.startswith('代码7.') else '宋体'),(text[:70],props)
                assert props['ascii']==props['hAnsi']=='Times New Roman',(text[:70],props)
            checked+=1
        assert checked>=180,checked
        code_paragraphs=[p for p in paragraphs if p.find('w:pPr/w:pStyle',NS) is not None
                         and by_id[p.find('w:pPr/w:pStyle',NS).get(W+'val')].find('w:name',NS).get(W+'val')=='Thesis Code']
        old_excerpts=json.loads((ROOT/'docs/validation/thesis-final-quality-20261113/code-excerpts.json').read_text())
        expected_lines=[line for r in old_excerpts for line in r['text'].split('\n')]
        assert [''.join(p.xpath('.//w:t/text()',namespaces=NS)) for p in code_paragraphs]==expected_lines
        for p in code_paragraphs:
            for run in p.findall('w:r',NS):
                props=effective(run,p);assert props['sz']=='19' and props['eastAsia']=='宋体'
                assert props['ascii']==props['hAnsi']=='Courier New'
        footers=[]
        for name in z.namelist():
            if not re.fullmatch(r'word/footer\d+\.xml',name):continue
            footer=E.fromstring(z.read(name))
            for run in footer.findall('.//w:r',NS):
                props=properties(run.find('w:rPr',NS))
                assert props['sz']=='18' and props['eastAsia']==props['ascii']==props['hAnsi']=='宋体',(name,props)
            footers.append(name)
        # The official cover's original images, headers, and page settings remain.
        template=next((ROOT/'docs/materials/27届毕业设计学校通知和模板').rglob('*正文模板.docx'))
        with ZipFile(template) as original:
            for name in original.namelist():
                if re.fullmatch(r'word/header\d+\.xml',name) or name.startswith('word/media/'):
                    assert original.read(name)==z.read(name),name
    pdf_name='毕业论文-字体受限预览.pdf' if os.environ.get('THESIS_ALLOW_SUBSTITUTE_PREVIEW')=='1' else '毕业论文.pdf'
    pdf=fitz.open(OUT/pdf_name)
    # Every page after the cover must retain the original school header, with
    # the logo inside its visible area. Text bounds alone cannot detect this.
    header_checks=[]
    for i,page in enumerate(pdf):
        if i==0:continue
        logos=[b for b in page.get_text('dict')['blocks'] if b['type']==1
               and b['width']==328 and b['height']==80 and b['bbox'][1]<80]
        assert len(logos)==1,('Missing or duplicated school header logo',i+1)
        box=logos[0]['bbox']
        assert box[1]>=0 and box[3]<=71 and box[2]<=page.rect.width,(i+1,box)
        rules=[d for d in page.get_drawings() if abs(d['rect'].y0-70.9)<.2
               and abs(d['rect'].y1-d['rect'].y0)<.2]
        assert rules,('Missing school header rule',i+1)
        header_checks.append({'pdf_page':i+1,'logo_bbox':list(box),'header_rule_present':True})
    # Exclude header/footer positions so an excerpt can continue naturally on
    # the next page without page-number text being mistaken for source code.
    pdf_body=norm(''.join(p.get_text(clip=fitz.Rect(0,60,p.rect.width,p.rect.height-60)) for p in pdf))
    for record in old_excerpts:assert norm(record['text']) in pdf_body,('Code lost in PDF',record['number'])
    # Rebuild the item index against this PDF, rather than reusing the older
    # 99-page delivery's figure/table/code/reference page numbers.
    page_text=[norm(page.get_text()) for page in pdf]
    indexed=[]
    for line in md.splitlines():
        caption=plain(line)
        match=re.match(r'^(图|表|代码)\s*([A-Z0-9]+\.\d+)\s*(.+)$',caption)
        ref=re.match(r'^\[(\d+)\]\s*(.+)$',caption)
        if match:
            kind,number,title=match.groups()
            if kind in {'图','表'} and not line.startswith('**'):continue
        elif ref:kind,number,title='文献',*ref.groups()
        else:continue
        pages=[i+1 for i,text in enumerate(page_text) if norm(caption) in text]
        assert pages,('Caption or reference not found in PDF',kind,number)
        indexed.append({'kind':kind,'number':number,'title':title,
                        'pdf_pages':';'.join(map(str,pages))})
    item_counts={kind:sum(r['kind']==kind for r in indexed) for kind in ['图','表','代码','文献']}
    assert item_counts=={'图':28,'表':29,'代码':0,'文献':27},item_counts
    with (RUN/'图表代码文献页码索引.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=['kind','number','title','pdf_pages'],lineterminator='\n')
        writer.writeheader();writer.writerows(indexed)
    names=sorted({font[3] for page in pdf for font in page.get_fonts()})
    assert any('TimesNewRoman' in f for f in names),names
    # Inspect actual glyph spans too: a registered but unused font proves nothing.
    spans=[s for page in pdf for block in page.get_text('dict')['blocks'] if block['type']==0
           for line in block['lines'] for s in line['spans']]
    tnr_spans=[s for s in spans if 'TimesNewRoman' in s['font']]
    assert any(re.search(r'[A-Za-z0-9]',s['text']) for s in tnr_spans)
    assert any(abs(s['size']-12)<.05 for s in tnr_spans)
    title_spans=[s for s in pdf[0].get_text('dict')['blocks'] if s['type']==0
                 for line in s['lines'] for s in line['spans'] if any(t in s['text'] for t in ['基于智谱','与学习推荐'])]
    assert title_spans and all(abs(s['size']-18)<.05 for s in title_spans),title_spans
    # The page-number rule is 9pt Song; preview rendering is clearly qualified.
    start=next(page for _,title,page in pdf.get_toc() if norm(title)=='1绪论')
    page_spans=[]
    for title,expected in [('摘要','I'),('Abstract','II')]:
        index=next(page for _,name,page in pdf.get_toc() if norm(name)==title)-1
        page=pdf[index]
        actual=[s for b in page.get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] for s in l['spans']
                if s['text'].strip()==expected and s['bbox'][1]>page.rect.height-55]
        assert len(actual)==1 and abs(actual[0]['size']-9)<.05,(title,actual)
        page_spans.append({'pdf_page':index+1,'abstract_page':expected,'size':actual[0]['size'],'actual_font':actual[0]['font']})
    for i in range(start-1,len(pdf)):
        page=pdf[i];expected=str(i-start+2)
        actual=[s for b in page.get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] for s in l['spans']
                if s['text'].strip()==expected and s['bbox'][1]>page.rect.height-55]
        assert len(actual)==1 and abs(actual[0]['size']-9)<.05,(i+1,actual)
        page_spans.append({'pdf_page':i+1,'body_page':expected,'size':actual[0]['size'],'actual_font':actual[0]['font']})
    original_pdf=all(any(k in n for n in names) for k in ['SimSun','SimHei','TimesNewRoman'])
    if os.environ.get('THESIS_ALLOW_SUBSTITUTE_PREVIEW')!='1':
        assert original_pdf,('Original PDF fonts not verified',names)
    result={'source_sha_unchanged':sha(ROOT/'docs/thesis/毕业论文.md')==baseline['docs/thesis/毕业论文.md'],
            'protected_files_checked':len(protected),'protected_changes':changed,
            'cover_title':'18pt, bold, centred; East Asian SimHei / Latin Times New Roman',
            'style_checks':style_checks,'heading_paragraphs_checked':len(heading_checks),
            'source_code_lines_checked':len(code_paragraphs),
            'indexed_items':item_counts,
            'ordinary_paragraphs_checked':checked,'footer_parts_checked':footers,
            'pdf_pages':len(pdf),'actual_pdf_fonts':names,'times_new_roman_used_spans':len(tnr_spans),
            'school_header_pages_checked':len(header_checks),'school_headers':header_checks,
            'original_pdf_fonts_verified':original_pdf,'microsoft_word_verified':False,
            'pdf_page_number_spans':page_spans,'raster_figure_fonts_revalidated':False,
            'raster_figure_limit':'Twenty diagrams are re-rendered from complete vector geometry with safe padding; screenshot evidence remains unchanged. DOCX run fonts do not certify raster-image typography.'}
    (RUN/'font-layout-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'style_checks','pdf_page_number_spans','school_headers'}},ensure_ascii=False))

if __name__=='__main__':main()
