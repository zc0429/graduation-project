"""Build PR #1 review diagrams only; leave accepted thesis assets/evidence intact.

python scripts/documents/build_business_flow_review.py
python scripts/documents/build_business_flow_review.py --export --drawio /path/to/drawio
The Python scene definitions are the editable generation source. Native draw.io
exports supply SVG/PDF; PNGs are 300 dpi renders of the final A4 PDFs.
"""
from pathlib import Path
import argparse, base64, hashlib, io, itertools, json, math, os, subprocess, tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/thesis/business-flow/review-20261111'
SCALE = 1169 / 1600
INSET = .94
def sx(x): return ((x-800)*INSET+800)*SCALE
def sy(y): return (y*INSET+20)*SCALE
FONT = 'Noto Serif CJK SC'
SCENES = []

def scene(slug, title, lanes, notes):
    s = dict(slug=slug, title=title, lanes=lanes, notes=notes, nodes=[], edges=[])
    SCENES.append(s)
    return s

def node(s, key, x, y, text, w=330, h=60, kind='process', lane=0):
    n = dict(id=key, x=x-w/2, y=y, w=w, h=h, text=text, kind=kind, lane=lane)
    s['nodes'].append(n)
    return n

def port(n, side):
    return {'t':(n['x']+n['w']/2,n['y']), 'b':(n['x']+n['w']/2,n['y']+n['h']),
            'l':(n['x'],n['y']+n['h']/2),'r':(n['x']+n['w'],n['y']+n['h']/2)}[side]

def edge(s, a, b, start='b', end='t', bends=(), label='', labelpos=None):
    s['edges'].append(dict(id='e'+str(len(s['edges'])), source=a['id'], target=b['id'],
        start=start, end=end, points=[port(a,start),*bends,port(b,end)], label=label, labelpos=labelpos))

lanes=[('学生',60,500),('学习平台',560,520),('AI模型',1080,460)]
s=scene('01-错题录入与AI分析','图3.2  错题录入与AI分析业务流程图',lanes, [])
a=node(s,'start',310,155,'开始',160,36,'terminal')
b=node(s,'input',310,225,'录入并提交错题\n手工填写／图片辅助',330,62)
c=node(s,'operation',310,345,'本次操作？',280,86,'decision')
d=node(s,'image_request',820,358,'校验图片\n准备识别请求',330,60,lane=1)
e=node(s,'recognize',1310,358,'识别图片内容\n返回候选题目信息',330,60,lane=2)
f=node(s,'candidate',820,480,'处理候选并回填\n识别失败则提示手录',360,62,lane=1)
g=node(s,'save',820,590,'校验并保存错题\n创建复习计划',330,60,lane=1)
h=node(s,'saved',820,685,'保存成功？',280,80,'decision',1)
i=node(s,'correct',310,695,'根据提示修改输入',330,60)
j=node(s,'analysis_request',820,805,'检索本人参考题\n准备上下文并发起解析',360,60,lane=1)
k=node(s,'analyze',1310,805,'归类知识点\n分析错因与解题思路',330,60,lane=2)
l=node(s,'result',820,910,'校验、保存分析结果\n或记录／返回失败信息',360,60,lane=1)
m=node(s,'view',310,910,'查看知识点与解析\n或失败提示',330,60)
z=node(s,'end',310,1000,'结束',160,36,'terminal')
edge(s,a,b);edge(s,b,c)
edge(s,c,d,'r','l',label='图片辅助',labelpos=(510,365));edge(s,d,e,'r','l')
edge(s,e,f,'b','t',[(1310,450),(820,450)])
edge(s,d,f,'b','l',[(820,435),(605,435),(605,511)],'不可识别',(675,465))
edge(s,f,b,'r','r',[(1510,511),(1510,205),(520,205),(520,256)])
edge(s,c,g,'b','l',[(310,620)],'提交题目',(360,598))
edge(s,g,h)
edge(s,h,i,'l','r',label='否',labelpos=(580,710))
edge(s,i,b,'l','l',[(95,725),(95,256)])
edge(s,h,j,label='是',labelpos=(860,785))
edge(s,j,k,'r','l');edge(s,k,l,'b','r',[(1310,940)])
edge(s,j,l,label='未启动／失败',labelpos=(925,887))
edge(s,l,m,'l','r')
edge(s,m,j,'t','l',[(310,835)],'重试解析',(480,819))
edge(s,m,z)

