"""Build the editable review from the retained 2027 school template.

Preserves untouched package parts byte-for-byte. Field cache can be rebuilt from
an independently checked page-map.json; never round-trips the DOCX through LO.
"""
from pathlib import Path
from copy import deepcopy
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import re,json,hashlib
from lxml import etree
from docx import Document
from docx.shared import Pt,Cm,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_BREAK,WD_TAB_ALIGNMENT,WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image,ImageOps

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'docs/validation/learning-delivery-20261112'
OUT=ROOT/'output/thesis/learning-delivery-20261112/毕业论文.docx'
TPL=next((ROOT/'docs/materials/27届毕业设计学校通知和模板').rglob('*正文模板.docx'))
BOOKMARK_ID=100

# OOXML property containers are ordered sequences, not unordered attributes.
PROPERTY_ORDER={
 'tblBorders':'top start left bottom end right insideH insideV',
 'tcBorders':'top start left bottom end right insideH insideV tl2br tr2bl',
 'tcMar':'top start left bottom end right',
 'pPr':'pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection textAlignment textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange',
 'tblPr':'tblStyle tblpPr tblOverlap bidiVisual tblStyleRowBandSize tblStyleColBandSize tblW jc tblCellSpacing tblInd tblBorders shd tblLayout tblCellMar tblLook tblCaption tblDescription tblPrChange',
 'tcPr':'cnfStyle tcW gridSpan hMerge vMerge tcBorders shd noWrap tcMar textDirection tcFitText vAlign hideMark headers cellIns cellDel cellMerge tcPrChange',
 'sectPr':'headerReference footerReference footnotePr endnotePr type pgSz pgMar paperSrc pgBorders lnNumType pgNumType cols formProt vAlign noEndnote titlePg textDirection bidi rtlGutter docGrid printerSettings sectPrChange',
}

def normalize_properties(tree):
    for container in tree.iter():
        name=etree.QName(container).localname
        if name not in PROPERTY_ORDER:continue
        order=PROPERTY_ORDER[name].split();rank={v:i for i,v in enumerate(order)}
        children=list(container)
        # Reapplying paragraph formatting must update, not duplicate, properties.
        for child in children:
            if any(other.tag==child.tag for other in children[children.index(child)+1:]) and name!='sectPr':
                container.remove(child)
        container[:]=sorted(list(container),key=lambda x:rank.get(etree.QName(x).localname,999))
def el(tag,**attrs):
    x=OxmlElement('w:'+tag)
    for k,v in attrs.items():x.set(qn('w:'+k),str(v))
    return x
def font(r,size=12,east='宋体',bold=False):
    r.font.name='Times New Roman'; r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=RGBColor(0,0,0)
    f=r._r.get_or_add_rPr().get_or_add_rFonts();f.set(qn('w:eastAsia'),east)
    return r
def field(p,instruction,cached,size=12):
    p.add_run()._r.append(el('fldChar',fldCharType='begin'))
    x=el('instrText');x.set(qn('xml:space'),'preserve');x.text=' '+instruction+' ';p.add_run()._r.append(x)
    p.add_run()._r.append(el('fldChar',fldCharType='separate'))
    font(p.add_run(str(cached)),size)
    p.add_run()._r.append(el('fldChar',fldCharType='end'))
def bookmark_start(p,name):
    global BOOKMARK_ID
    BOOKMARK_ID+=1;p._p.append(el('bookmarkStart',id=BOOKMARK_ID,name=name));return BOOKMARK_ID
