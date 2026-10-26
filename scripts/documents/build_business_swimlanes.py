"""Business-facing swimlanes: editable draw.io, SVG, PNG and individual and combined A4 PDFs.

Run: python -X utf8 scripts/documents/build_business_swimlanes.py
Creates editable and publication exports from the same explicit node/edge data.
"""
from pathlib import Path
import json
import math
import os
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

import pymupdf as fitz
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/thesis/business-flow'
PDF = ROOT / 'output/pdf/业务流程图-导师讲解版.pdf'
FONT = 'BusinessSong'
font_candidates = [os.environ.get('BUSINESS_FLOW_FONT', ''), 'C:/Windows/Fonts/simsun.ttc',
                   str(Path.home()/'.local/share/fonts/NotoSerifSC.ttf')]
font_path = next((path for path in font_candidates if path and Path(path).is_file()), None)
if font_path:
    pdfmetrics.registerFont(TTFont(FONT, font_path, subfontIndex=0))
else:
    FONT = 'STSong-Light'
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
INK = '#25313a'
ACCENT = '#355e76'
SCENES = []


def scene(slug, title, height, lanes, note):
    s = dict(slug=slug, title=title, width=1100, height=height,
             lanes=lanes, note=note, nodes=[], edges=[])
    SCENES.append(s)
    return s


def node(s, key, lane, y, text, kind='process', w=280, h=72):
    count = len(s['lanes'])
    center = 40 + (1020 / count) * (lane + .5)
    n = dict(id=key, lane=lane, x=center-w/2, y=y, w=w, h=h,
             text=text, kind=kind)
    s['nodes'].append(n)
    return n


def port(n, side):
    x, y, w, h = [n[k] for k in ('x', 'y', 'w', 'h')]
    return {'t': (x+w/2, y), 'b': (x+w/2, y+h),
            'l': (x, y+h/2), 'r': (x+w, y+h/2)}[side]


def edge(s, a, b, start='b', end='t', bends=(), label='', labelpos=None):
    pts = [port(a, start), *bends, port(b, end)]
    s['edges'].append(dict(source=a['id'], target=b['id'], start=start, end=end,
                           points=pts, label=label, labelpos=labelpos))


# Layout is deliberately compact enough for a portrait A4 page.
s = scene('01-错题分析与巩固学习', '错题分析与巩固学习业务流程图', 1510,
          ['学生', '学习平台', 'AI 服务'],
          '识别失败可手录；解析失败可重试，已存错题与计划保留。\n练习由学生自评，平台保存记录并更新掌握度。')