s=scene('02-学习练习与复习','图3.3  知识学习、练习与复习业务流程图',lanes, [])
a=node(s,'start',310,148,'开始',160,36,'terminal')
b=node(s,'select',310,207,'选择错题／知识点\n或待复习任务',330,58)
c=node(s,'mode',310,296,'本次需要？',280,80,'decision')
d=node(s,'lookup_learning',820,260,'查询已有知识内容',360,54,lane=1)
e=node(s,'lookup_practice',820,350,'查询本人原题／拓展题\n拓展题优先未练',360,60,lane=1)
f=node(s,'available',820,435,'有合适资源？',280,80,'decision',1)
g=node(s,'generate',1310,445,'按所选类型生成\n知识讲解／变式题',330,60,lane=2)
h=node(s,'valid',820,550,'结果可用？',280,80,'decision',1)
i=node(s,'store',820,655,'校验后保存生成内容\n关联知识点／原题',360,60,lane=1)
j=node(s,'type',310,655,'所选内容类型？',300,80,'decision')
k=node(s,'learn',195,760,'阅读知识内容',190,60)
l=node(s,'practice',425,760,'作答并自行\n判定正误',190,60)
m=node(s,'record',820,760,'保存作答与题目标识\n更新掌握度',360,60,lane=1)
n=node(s,'review',310,845,'完成所选复习？',360,80,'decision')
o=node(s,'finish',820,855,'记录该复习任务完成',360,60,lane=1)
p=node(s,'again',310,950,'继续学习或练习？',330,76,'decision')
q=node(s,'failure_out',1030,567,'B',46,46,'connector',1)
qr=node(s,'failure_in',100,969,'B',38,38,'connector',0)
z=node(s,'end',310,1048,'结束',160,30,'terminal',0)
edge(s,a,b);edge(s,b,c)
edge(s,c,d,'r','l',[(585,336),(585,287)],'知识学习',(510,312))
edge(s,c,e,'b','l',[(310,400),(605,400),(605,380)],'做题练习',(470,380))
edge(s,d,f,'r','t',[(1045,287),(1045,420),(820,420)])
edge(s,e,f)
edge(s,f,g,'r','l',label='无',labelpos=(1025,453))
edge(s,g,h,'b','t',[(1310,530),(820,530)])
edge(s,h,i,label='是',labelpos=(865,643))
edge(s,h,q,'r','l',label='否',labelpos=(983,574))
# A standard paired on-page connector preserves an explicit failure path without crossing the reuse path.
s['edges'].append(dict(id='failure_link',source='failure_out',target='failure_in',semantic_only=True,points=[],label='B',labelpos=None))
edge(s,f,j,'l','t',[(620,475),(620,635),(310,635)],'有',(595,555))
edge(s,i,j,'l','r',[(585,685),(585,695)])
edge(s,j,k,'l','t',[(115,695),(115,743),(195,743)],'学习',(150,727))
edge(s,j,l,'b','t',[(310,745),(425,745)],'练习',(425,726))
edge(s,l,m,'r','l');edge(s,m,n,'b','t',[(820,833),(310,833)])
edge(s,k,n,'b','l',[(195,833),(95,833),(95,885)])
edge(s,n,o,'r','l',label='是',labelpos=(545,865))
edge(s,o,p,'b','t',[(820,935),(310,935)])
edge(s,n,p,label='否',labelpos=(270,937))
edge(s,qr,p,'r','l')
edge(s,p,b,'r','r',[(1510,988),(1510,155),(505,155),(505,236)],'是',(515,968))
edge(s,p,z,label='否',labelpos=(350,1038))
# Optional exits for no task/selection. A selected available task is required above.
edge(s,b,z,'l','l',[(75,236),(75,1063)],'退出',(110,435))