def bookmark_end(p,n):p._p.append(el('bookmarkEnd',id=n))
def plain(s):return re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',s).replace('**','').replace('`','')
def inline(p,s,size=12,refs=True):
    s=plain(s)
    pattern=r'(\[\d+\]|[图表]\s*\d+\.\d+)'
    for part in re.split(pattern,s):
        if re.fullmatch(r'\[\d+\]',part) and refs:
            link=el('hyperlink',anchor='ref'+part[1:-1],history=1)
            r=font(p.add_run(part),size);r.font.superscript=True;link.append(r._r);p._p.append(link)
        elif re.fullmatch(r'[图表]\s*\d+\.\d+',part):
            kind=part[0];n=re.search(r'\d+\.\d+',part)[0];key=('fig' if kind=='图' else 'tab')+n.replace('.','_')
            field(p,f'REF {key} \\h',f'{kind} {n}',size)
        elif part:font(p.add_run(part),size)
def fmt(p,size=12,indent=24,align=WD_ALIGN_PARAGRAPH.JUSTIFY,line=20,before=0,after=0,keep=False):
    f=p.paragraph_format;f.first_line_indent=Pt(indent);f.left_indent=Pt(0);f.right_indent=Pt(0)
    f.line_spacing=Pt(line);f.space_before=Pt(before);f.space_after=Pt(after);f.keep_with_next=keep;f.widow_control=True
    p.alignment=align
    p._p.get_or_add_pPr().append(el('snapToGrid',val=0))
    return p
def section_end(doc,base,header=None,footer=None,number=None):
    s=deepcopy(base)
    for tag in ['headerReference','footerReference','pgNumType','type','titlePg']:
        for x in s.findall(qn('w:'+tag)):s.remove(x)
    if header:
        x=el('headerReference',type='default');x.set(qn('r:id'),header);s.insert(0,x)
    if footer:
        x=el('footerReference',type='default');x.set(qn('r:id'),footer);s.insert(1 if header else 0,x)
    s.insert(2 if header and footer else 0,el('type',val='nextPage'))
    s.find(qn('w:pgMar')).set(qn('w:footer'),'851')
    if number:s.append(el('pgNumType',fmt=number,start=1))
    return s
def append_sect(doc,s):
    p=doc.add_paragraph();fmt(p,indent=0,line=1);p._p.get_or_add_pPr().append(s)
def heading(doc,text,level=1,key=None,pagebreak=False):
    # Ctrl+Enter semantics: a real w:br w:type="page", not blank paragraphs.
    if pagebreak:
        doc.paragraphs[-1].add_run().add_break(WD_BREAK.PAGE)
    p=doc.add_paragraph(style=f'Heading {min(level,3)}')
    template=Document(TPL).paragraphs[101 if level==1 else 86 if level==2 else 87]
    current=p._p.get_or_add_pPr();p._p.remove(current);p._p.insert(0,deepcopy(template._p.pPr))
    p.style=f'Heading {min(level,3)}'
    p.paragraph_format.page_break_before=False
    p.paragraph_format.keep_with_next=True
    if key:k=bookmark_start(p,key)
    font(p.add_run(text),14 if level==1 else 12,'黑体')
    if text=='参考文献':
        p.paragraph_format.space_before=Pt(6);p.paragraph_format.space_after=Pt(0)
    if key:bookmark_end(p,k)
    return p
def caption(doc,text,continued=False):
    m=re.match(r'([图表])\s*(\d+)\.(\d+)\s*(.*)',text);kind,ch,n,title=m.groups()
    p=doc.add_paragraph(style='Caption');fmt(p,size=10.5,indent=0,align=WD_ALIGN_PARAGRAPH.CENTER,line=13,
        before=12 if kind=='表' else 6,after=6 if kind=='表' else 12,keep=kind=='表')
    name=('fig' if kind=='图' else 'tab')+ch+'_'+n
    if not continued:k=bookmark_start(p,name)
    font(p.add_run(('续' if continued else '')+kind+' '+ch+'.'),10.5)
    if continued:font(p.add_run(n),10.5)
    else:field(p,f'SEQ {"Figure" if kind=="图" else "Table"}{ch} \\* ARABIC'+(' \\r 1' if n=='1' else ''),n,10.5)
    if not continued:bookmark_end(p,k)
    font(p.add_run('　'+title),10.5)
    return p
def table(doc,rows,cap):
    n=len(rows[0]);widths=([3.0,3.0,4.75,5.0] if n==4 and '字段' in rows[0][0] else
        [2.2,6.2,7.35] if n==3 and '接口' in cap else
        [3,4.0,5.0,3.75] if n==4 else [3.7,6,6.05] if n==3 else [15.75/n]*n)
    if '6.12' in cap:widths=[2.2,1.8,6.6,5.15]
    if '3.1' in cap:widths=[1.5,3.0,8.0,3.25]
    t=doc.add_table(rows=1,cols=n);t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    for c,w in zip(t.columns,widths):c.width=Cm(w)
    pr=t._tbl.tblPr
    for old in list(pr):
        if old.tag in [qn('w:tblBorders'),qn('w:tblStyle')]:pr.remove(old)
    borders=el('tblBorders')
    for side in ['top','bottom','left','right','insideH','insideV']:
        borders.append(el(side,val='single' if side in ['top','bottom'] else 'nil',sz=12 if side in ['top','bottom'] else 0,color='000000'))
    pr.append(borders)
    for ri,data in enumerate(rows):
        row=t.rows[0] if ri==0 else t.add_row(); row._tr.get_or_add_trPr().append(el('cantSplit'))
        if ri==0:row._tr.get_or_add_trPr().append(el('tblHeader'))
        for ci,(c,value) in enumerate(zip(row.cells,data)):
            c.width=Cm(widths[ci]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp=c._tc.get_or_add_tcPr(); margins=el('tcMar')
            for side,v in [('top',35),('bottom',35),('left',60),('right',60)]:margins.append(el(side,w=v,type='dxa'))
            cp.append(margins)
            if ri==0:
                cb=el('tcBorders');cb.append(el('bottom',val='single',sz=8,color='000000'));cp.append(cb)
            p=c.paragraphs[0];fmt(p,indent=0,align=WD_ALIGN_PARAGRAPH.CENTER if ri==0 else WD_ALIGN_PARAGRAPH.LEFT,line=13,before=3,after=3,keep=ri<len(rows)-1)
            # Allow very long identifier runs to wrap while retaining their exact visible text.
            p._p.get_or_add_pPr().append(el('wordWrap',val=0));inline(p,value,10.5,refs=False)
    return t
def main():
    assert hashlib.sha256(TPL.read_bytes()).hexdigest()=='79da5538204e7d6a9dcf9f3d4a4db297c9dc69fbbe807f493dca4ae6ed1c6c8e'
    RUN.mkdir(parents=True,exist_ok=True)
    md=(ROOT/'docs/thesis/毕业论文.md').read_text(encoding='utf-8')
    opening=(ROOT/'docs/thesis/开题报告.md').read_text(encoding='utf-8')
    references=re.findall(r'^\[(\d+)\]\s*(.+)$',md,re.M)
    assert len(references)==20 and references==re.findall(r'^\[(\d+)\]\s*(.+)$',opening,re.M), 'Thesis references must match the opening report.'
    md=re.sub(r'<!--.*?-->','',md,flags=re.S)
    pages=json.loads((RUN/'page-map.json').read_text(encoding='utf-8')) if (RUN/'page-map.json').exists() else {}
    d=Document(TPL);d.core_properties.author='赵灿';d.core_properties.title='基于智谱GLM模型的AI错题分析与学习推荐系统设计与实现';base=[deepcopy(s._sectPr) for s in d.sections]
    cover=[deepcopy(p._p) for p in d.paragraphs[:8]]
    body=d._element.body
    for x in list(body):body.remove(x)
    for x in cover:body.append(x)
    for x in list(body.iter()):
        if x.tag in {qn('w:commentRangeStart'),qn('w:commentRangeEnd'),qn('w:commentReference'),qn('w:bookmarkStart'),qn('w:bookmarkEnd')}:
            x.getparent().remove(x)
    p=d.paragraphs[6];p.clear();fmt(p,indent=0,align=WD_ALIGN_PARAGRAPH.CENTER,line=24)
    font(p.add_run(md.splitlines()[0][2:].replace('与学习推荐','\n与学习推荐')),16,'黑体',True)
    p=d.paragraphs[7];p.clear();fmt(p,indent=0,align=WD_ALIGN_PARAGRAPH.CENTER,line=19,after=20)
    font(p.add_run(re.search(r'> \*\*英文题目\*\*：(.*)',md)[1].strip()),12,'宋体',True)
    for text in ['人工智能学院　软件工程','2023级【本科】软件工程1班','赵灿　23612801026　指导教师：胡韬']:
        p=d.add_paragraph();fmt(p,indent=0,align=WD_ALIGN_PARAGRAPH.CENTER,line=20);inline(p,text)
    append_sect(d,section_end(d,base[0]))
    # Preserve all existing template styles. Only introduce missing semantic styles.
    edited_styles=[]
    for name in ['Caption','Title']:
        if name not in d.styles:
            st=d.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH);edited_styles.append(st.style_id)
    # Word rebuilds a TOC using TOC1/2/3, discarding cached direct formatting.
    # Define these styles explicitly so an update retains the checked layout.
    for level in range(1,4):
        name=f'TOC {level}'
        if name not in d.styles:d.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
        st=d.styles[name];st.base_style=d.styles['Normal'];st.next_paragraph_style=d.styles['Normal']
        st.font.name='Times New Roman';st.font.size=Pt(12);st.font.bold=False
        st.font.color.rgb=RGBColor(0,0,0)
        st.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
        f=st.paragraph_format;f.first_line_indent=Pt(0);f.left_indent=Cm((level-1)*.5)
        f.right_indent=Pt(0);f.line_spacing=1.5;f.space_before=Pt(0);f.space_after=Pt(0)
        f.keep_with_next=False;f.page_break_before=False;f.alignment=WD_ALIGN_PARAGRAPH.LEFT
        f.tab_stops.add_tab_stop(Cm(15.5),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
        st.element.get_or_add_pPr().append(el('outlineLvl',val=9))
        edited_styles.append(st.style_id)
    hp=heading(d,'目　录');hp.style='Normal'
    for r in hp.runs:font(r,14,'黑体')
    hp.paragraph_format.line_spacing=1
    entries=[('摘　要','abstract_cn',1),('Abstract','abstract_en',1)]
    for line in md.splitlines():
        m=re.match(r'^(#{2,4}) (\d+(?:\.\d+)* .+|参考文献|致　谢.*)$',line)
        if m:entries.append((m[2].replace('（预留）',''),'h'+str(len(entries)),len(m[1])-1))
    key_by_title={t:k for t,k,l in entries}
    for i,(t,key,lev) in enumerate(entries):
        p=d.add_paragraph(style=f'TOC {lev}');fmt(p,indent=0,line=20,align=WD_ALIGN_PARAGRAPH.LEFT);p.paragraph_format.line_spacing=1.5
        p.paragraph_format.left_indent=Cm((lev-1)*.5)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(15.5),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
        if i==0:
            p.add_run()._r.append(el('fldChar',fldCharType='begin'));x=el('instrText');x.text=' TOC \\o "1-3" \\h \\z \\u ';p.add_run()._r.append(x);p.add_run()._r.append(el('fldChar',fldCharType='separate'))
        link=el('hyperlink',anchor=key,history=1);r=font(p.add_run(t),14 if key in ['abstract_cn','abstract_en'] or t in ['参考文献','致　谢'] else 12,'黑体' if lev==1 else '宋体');link.append(r._r);p._p.append(link)
        font(p.add_run('\t'));field(p,f'PAGEREF {key} \\h',pages.get(key,'1'))
        if i==len(entries)-1:p.add_run()._r.append(el('fldChar',fldCharType='end'))
    append_sect(d,section_end(d,base[1],header='rId6',footer='rId7'))
    for title,key in [('摘　要','abstract_cn'),('Abstract','abstract_en')]:
        p=heading(d,title,key=key,pagebreak=key=='abstract_en')
        for r in p.runs:font(r,14,'黑体',key=='abstract_en')
        p.paragraph_format.line_spacing=1
        p.style='Normal';p._p.get_or_add_pPr().append(el('outlineLvl',val=0))
        section=md.split('## '+title+'\n')[1].split('\n## ')[0]
        for line in section.splitlines():
            if not line.strip() or line=='---':continue
            p=d.add_paragraph();fmt(p,indent=0 if line.startswith('**') else 24)
            if line.startswith('**'):
                parts=plain(line).split('：',1) if '：' in line else plain(line).split(':',1)
                font(p.add_run(('关键词：' if key=='abstract_cn' else 'Keywords: ')),14,'黑体',key=='abstract_en')
                inline(p,parts[-1].strip())
            else:inline(p,line)
    append_sect(d,section_end(d,base[2],header='rId6',footer='rId8',number='upperRoman'))
    lines=md[md.index('## 1 '):].splitlines();i=0;pending_caption=None;in_refs=False;body_split=False;landscape=False
    while i<len(lines):
        line=lines[i].strip();i+=1
        if not line or line=='---' or line.startswith('>'):continue
        if line.startswith('#'):
            n=len(line)-len(line.lstrip('#'));title=line[n:].strip().replace('（预留）','')
            in_refs=title=='参考文献' or (in_refs and title!='致　谢')
            heading(d,title,n-1,key_by_title.get(title),pagebreak=n==2);continue
        if line.startswith('```'):
            code=[]
            while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
            i+=1
            for text in code:
                p=d.add_paragraph();fmt(p,indent=0,line=14);font(p.add_run(text),10.5)
            continue
        if line.startswith('!['):
            target=re.search(r'\]\(([^)]+)\)',line)[1];path=ROOT/'docs/thesis'/target
            im=Image.open(path).convert('RGB');w,h=im.size
            landscape='business-flow/' in target
            if landscape:
                append_sect(d,section_end(d,base[3],header='rId6',footer='rId9',number='decimal' if not body_split else None));body_split=True
                box=ImageOps.invert(im.convert('L')).point(lambda x: 255 if x>30 else 0).getbbox()
                im=im.crop(box);w,h=im.size;buf=BytesIO();im.save(buf,format='PNG');buf.seek(0)
                width=min(24.45,14.6*w/h);picture=buf
            else:
                width=min(15.75,(23 if 'delivery-20261112/figures/3-' in target else 20)*w/h);picture=str(path)
            p=d.add_paragraph();fmt(p,indent=0,align=WD_ALIGN_PARAGRAPH.CENTER,line=14,keep=True,before=6)
            p.paragraph_format.line_spacing=1
            p.add_run().add_picture(picture,width=Cm(width));continue
        if line.startswith('**图 '):
            p=caption(d,plain(line))
            following=next((x.strip() for x in lines[i:] if x.strip()),'')
            p.paragraph_format.keep_with_next=following.startswith('资料来源')
            if landscape:
                sec=section_end(d,base[3],header='rId6',footer='rId9')
                pg=sec.find(qn('w:pgSz'));pg.set(qn('w:w'),'16838');pg.set(qn('w:h'),'11906');pg.set(qn('w:orient'),'landscape')
                append_sect(d,sec);landscape=False
            continue
        if line.startswith('**表 '):pending_caption=plain(line);continue
        if line.startswith('|'):
            rows=[line]
            while i<len(lines) and lines[i].strip().startswith('|'):rows.append(lines[i].strip());i+=1
            rows=[[x.strip() for x in r.strip('|').split('|')] for r in rows if not re.match(r'^\|\s*:?-',r)]
            if pending_caption and '6.12' in pending_caption:
                for ci,start in enumerate(range(1,len(rows),14)):
                    cap=caption(d,pending_caption,continued=ci>0)
                    cap.paragraph_format.page_break_before=True
                    table(d,[rows[0]]+rows[start:start+14],pending_caption)
            else:
                if pending_caption:caption(d,pending_caption)
                table(d,rows,pending_caption or '')
            pending_caption=None;continue
        p=d.add_paragraph();fmt(p)
        if in_refs and re.match(r'^\[\d+\]',line):
            num=re.match(r'^\[(\d+)\]',line)[1];k=bookmark_start(p,'ref'+num)
            p.paragraph_format.left_indent=Pt(0);p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=Pt(22)
            inline(p,re.sub(r'^(\[\d+\])\s+',r'\1',line),10.5,refs=False);bookmark_end(p,k)
        elif line.startswith('资料来源'):
            fmt(p,indent=0,line=13,before=6,after=12);inline(p,line,10.5,refs=False)
        else:inline(p,line)
    body.append(section_end(d,base[3],header='rId6',footer='rId9',number=None if body_split else 'decimal'))
    # Refresh is deferred to Word; cached fields are deterministic and separately QAed.
    settings=d.settings.element
    for x in settings.findall(qn('w:updateFields')):settings.remove(x)
    settings.insert_element_before(el('updateFields',val='true'),'w:hdrShapeDefaults','w:footnotePr','w:endnotePr','w:compat','w:docVars','w:rsids','w:mathPr','w:attachedSchema','w:themeFontLang','w:clrSchemeMapping','w:doNotIncludeSubdocsInStats','w:doNotAutoCompressPictures','w:forceUpgrade','w:captions','w:readModeInkLockDown','w:smartTagType','w:schemaLibrary','w:shapeDefaults','w:doNotEmbedSmartTags','w:decimalSymbol','w:listSeparator')
    normalize_properties(d._element)
    buf=BytesIO();d.save(buf);buf.seek(0)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(TPL) as orig,ZipFile(buf) as generated,ZipFile(OUT,'w',ZIP_DEFLATED) as out:
        editable={'docProps/core.xml','word/document.xml','word/settings.xml','word/_rels/document.xml.rels','[Content_Types].xml'}
        styles=etree.fromstring(orig.read('word/styles.xml'));newstyles=etree.fromstring(generated.read('word/styles.xml'))
        for sid in edited_styles:
            for x in list(styles):
                if x.get(qn('w:styleId'))==sid:styles.remove(x)
            for x in newstyles:
                if x.get(qn('w:styleId'))==sid:styles.append(deepcopy(x))
        # The retained template places uiPriority after qFormat in some styles.
        # Normalize CT_Style order in the output only; preserve all values and
        # repeated tblStylePr children (unlike singleton property containers).
        style_order='name aliases basedOn next link autoRedefine hidden uiPriority semiHidden unhideWhenUsed qFormat locked personal personalCompose personalReply rsid pPr rPr tblPr trPr tcPr tblStylePr'.split()
        style_rank={name:i for i,name in enumerate(style_order)}
        for style in styles.findall(qn('w:style')):
            style[:]=sorted(style,key=lambda x:style_rank.get(etree.QName(x).localname,999))
        for name in orig.namelist():
            data=generated.read(name) if name in editable else orig.read(name)
            if name=='word/styles.xml':data=etree.tostring(styles,xml_declaration=True,encoding='UTF-8',standalone=True)
            if re.match(r'word/footer\d+.xml',name):
                tree=etree.fromstring(data)
                for pp in tree.iter(qn('w:pPr')):
                    for x in list(pp):
                        if x.tag in [qn('w:jc'),qn('w:ind')]:pp.remove(x)
                    pp.append(el('jc',val='center'))
                normalize_properties(tree)
                data=etree.tostring(tree,xml_declaration=True,encoding='UTF-8',standalone=True)
            if name.startswith('word/comments') or name in ['word/footnotes.xml','word/endnotes.xml']:
                tree=etree.fromstring(data)
                for x in list(tree):
                    if x.get(qn('w:id')) not in ['-1','0']:tree.remove(x)
                data=etree.tostring(tree,xml_declaration=True,encoding='UTF-8',standalone=True)
            out.writestr(name,data)
        for name in generated.namelist():
            if name not in orig.namelist():out.writestr(name,generated.read(name))
    (RUN/'heading-keys.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
    print(OUT)
if __name__=='__main__':main()
