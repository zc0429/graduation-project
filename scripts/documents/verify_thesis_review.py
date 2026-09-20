"""Read-only content/package checks; writes audit records, never claims visual/native QA."""
from pathlib import Path
from zipfile import ZipFile
import json,re,sys,tempfile,hashlib,difflib,subprocess,contextlib,io
from lxml import etree
import fitz

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'docs/notes/thesis-run-20260920'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
ns={'w':W}
def write(name,value):
    (RUN/name).write_text(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    md=(ROOT/'docs/thesis/毕业论文.md').read_text(encoding='utf-8')
    old=subprocess.check_output(['git','show','3b7fc4768e4a2588583f109133d378a050da8733:docs/thesis/毕业论文.md'],cwd=ROOT).decode('utf-8')
    write('CHAPTER2-AFTER.md',md[md.index('## 2 文献综述'):md.index('## 3 系统分析')])
    write('THESIS-CHANGES.diff',''.join(difflib.unified_diff(old.splitlines(True),md.splitlines(True),fromfile='baseline/毕业论文.md',tofile='review/毕业论文.md')))
    stats={}
    for i in range(1,8):
        section=re.search(r'^## '+str(i)+r' .*?(?=^## |\Z)',md,re.S|re.M)[0]
        clean=re.sub(r'!\[[^]]*\]\([^)]+\)','',section)
        clean=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',clean)
        clean=re.sub(r'\[\d+\]|[#*`|]','',clean)
        stats[str(i)]={'chinese':len(re.findall(r'[\u4e00-\u9fff]',clean)),'nonspace':len(re.sub(r'\s','',clean))}
    stats['total_chinese']=sum(v['chinese'] for v in stats.values())
    stats['body_3_to_6_chinese']=sum(stats[str(i)]['chinese'] for i in range(3,7))
    write('word-count.json',stats)
    a=(RUN/'REFERENCE-AUDIT.md').read_text(encoding='utf-8')
    a=re.sub(r'综述汉字数\d+，去空白字符数\d+',f"综述汉字数{stats['2']['chinese']}，去空白字符数{stats['2']['nonspace']}",a)
    write('REFERENCE-AUDIT.md',a)
    seen=list(dict.fromkeys(re.findall(r'\[(\d+)\]',md.split('## 参考文献')[0])))
    assert seen==[str(i) for i in range(1,25)]
    docx=ROOT/'output/docx/论文审阅版.docx';pdf=ROOT/'output/pdf/论文审阅版.pdf'
    template=next((ROOT/'docs/materials/27届毕业设计学校通知和模板').rglob('*正文模板.docx'))
    with ZipFile(docx) as z,ZipFile(template) as orig:
        assert z.testzip() is None
        tree=etree.fromstring(z.read('word/document.xml'))
        bookmarks=tree.xpath('//w:bookmarkStart/@w:name',namespaces=ns)
        assert len(bookmarks)==len(set(bookmarks))
        anchors=tree.xpath('//w:hyperlink/@w:anchor',namespaces=ns)
        assert not(set(anchors)-set(bookmarks))
        fields=tree.xpath('//w:instrText/text()',namespaces=ns)
        for f in fields:
            if re.match(r'\s*(PAGE)?REF ',f):assert f.strip().split()[1] in bookmarks
        seq=[f for f in fields if f.strip().startswith('SEQ ')]
        assert len(seq)==33
        assert all('ref'+str(i) in bookmarks for i in range(1,25))
        assert len(tree.xpath('//w:tbl',namespaces=ns))==20
        assert z.read('word/header1.xml')==orig.read('word/header1.xml')
        assert z.read('docProps/core.xml')==orig.read('docProps/core.xml')
        sections=tree.xpath('//w:sectPr',namespaces=ns);assert len(sections)==4
        for s in sections:
            m=s.find('w:pgMar',ns)
            assert [int(m.get('{'+W+'}'+x)) for x in ['left','right','top','bottom','header','footer']]==[1559,1417,1417,1417,851,851]
        docx_stats={'seq':len(seq),'ref':sum(f.strip().startswith('REF ') for f in fields),'pageref':sum(f.strip().startswith('PAGEREF ') for f in fields),'reference_links':sum(a.startswith('ref') for a in anchors),'bookmarks':len(bookmarks),'physical_tables':20,'semantic_tables':16,'sections':4,'template_header_unchanged':True,'template_core_metadata_unchanged':True}
        # The bundled validator's sole environment failure was a remote Dublin Core
        # XSD import for byte-identical template metadata. Exclude that one part
        # explicitly, retain all other package/reference/schema checks.
        validator_dir=Path('C:/Users/can/.agents/skills/docx/scripts/office')
        sys.path.insert(0,str(validator_dir))
        from validators import DOCXSchemaValidator
        with tempfile.TemporaryDirectory() as tmp:
            z.extractall(tmp)
            v=DOCXSchemaValidator(Path(tmp),template,verbose=True)
            v.xml_files=[p for p in v.xml_files if p.relative_to(Path(tmp)).as_posix()!='docProps/core.xml']
            log=io.StringIO()
            with contextlib.redirect_stdout(log):ok=v.validate()
            write('DOCX-STRUCTURE-CHECK.txt','Scope: all package checks except byte-identical docProps/core.xml (remote Dublin Core schema unavailable).\n'+log.getvalue())
            assert ok,log.getvalue()
    p=fitz.open(pdf);assert len(p)==61
    outliers=[];badlinks=[];citation_links=0
    for n,page in enumerate(p,1):
        assert abs(page.rect.width-595.276)<1 and abs(page.rect.height-841.89)<1
        assert '\ufffd' not in page.get_text()
        assert not any(x in page.get_text() for x in ['Error! Reference','错误!未找到','<!--','-->' ])
        for word in page.get_text('words'):
            if not page.rect.contains(fitz.Rect(word[:4])):outliers.append([n,word[4]])
        for link in page.get_links():
            if link['kind']==fitz.LINK_GOTO:
                if not 0<=link['page']<len(p):badlinks.append(n)
                source=page.get_textbox(link['from']+(-1,-2,1,2)).strip()
                matched=re.search(r'\[\d+\]',source)
                if matched and n>3 and link['page'] in (58,59):
                    source=matched[0]
                    target=p[link['page']];to=link['to']
                    around=target.get_textbox(fitz.Rect(0,max(0,to.y-3),target.rect.width,min(target.rect.height,to.y+27)))
                    assert source in around,(n,source,link['page'],around)
                    citation_links+=1
    assert not outliers and not badlinks
    keys=json.loads((RUN/'heading-keys.json').read_text(encoding='utf-8'))
    expected=json.loads((RUN/'page-map.json').read_text(encoding='utf-8'))
    toc=p.get_toc();actual={}
    for title,key,lev in keys:
        rows=[r for r in toc if re.sub(r'\s','',r[1])==re.sub(r'\s','',title)]
        assert len(rows)==1,(title,rows)
        page=rows[0][2];actual[key]='I' if key=='abstract_cn' else 'II' if key=='abstract_en' else str(page-5)
    assert actual=={k:str(v) for k,v in expected.items()},(actual,expected)
    assert citation_links==docx_stats['reference_links']
    protected=['server','web','docs/materials','docs/references','docs/experiments','docs/validation','docs/thesis/开题报告.md','docs/thesis/开题报告-系统填报版.md','docs/thesis/figures']
    assert not subprocess.check_output(['git','diff','3b7fc4768e4a2588583f109133d378a050da8733','--',*protected],cwd=ROOT)
    report={'date':'2026-09-21 Asia/Shanghai','docx_sha256':sha(docx),'pdf_sha256':sha(pdf),'docx':docx_stats,'pdf_pages':len(p),'a4':True,'glyph_outliers':outliers,'invalid_internal_links':badlinks,'citation_destinations_verified':citation_links,'toc_pages_checked':len(actual),'protected_baseline_paths_unchanged':protected,'word_counts':stats,'native_word_update':'not performed','visual_review':'separate manual record in DOCUMENT-QA.md'}
    write('document-check.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