s=scene('03-管理与学情查看','图3.4  管理与学情查看业务流程图',
 [('管理员',60,500),('学习平台',560,520),('教师',1080,460)], [])
a=node(s,'start',820,165,'开始',170,40,'terminal',1)
b=node(s,'role',820,255,'当前登录角色？',320,94,'decision',1)
c=node(s,'admin',310,420,'选择管理事项\n科目／知识点、账号、公告',390,82)
d=node(s,'teacher',1310,420,'请求全站学情报告',340,62,lane=2)
e=node(s,'admin_process',820,530,'按权限处理管理请求\n查询或校验、保存变更',380,76,lane=1)
f=node(s,'teacher_process',820,705,'按权限读取当前记录\n聚合全站学情数据',380,76,lane=1)
g=node(s,'admin_result',310,705,'接收查询／操作结果\n失败时按提示处理',380,76)
h=node(s,'teacher_result',1310,865,'查看汇总报告\n或无数据／失败提示',360,76,lane=2)
z=node(s,'end',820,980,'结束',170,40,'terminal',1)
edge(s,a,b)
edge(s,b,c,'l','t',[(310,302)],'管理员',(460,280))
edge(s,b,d,'r','t',[(1310,302)],'教师',(1160,280))
edge(s,c,e,'r','t',[(590,461),(590,510),(820,510)])
edge(s,e,g,'b','r',[(820,655),(530,655),(530,743)])
edge(s,d,f,'b','r',[(1310,743)])
edge(s,f,h,'b','l',[(820,903)])
edge(s,g,z,'b','l',[(310,1000)])
edge(s,h,z,'b','r',[(1310,1000)])


def model(s):
    m=ET.Element('mxGraphModel',page='1',pageScale='1',pageWidth='1169',pageHeight='827',grid='1',gridSize='10',math='0',shadow='0',background='#ffffff')
    r=ET.SubElement(m,'root');ET.SubElement(r,'mxCell',id='0');ET.SubElement(r,'mxCell',id='1',parent='0')
    def vertex(key,text,x,y,w,h,style):
        c=ET.SubElement(r,'mxCell',id=key,value=text,style=style,vertex='1',parent='1')
        ET.SubElement(c,'mxGeometry',x=str(sx(x)),y=str(sy(y)),width=str(w*SCALE*INSET),height=str(h*SCALE*INSET),attrib={'as':'geometry'})
    common=f'html=0;whiteSpace=nowrap;fontFamily={FONT};fontColor=#000000;strokeColor=#000000;fillColor=#ffffff;strokeWidth={1.5*SCALE*INSET};align=center;verticalAlign=middle;spacing=0;'
    vertex('title',s['title'],60,40,1480,50,common+f'fontSize={28*SCALE*INSET};fontStyle=1;align=left;spacingLeft={16*SCALE*INSET};')
    for j,(title,x,w) in enumerate(s['lanes']):
        vertex(f'lane{j}',title,x,90,w,1008,common+f'shape=swimlane;horizontal=1;startSize={45*SCALE*INSET};fontSize={25*SCALE*INSET};fontStyle=1;swimlaneFillColor=#ffffff;')
    for n in s['nodes']:
        shape={'process':'rounded=0;','decision':'shape=rhombus;','terminal':'rounded=1;arcSize=90;','connector':'shape=ellipse;'}[n['kind']]
        vertex(n['id'],n['text'],n['x'],n['y'],n['w'],n['h'],common+shape+f'fontSize={24*SCALE*INSET};')
    sides={'t':(.5,0),'b':(.5,1),'l':(0,.5),'r':(1,.5)}
    for e in s['edges']:
        if e.get('semantic_only'):continue
        ex,ey=sides[e['start']];tx,ty=sides[e['end']]
        st=f'edgeStyle=none;rounded=0;html=0;endArrow=block;endFill=1;strokeColor=#000000;strokeWidth={1.7*SCALE*INSET};endSize={9*SCALE*INSET};exitX={ex};exitY={ey};entryX={tx};entryY={ty};exitPerimeter=0;entryPerimeter=0;'
        c=ET.SubElement(r,'mxCell',id=e['id'],value='',style=st,parent='1',edge='1',source=e['source'],target=e['target'])
        geom=ET.SubElement(c,'mxGeometry',relative='1',attrib={'as':'geometry'})
        if len(e['points'])>2:
            pts=ET.SubElement(geom,'Array',attrib={'as':'points'})
            for x,y in e['points'][1:-1]:ET.SubElement(pts,'mxPoint',x=str(sx(x)),y=str(sy(y)))
        if e['label']:
            x,y=e['labelpos']; w=max(32,len(e['label'])*21+10)
            vertex(e['id']+'_label',e['label'],x-w/2,y-14,w,28,common+f'strokeColor=none;fillColor=none;fontSize={21*SCALE*INSET};')
    # Notes are inside the A4 page, outside the flow frame.
    for i,line in enumerate(s['notes']):
        vertex('note'+str(i),line,60,1085+i*22,1480,21,common+f'strokeColor=none;fontSize={20*SCALE*INSET};align=left;')
    return m