a=node(s,'start',0,155,'开始','terminal',160,36)
b=node(s,'image',0,215,'图片录入？','decision',220,66)
c=node(s,'upload',0,315,'上传单题图片',w=240,h=54)
d=node(s,'imagecheck',1,315,'校验图片\n请求识别',w=240,h=54)
e=node(s,'recognize',2,315,'识别题干、科目\n作答与来源',w=240,h=54)
f=node(s,'manual',0,410,'手工录入\n富文本编辑',w=240,h=54)
g=node(s,'candidate',1,410,'回填候选内容\n或显示错误提示',w=240,h=54)
h=node(s,'confirm',0,505,'核对并编辑\n确认提交',w=240,h=54)
i=node(s,'save',1,505,'校验并保存\n错题与图片',w=240,h=54)
j=node(s,'plans',1,595,'创建五条复习计划\n独立请求后台解析',w=260,h=54)
k=node(s,'embed',2,595,'生成题干文本向量',w=240,h=54)
l=node(s,'retrieve',1,685,'检索本人参考题\n组装分析输入',w=240,h=54)
m=node(s,'analyze',2,685,'辅助归类、错因\n与解题解析',w=240,h=54)
n=node(s,'status',1,775,'校验模型结果\n记录成功或失败',w=240,h=54)
o=node(s,'read',0,775,'查看解析\n或失败提示',w=240,h=54)
p=node(s,'extend',0,865,'拓展练习？','decision',220,66)
q=node(s,'variantchoice',1,865,'请求变式？','decision',220,66)
r=node(s,'variant',2,871,'生成三道变式题',w=240,h=54)
t=node(s,'original',0,975,'选择原题练习',w=240,h=54)
u=node(s,'similar',1,975,'检索本人\n相似题',w=150,h=54)
u['x']=392
sv=node(s,'savevariant',1,975,'校验结果\n保存变式题',w=150,h=54)
sv['x']=558
v=node(s,'available',1,1070,'有可用题？','decision',220,66)
w=node(s,'exercise',0,1160,'选择题目作答\n对照答案自评',w=240,h=54)
x=node(s,'record',1,1160,'保存练习记录\n更新原题掌握度',w=240,h=54)
y=node(s,'feedback',0,1280,'查看学习反馈',w=240,h=54)
z=node(s,'end',0,1390,'结束','terminal',160,36)
edge(s,a,b)
edge(s,b,c,label='是',labelpos=(238,301))
edge(s,b,f,'l','l',[(65,248),(65,437)],label='否',labelpos=(86,388))
edge(s,c,d,'r','l');edge(s,d,e,'r','l')
edge(s,e,g,'b','t',[(890,389),(550,389)])
edge(s,g,h,'b','t',[(550,485),(210,485)])
edge(s,f,h)
edge(s,h,i,'r','l')
edge(s,i,g,'r','r',[(700,532),(700,437)],label='校验失败',labelpos=(780,486))
edge(s,i,j,label='成功',labelpos=(584,581))
edge(s,j,k,'r','l')
edge(s,k,l,'b','t',[(890,671),(550,671)])
edge(s,l,m,'r','l')
edge(s,m,n,'b','t',[(890,756),(550,756)])
edge(s,n,o,'l','r');edge(s,o,p)
edge(s,p,q,'r','l',label='是',labelpos=(380,888))
edge(s,p,t,label='否',labelpos=(235,958))
edge(s,q,r,'r','l',label='是',labelpos=(720,888))
edge(s,q,u,'b','t',[(550,948),(467,948)],label='否',labelpos=(520,956))
edge(s,r,sv,'b','t',[(890,950),(633,950)])
edge(s,u,v,'b','t',[(467,1050),(550,1050)])
edge(s,sv,v,'b','t',[(633,1050),(550,1050)])
edge(s,v,w,'b','t',[(550,1148),(210,1148)],label='是',labelpos=(576,1147))
edge(s,v,t,'l','r',[(380,1103),(380,1002)],label='否',labelpos=(402,1065))
edge(s,t,w)
edge(s,w,x,'r','l')
edge(s,x,y,'b','r',[(550,1307)])
edge(s,y,z)

s = scene('02-按期复习', '按期复习业务流程图', 1110,
          ['学生', '学习平台'],
          '保存错题即建第1/2/4/7/15天计划；每日8点发送当日到期提醒。\n练习不自动完成复习任务，日期不因自评结果重排。')
a=node(s,'start',0,155,'开始：查看复习任务','terminal',300,42)
b=node(s,'open',0,245,'查看提醒或任务列表',w=320,h=60)
c=node(s,'query',1,245,'查询到期、逾期\n未完成的任务',w=320,h=60)
d=node(s,'due',1,350,'有待复习任务？','decision',300,86)
e=node(s,'empty',0,363,'暂无任务\n之后再查看',w=280,h=60)
f=node(s,'show',1,490,'展示待复习任务',w=300,h=60)
g=node(s,'review',0,490,'选择错题并复习\n按需进行自评练习',w=320,h=60)
h=node(s,'confirm',0,610,'确认完成？','decision',270,86)
i=node(s,'pending',1,623,'保留未完成状态\n逾期仍可处理',w=300,h=60)
j=node(s,'finish',1,770,'记录该条任务已完成',w=320,h=60)
k=node(s,'feedback',0,770,'查看学习反馈',w=300,h=60)
z=node(s,'end',0,960,'结束本次复习','terminal',260,42)
edge(s,a,b);edge(s,b,c,'r','l');edge(s,c,d)
edge(s,d,e,'l','r',label='否',labelpos=(550,383))
edge(s,d,f,label='是',labelpos=(830,473))
edge(s,f,g,'l','r');edge(s,g,h)
edge(s,h,i,'r','l',label='否',labelpos=(550,643))
edge(s,h,j,'b','t',[(295,735),(805,735)],label='是',labelpos=(320,721))
edge(s,j,k,'l','r');edge(s,k,z)
edge(s,e,z,'l','l',[(65,393),(65,981)])
edge(s,i,z,'r','b',[(1040,653),(1040,1040),(295,1040)])

