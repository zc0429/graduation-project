"""Verify real raster edges, DOCX embedding and PDF table/image layout."""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import argparse,hashlib,json,os,re,math
from lxml import etree as E
from PIL import Image,ImageChops
from docx import Document
import fitz
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/thesis/border-polish-20261114/figures'
RUN=ROOT/'docs/validation'/os.environ.get('THESIS_DELIVERY_ID','thesis-border-polish-20261114')
NS='http://www.w3.org/2000/svg'
def norm(s):return re.sub(r'[\s\u200b\u00ad]+','',s)
def pixels(im):return hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
def margins(im):
    im=im.convert('RGB');b=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox()
    assert b,'Blank image';return [b[0],b[1],im.width-b[2],im.height-b[3]]
def line_coverage(im,x0,y0,x1,y1,tol=4):
    p=im.convert('L').load();width,height=im.size;n=max(2,math.ceil(max(abs(x1-x0),abs(y1-y0))/4));hit=0
    for i in range(n+1):
        x=round(x0+(x1-x0)*i/n);y=round(y0+(y1-y0)*i/n)
        ray=[(x+t,y) for t in range(-tol,tol+1)] if abs(y1-y0)>abs(x1-x0) else [(x,y+t) for t in range(-tol,tol+1)]
        hit+=any(0<=a<width and 0<=b<height and p[a,b]<190 for a,b in ray)
    return hit/(n+1)
def rectangle_edges(im,r,vb,scale):
    x=(r['x']-vb[0])*scale;y=(r['y']-vb[1])*scale;w=r['w']*scale;h=r['h']*scale
    return [line_coverage(im,*coords) for coords in [(x+5,y,x+w-5,y),(x+w,y+5,x+w,y+h-5),(x+w-5,y+h,x+5,y+h),(x,y+h-5,x,y+5)]]
def inspect_figures():
    manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'));result=[]
    for target,m in manifest.items():
        png=BASE/m['file'];svg=png.with_suffix('.svg');im=Image.open(png).convert('RGB');vb=m['viewBox'];scale=m['raster_scale']
        assert hashlib.sha256(png.read_bytes()).hexdigest()==m['png_sha256']
        assert hashlib.sha256(svg.read_bytes()).hexdigest()==m['svg_sha256']
        assert hashlib.sha256((ROOT/m['source']).read_bytes()).hexdigest()==m['source_sha256']
        pad=margins(im);assert min(pad)>=80 and max(pad)<=128,(m['number'],pad)
        tree=E.fromstring(svg.read_bytes());rect_checks=[]
        for r in tree.iter('{'+NS+'}rect'):
            if r.get('stroke') in {None,'none'}:continue
            if float(r.get('rx','0')) or float(r.get('ry','0')):continue
            box={key:float(r.get(key)) for key in ['x','y','width','height']};dx=dy=0
            for a in r.iterancestors():
                t=re.fullmatch(r'translate\(([\d.-]+),([\d.-]+)\)',a.get('transform',''))
                if t:dx+=float(t[1]);dy+=float(t[2])
            geo={'x':box['x']+dx,'y':box['y']+dy,'w':box['width'],'h':box['height']}
            values=rectangle_edges(im,geo,vb,scale);assert min(values)>=.97,(m['number'],geo,values)
            rect_checks.append({'box':geo,'coverage_top_right_bottom_left':values})
        frame_check=None
        if m['closed_outer_frame']:
            f=m['closed_outer_frame'];assert f['stroke_width']>=1.5
            frame_check=rectangle_edges(im,f,vb,scale);assert min(frame_check)>.995,(m['number'],frame_check)
        if m['number']=='6.5':
            heads=tree.xpath('//*[@data-role="realization-triangle"]');shafts=tree.xpath('//*[@data-role="realization-shaft"]');joins=tree.xpath('//*[@data-role="realization-base-join"]');assert len(heads)==len(shafts)==len(joins)==1
            for head,shaft,join in zip(heads,shafts,joins):
                def pts(x):return [tuple(map(float,p.split(','))) for p in x.get('points').split()]
                tip,a,b=pts(head);base=((a[0]+b[0])/2,(a[1]+b[1])/2)
                assert math.dist(pts(shaft)[-1],base)<.001 and math.dist(pts(join)[-1],base)<.001
                assert abs(tip[1]-184)<.001 and 238<=tip[0]<=438
                assert pts(shaft)[0] == (337,224) and tip == (337,184), 'Client must connect to LlmClient'
            assert '«interface» LlmClient' in m['text_content'] and not any('<<<<' in t for t in m['text_content'])
        if m['number']=='5.6':assert '每日 08:00 扫描' in m['text_content']
        result.append({'number':m['number'],'target':target,'margins_px':pad,'rectangles':rect_checks,'outer_frame_coverage':frame_check,'pixel_sha256':pixels(im)})
    assert len(result)==20
    return manifest,result