def structural_checks():
    report=[]
    for s in SCENES:
        nodes={n['id']:n for n in s['nodes']};assert len(nodes)==len(s['nodes'])
        starts=[n['id'] for n in s['nodes'] if n['id']=='start'];ends=[n['id'] for n in s['nodes'] if n['id']=='end']
        assert len(starts)==len(ends)==1
        def reach(seed,reverse=False):
            seen=set();todo=[seed]
            while todo:
                k=todo.pop()
                if k in seen:continue
                seen.add(k)
                todo += [e['source' if reverse else 'target'] for e in s['edges'] if e['target' if reverse else 'source']==k]
            return seen
        assert reach('start')==set(nodes),(s['slug'],'unreachable',set(nodes)-reach('start'))
        assert reach('end',True)==set(nodes),(s['slug'],'cannot exit')
        issues=[]
        for n in nodes.values():
            lane=s['lanes'][n['lane']];assert lane[1]<=n['x'] and n['x']+n['w']<=lane[1]+lane[2],n
            assert 135<n['y'] and n['y']+n['h']<1080,n
            if n['kind']=='decision':
                out=[e for e in s['edges'] if e['source']==n['id']]
                assert len(out)==2 and all(e['label'] for e in out),(s['slug'],n['id'],'branches')
        for e in s['edges']:
            assert e['source'] in nodes and e['target'] in nodes
            if nodes[e['source']]['lane']==2 and s['slug'].startswith(('01','02')):
                assert nodes[e['target']]['lane']==1,'AI directly to student'
            for (x1,y1),(x2,y2) in zip(e['points'],e['points'][1:]):
                assert x1==x2 or y1==y2,(s['slug'],e['id'],'diagonal',(x1,y1),(x2,y2))
                assert (x1,y1)!=(x2,y2),(e['id'],'zero segment')
                for n in nodes.values():
                    if n['id'] in [e['source'],e['target']]:continue
                    left,top,right,bottom=n['x'],n['y'],n['x']+n['w'],n['y']+n['h']
                    hit=(x1==x2 and left<x1<right and max(min(y1,y2),top)<min(max(y1,y2),bottom)) or (y1==y2 and top<y1<bottom and max(min(x1,x2),left)<min(max(x1,x2),right))
                    if hit:issues.append({'edge':e['id'],'node':n['id'],'type':'through_node'})
        report.append({'page':s['slug'],'nodes':len(nodes),'edges':len(s['edges']),'one_start_one_end':True,'all_reachable_and_can_exit':True,'issues':issues})
    return report


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    checks=structural_checks()
    print(json.dumps(checks,ensure_ascii=False,indent=2))
    if any(c['issues'] for c in checks):raise ValueError('Fix geometry before export')
    mx=ET.Element('mxfile',host='app.diagrams.net',type='device',version='32.6.10')
    for i,s in enumerate(SCENES):
        d=ET.SubElement(mx,'diagram',id=str(i+1),name=s['slug']);d.append(model(s))
        one=ET.Element('mxfile',host='app.diagrams.net',type='device',version='32.6.10');one.append(d)
        ET.ElementTree(one).write(OUT/(s['slug']+'.drawio'),encoding='utf-8',xml_declaration=True)
    ET.indent(mx);ET.ElementTree(mx).write(OUT/'业务流程图-三页可编辑.drawio',encoding='utf-8',xml_declaration=True)
    (OUT/'业务流程图.json').write_text(json.dumps(SCENES,ensure_ascii=False,indent=2)+'\n')
    return checks