s = scene('03-管理与学情查看', '管理与学情查看业务流程图', 1060,
          ['管理员', '学习平台', '教师'],
          '两段业务独立，管理操作按需选择。\n教师仅查看系统汇总，不含班级或学生个人钻取。')
a=node(s,'adminstart',0,170,'开始：基础维护','terminal',250,44)
b=node(s,'manage',0,285,'维护科目与知识点\n查询、停用账号\n按需发布公告',w=280,h=100)
c=node(s,'apply',1,305,'校验并保存操作\n提供基础数据',w=250,h=60)
d=node(s,'adminend',0,460,'管理结束','terminal',210,44)
e=node(s,'teacherstart',2,600,'开始：查看学情','terminal',250,44)
f=node(s,'request',2,705,'请求学情报告',w=250,h=60)
g=node(s,'aggregate',1,705,'按当前记录\n聚合系统学情',w=250,h=60)
h=node(s,'read',2,820,'查看错题、练习\n复习与掌握度汇总',w=280,h=60)
i=node(s,'teacherend',2,940,'查看结束','terminal',210,44)
edge(s,a,b);edge(s,b,c,'r','l')
edge(s,c,d,'b','t',[(550,425),(210,425)])
edge(s,e,f);edge(s,f,g,'l','r')
edge(s,g,h,'b','l',[(550,850)])
edge(s,h,i)


def validate():
    for s in SCENES:
        nodes={n['id']: n for n in s['nodes']}
        assert len(nodes)==len(s['nodes'])
        for n in nodes.values():
            assert n['x']>=40 and n['x']+n['w']<=1060
            assert 138<=n['y'] and n['y']+n['h']<s['height']-55
            for line in n['text'].splitlines():
                assert pdfmetrics.stringWidth(line,FONT,23) < n['w']-16, (n['id'],line)
        reached=set()
        def visit(key):
            if key in reached:return
            reached.add(key)
            for e in s['edges']:
                if e['source']==key:visit(e['target'])
        for n in s['nodes']:
            if n['kind']=='terminal' and n['text'].startswith(('开始','错题保存')):visit(n['id'])
        assert reached==set(nodes), (s['slug'],set(nodes)-reached)
        for n in s['nodes']:
            if n['kind']=='decision':
                outgoing=[e['label'] for e in s['edges'] if e['source']==n['id']]
                assert len(outgoing)==2 and any(x.startswith('是') for x in outgoing) and any(x.startswith('否') for x in outgoing)
        # All connectors are orthogonal and may only enter their endpoint nodes.
        for e in s['edges']:
            for (x1,y1),(x2,y2) in zip(e['points'],e['points'][1:]):
                assert x1==x2 or y1==y2, (s['slug'],e['source'],e['target'],'non-orthogonal')
                for n in s['nodes']:
                    if n['id'] in (e['source'],e['target']):continue
                    left,right=n['x']+2,n['x']+n['w']-2
                    top,bottom=n['y']+2,n['y']+n['h']-2
                    hit=(x1==x2 and left<x1<right and max(min(y1,y2),top)<min(max(y1,y2),bottom)) or (y1==y2 and top<y1<bottom and max(min(x1,x2),left)<min(max(x1,x2),right))
                    assert not hit,(s['slug'],e['source'],e['target'],'crosses',n['id'])