def embedded_figures(doc):
    result={};pending=None
    for p in doc.paragraphs:
        blips=p._p.xpath('.//*[local-name()="blip"]')
        if blips:
            pending=(doc.part.related_parts[blips[0].get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')].blob,p)
        elif pending:
            m=re.match(r'^图\s*(\d+\.\d+)',p.text)
            if m:result[m[1]]=pending
            pending=None
    return result

def check_delivery(manifest,figure_checks):
    ident=os.environ['THESIS_DELIVERY_ID'];out=ROOT/'output/thesis'/ident
    pdfname='毕业论文-字体受限预览.pdf' if os.environ.get('THESIS_ALLOW_SUBSTITUTE_PREVIEW')=='1' else '毕业论文.pdf'
    doc=Document(out/'毕业论文.docx');pdf=fitz.open(out/pdfname)
    embedded=embedded_figures(doc);page_map=json.loads((RUN/'page-map.json').read_text(encoding='utf-8'));start=next(p for _,t,p in pdf.get_toc() if norm(t)=='1绪论')
    checked=[]
    for target,m in manifest.items():
        number=m['number'];blob,p=embedded[number];im=Image.open(BytesIO(blob)).convert('RGB');expected=Image.open(BASE/m['file']).convert('RGB')
        assert im.size==expected.size and pixels(im)==pixels(expected),('DOCX resized or cropped figure',number)
        assert not p._p.xpath('.//*[local-name()="srcRect"]'),('DOCX source crop',number)
        page=int(page_map['fig'+number.replace('.','_')])+start-1;pg=pdf[page-1]
        candidates=[x for x in pg.get_image_info(xrefs=True) if x['bbox'][1]>70 and abs(x['width']/x['height']-im.width/im.height)<.006]
        assert candidates,('PDF image missing',number,page)
        item=min(candidates,key=lambda x:abs(x['width']/x['height']-im.width/im.height));pix=fitz.Pixmap(pdf,item['xref'])
        if pix.colorspace.name!='DeviceRGB':pix=fitz.Pixmap(fitz.csRGB,pix)
        if pix.alpha:pix=fitz.Pixmap(pix,0)
        actual=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);pad=margins(actual)
        assert min(pad)>=12,('PDF removed safe padding',number,pad)
        r=fitz.Rect(item['bbox']);assert r.x0>=0 and r.x1<=pg.rect.width and r.y0>=70 and r.y1<=pg.rect.height-70,(number,list(r))
        checked.append({'number':number,'pdf_page':page,'body_page':page-start+1,'docx_pixels_exact':True,'pdf_image_size':[pix.width,pix.height],'pdf_white_margins_px':pad,'pdf_bbox':list(r)})
    chunks=json.loads((RUN/'table-chunks.json').read_text(encoding='utf-8'))
    def table_page(prefix):
        cap=next(c['caption'] for c in chunks if c['caption'].startswith(prefix));text=norm(cap)
        return next(i for i,p in enumerate(pdf) if i+1>=start and text in norm(p.get_text()))
    interface_pages=[i for i,p in enumerate(pdf) if i+1>=start and norm('表 6.13 系统接口一览') in norm(p.get_text())]
    def table_left(page):
        lines=[d['rect'].x0 for d in page.get_drawings() if 72<d['rect'].y0<page.rect.height-70 and abs(d['rect'].height)<.5 and abs(d['rect'].width-446.4567)<1]
        assert lines,('Table border geometry not found',page.number+1)
        return sorted(lines)[len(lines)//2]
    deletes=[]
    for i in interface_pages:
        method_left=table_left(pdf[i])+1.9*28.3464567;method_right=method_left+2.2*28.3464567
        for word in pdf[i].get_text('words'):
            if word[4]=='DELETE':
                assert method_left+1<=word[0] and word[2]<=method_right-1,('DELETE exceeds method cell',i+1,word)
                deletes.append({'page':i+1,'bbox':list(word[:4]),'text':word[4]})
        assert not re.search(r'\bDELET\s+E\b',pdf[i].get_text()),('Broken DELETE',i+1)
    assert len(deletes)==3,('DELETE single-line count',deletes)
    qpage=table_page('表 6.4');stamp=[];left=table_left(pdf[qpage])+(3.0+3.0)*28.3464567;right=left+5.6*28.3464567
    for word in pdf[qpage].get_text('words'):
        if word[4]=='CURRENT_TIMESTAMP':
            assert left+1<=word[0] and word[2]<=right-1,('Timestamp exceeds constraint cell',word)
            stamp.append(list(word[:4]))
    assert len(stamp)>=3,('Incomplete timestamp tokens',len(stamp))
    trace=pdf[table_page('表 8.7')].get_text();compact=norm(trace)
    for phrase in ['/auth/register、/auth/login','/subject/list、/subject','/question、/question/page']:assert phrase in compact,('Missing ideographic separator',phrase)
    apages=[i for i,p in enumerate(pdf) if i+1>=start and norm('表 A.2 核心代码位置索引') in norm(p.get_text())]
    files=[]
    for i in apages:
        for word in pdf[i].get_text('words'):
            if 'components/LearningResources.vue' in word[4]:files.append({'pdf_page':i+1,'word':word[4],'bbox':list(word[:4])})
        assert not re.search(r'LearningResources\.vu\s+e\b',pdf[i].get_text()),('Broken .vue filename',i+1)
    assert files,('Complete LearningResources.vue not found')
    refstart=next(p for _,t,p in pdf.get_toc() if norm(t)=='参考文献');refend=next(p for _,t,p in pdf.get_toc() if norm(t)=='致谢');refs=norm(''.join(pdf[i].get_text() for i in range(refstart-1,refend-1)))
    for phrase in ['徐行健.在线教育','熊莎莎.基于大模型','探究型高职教育——以Python语言课程为例']:assert phrase in refs,('Bibliographic punctuation',phrase)
    assert not re.search(r'—{3,}',refs)
    high=RUN/'affected-pages-300dpi';high.mkdir(exist_ok=True)
    selected=sorted(set([r['pdf_page'] for r in checked]+[i+1 for i in interface_pages]+[qpage+1,table_page('表 8.7')+1]+[i+1 for i in apages]+list(range(refstart,refend))))
    for number in selected:pdf[number-1].get_pixmap(dpi=300,alpha=False).save(high/f'page-{number:03}.png')
    return {'pdf_file':pdfname,'font_limited_preview':os.environ.get('THESIS_ALLOW_SUBSTITUTE_PREVIEW')=='1','high_resolution_pdf_pages':selected,'high_resolution_dpi':300,'figures':checked,'delete_tokens' :deletes,'complete_timestamp_tokens':stamp,'trace_punctuation_verified':True,'complete_vue_filenames':files,'bibliography_punctuation_verified':True,'all_checks_passed':True,'microsoft_word_verified':False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--figures-only',action='store_true');args=parser.parse_args();RUN.mkdir(parents=True,exist_ok=True)
    manifest,checks=inspect_figures();result={'raster_geometry':checks,'figure_count':len(checks),'svg_padding_units':24,'raster_scale':4,'geometry_checks_passed':True}
    if not args.figures_only:result.update(check_delivery(manifest,checks))
    (RUN/'border-polish-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'figure_count':20,'rectangle_shapes_checked':sum(len(x['rectangles']) for x in checks),'closed_frames':3,'minimum_native_white_margin_px':min(min(x['margins_px']) for x in checks),'delivery_checked':not args.figures_only,'passed':True},ensure_ascii=False))
if __name__=='__main__':main()