def embed_svg_fonts(path, s):
    from fontTools import subset
    from fontTools.ttLib import TTFont
    texts=[s['title'],*s['notes'],*[v[0] for v in s['lanes']],*[n['text'] for n in s['nodes']],*[e['label'] for e in s['edges']]]
    characters=''.join(texts)
    css=[]
    for weight,style in [(400,'Regular'),(700,'Bold')]:
        # Noto CJK collection order is JP, KR, SC, TC, HK; select SC explicitly.
        fontpath=subprocess.check_output(['fc-match','-f','%{file}',f'{FONT}:style={style}'],text=True)
        font=TTFont(fontpath,fontNumber=2)
        options=subset.Options();options.flavor='woff'
        sub=subset.Subsetter(options=options);sub.populate(text=characters);sub.subset(font)
        font.flavor='woff';buf=io.BytesIO();font.save(buf)
        data=base64.b64encode(buf.getvalue()).decode('ascii')
        css.append("@font-face{font-family:'"+FONT+"';font-style:normal;font-weight:"+str(weight)+";src:url(data:font/woff;base64,"+data+") format('woff');}")
    ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
    tree=ET.parse(path);root=tree.getroot()
    assert not root.findall('.//{*}foreignObject'), 'SVG must use portable text, not foreignObject'
    defs=root.find('{'+ns+'}defs')
    if defs is None:defs=ET.SubElement(root,'{'+ns+'}defs')
    ET.SubElement(defs,'{'+ns+'}style',type='text/css').text='\n'.join(css)
    tree.write(path,encoding='utf-8',xml_declaration=True)


def export(drawio):
    import fitz
    logs=[]
    # Native application exports, not an independent redraw of the figures.
    with tempfile.TemporaryDirectory(prefix='flow-review-') as td:
        td=Path(td)
        for s in SCENES:
            src=OUT/(s['slug']+'.drawio')
            for fmt in ['pdf','svg']:
                target=td/(s['slug']+'.'+fmt)
                cmd=[drawio,'--no-sandbox','--headless','--disable-gpu','--disable-update','--export','--theme','light','--format',fmt,'--output',str(target),str(src)]
                if fmt=='svg':cmd[cmd.index('--output'):cmd.index('--output')]=['--size','page','--embed-svg-fonts','false']
                proc=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
                logs.append({'page':s['slug'],'format':fmt,'returncode':proc.returncode,'stdout':proc.stdout.replace(str(td),'<temporary>'),'stderr':proc.stderr})
                if not target.exists() or target.stat().st_size==0:raise RuntimeError(logs[-1])
                if fmt=='svg':
                    ET.parse(target);(OUT/target.name).write_bytes(target.read_bytes());embed_svg_fonts(OUT/target.name,s)
                else:
                    native=fitz.open(target);assert len(native)==1
                    # Canonical exact ISO A4; native draw.io rounding is <1pt.
                    final=fitz.open();page=final.new_page(width=841.88976378,height=595.27559055)
                    page.show_pdf_page(page.rect,native,0)
                    final.save(OUT/target.name,garbage=4,deflate=True)
                    page.get_pixmap(dpi=300).save(OUT/(s['slug']+'.png'))
        combined=fitz.open()
        for s in SCENES:
            with fitz.open(OUT/(s['slug']+'.pdf')) as p:combined.insert_pdf(p)
        combined.save(OUT/'业务流程图-A4审阅版.pdf',garbage=4,deflate=True)
    (OUT/'export-log.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--export',action='store_true');parser.add_argument('--drawio',default=os.environ.get('DRAWIO_BIN','drawio'));args=parser.parse_args()
    build()
    if args.export:export(args.drawio)