def draw(s, c):
    H=s['height']; parts=[]
    def rect(x,y,w,h,fill='#ffffff',radius=0):
        c.setStrokeColor(INK);c.setFillColor(fill);c.setLineWidth(1.4)
        c.roundRect(x,H-y-h,w,h,radius,stroke=1,fill=1)
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{INK}" stroke-width="1.4"/>')
    def text(x,y,value,size=23,color=INK):
        c.setFillColor(color);c.setFont(FONT,size)
        lines=value.splitlines();first=y-(len(lines)-1)*size*.65
        for idx,line in enumerate(lines):
            baseline=first+idx*size*1.3+size*.35
            c.drawCentredString(x,H-baseline,line)
            parts.append(f'<text x="{x}" y="{baseline}" text-anchor="middle" font-family="Noto Serif SC,Noto Serif CJK SC,SimSun,宋体,serif" font-size="{size}" fill="{color}">{escape(line)}</text>')
    text(550,39,s['title'],31)
    count=len(s['lanes']);lw=1020/count
    for idx,lane in enumerate(s['lanes']):
        rect(40+idx*lw,90,lw,H-160,'#ffffff')
        rect(40+idx*lw,90,lw,48,'#e9eff3')
        text(40+(idx+.5)*lw,114,lane,25)
    for e in s['edges']:
        pts=e['points']; c.setStrokeColor(ACCENT);c.setFillColor(ACCENT);c.setLineWidth(1.8)
        path=c.beginPath();path.moveTo(pts[0][0],H-pts[0][1])
        for x,y in pts[1:]:path.lineTo(x,H-y)
        c.drawPath(path)
        (x0,y0),(x,y)=pts[-2:];ang=math.atan2(y-y0,x-x0)
        arrow=[(x,y),(x-11*math.cos(ang-.45),y-11*math.sin(ang-.45)),(x-11*math.cos(ang+.45),y-11*math.sin(ang+.45))]
        path=c.beginPath();path.moveTo(arrow[0][0],H-arrow[0][1])
        for ax,ay in arrow[1:]:path.lineTo(ax,H-ay)
        path.close();c.drawPath(path,stroke=0,fill=1)
        parts.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="{ACCENT}" stroke-width="1.8" marker-end="url(#arrow)"/>')
    for n in s['nodes']:
        x,y,w,h=[n[k] for k in ('x','y','w','h')]
        if n['kind']=='decision':
            pts=[(x+w/2,y),(x+w,y+h/2),(x+w/2,y+h),(x,y+h/2)]
            c.setStrokeColor(INK);c.setFillColor('#f7f2e7');path=c.beginPath();path.moveTo(pts[0][0],H-pts[0][1])
            for px,py in pts[1:]:path.lineTo(px,H-py)
            path.close();c.drawPath(path,stroke=1,fill=1)
            parts.append(f'<polygon points="{" ".join(f"{px},{py}" for px,py in pts)}" fill="#f7f2e7" stroke="{INK}" stroke-width="1.4"/>')
            text(x+w/2,y+h/2,n['text'],23)
        else:
            rect(x,y,w,h,'#eef3f5' if n['kind']=='terminal' else '#ffffff',h/2 if n['kind']=='terminal' else 0)
            text(x+w/2,y+h/2,n['text'])
    for e in s['edges']:
        if e['label']:
            x,y=e['labelpos']; width=pdfmetrics.stringWidth(e['label'],FONT,23)+10
            c.setFillColor('#ffffff');c.rect(x-width/2,H-y-11,width,25,stroke=0,fill=1)
            parts.append(f'<rect x="{x-width/2}" y="{y-14}" width="{width}" height="25" fill="white"/>')
            text(x,y,e['label'],23)
    text(550,H-30,s['note'],23)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{H}" viewBox="0 0 1100 {H}"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="{ACCENT}"/></marker></defs><rect width="1100" height="{H}" fill="white"/>'+''.join(parts)+'</svg>'
    (BASE/(s['slug']+'.svg')).write_text(svg,encoding='utf-8')


def drawio():
    root=ET.Element('mxfile',host='app.diagrams.net',type='device')
    for s in SCENES:
        dia=ET.SubElement(root,'diagram',name=s['slug'],id=s['slug'][:2])
        model=ET.SubElement(dia,'mxGraphModel',page='1',pageScale='1',pageWidth='1100',pageHeight=str(s['height']),grid='1',gridSize='10')
        graph=ET.SubElement(model,'root');ET.SubElement(graph,'mxCell',id='0');ET.SubElement(graph,'mxCell',id='1',parent='0')
        def cell(key,value,x,y,w,h,style):
            el=ET.SubElement(graph,'mxCell',id=key,value=value,style=style,vertex='1',parent='1')
            ET.SubElement(el,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
        cell('title',s['title'],40,10,1020,60,'text;html=0;fontFamily=SimSun;fontSize=31;align=center;')
        for idx,lane in enumerate(s['lanes']):
            lw=1020/len(s['lanes'])
            cell('lane'+str(idx),lane,40+idx*lw,90,lw,s['height']-160,'swimlane;html=0;startSize=48;horizontal=1;fontSize=25;fontFamily=SimSun;fillColor=#e9eff3;swimlaneFillColor=#ffffff;strokeColor=#25313a;')
        for n in s['nodes']:
            style='rhombus;' if n['kind']=='decision' else 'rounded=1;arcSize=60;' if n['kind']=='terminal' else 'rounded=0;'
            style+='html=0;whiteSpace=wrap;fontFamily=SimSun;fontSize=23;align=center;verticalAlign=middle;fillColor='+('#f7f2e7' if n['kind']=='decision' else '#ffffff')+';strokeColor=#25313a;'
            cell(n['id'],n['text'],n['x'],n['y'],n['w'],n['h'],style)
        for idx,e in enumerate(s['edges']):
            ports={'t':(.5,0),'b':(.5,1),'l':(0,.5),'r':(1,.5)}
            ex,ey=ports[e['start']];ix,iy=ports[e['end']]
            style=f'edgeStyle=segmentEdgeStyle;rounded=0;html=0;endArrow=block;endFill=1;strokeColor={ACCENT};fontFamily=SimSun;fontSize=23;labelBackgroundColor=#ffffff;exitX={ex};exitY={ey};entryX={ix};entryY={iy};'
            el=ET.SubElement(graph,'mxCell',id='edge'+str(idx),value=e['label'],source=e['source'],target=e['target'],parent='1',edge='1',style=style)
            geo=ET.SubElement(el,'mxGeometry',relative='1',attrib={'as':'geometry'})
            if len(e['points'])>2:
                arr=ET.SubElement(geo,'Array',attrib={'as':'points'})
                for x,y in e['points'][1:-1]:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
        cell('note',s['note'],40,s['height']-55,1020,50,'text;html=0;fontFamily=SimSun;fontSize=23;align=center;')
    ET.ElementTree(root).write(BASE/'业务流程图.drawio',encoding='utf-8',xml_declaration=True)
    for diagram, scene_data in zip(root, SCENES):
        single = ET.Element('mxfile', host='app.diagrams.net', type='device')
        single.append(ET.fromstring(ET.tostring(diagram)))
        ET.ElementTree(single).write(BASE/(scene_data['slug']+'.drawio'), encoding='utf-8', xml_declaration=True)


def main():
    validate();BASE.mkdir(parents=True,exist_ok=True);PDF.parent.mkdir(parents=True,exist_ok=True)
    (BASE/'业务流程图.json').write_text(json.dumps(SCENES,ensure_ascii=False,indent=2),encoding='utf-8')
    drawio()
    c=canvas.Canvas(str(PDF),pagesize=A4);c.setTitle('错题分析与学习推荐系统：业务泳道图')
    for s in SCENES:
        pw,ph=A4;scale=min((pw-38)/1100,(ph-38)/s['height'])
        c.saveState();c.translate((pw-1100*scale)/2,(ph-s['height']*scale)/2);c.scale(scale,scale)
        draw(s,c);c.restoreState();c.showPage()
    c.save()
    doc=fitz.open(PDF)
    for idx,s in enumerate(SCENES):
        single=fitz.open(); single.insert_pdf(doc,from_page=idx,to_page=idx)
        single.save(BASE/(s['slug']+'.pdf'))
    assert len(doc)==3
    for page,s in zip(doc,SCENES):
        assert s['title'] in page.get_text().replace('\n','')
        assert '\ufffd' not in page.get_text()
        pix=page.get_pixmap(dpi=300,alpha=False)
        pix.save(BASE/(s['slug']+'.png'))
    report=dict(pages=3,format='A4 portrait',editable_pages=3,
                nodes=[len(s['nodes']) for s in SCENES],edges=[len(s['edges']) for s in SCENES],
                checks=['unique node ids','all nodes reachable from starts','both outcomes for each decision',
                        'orthogonal connectors','connectors avoid unrelated nodes','node label width','PDF title extraction','no replacement characters'],
                visual_review='pending')
    (BASE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
