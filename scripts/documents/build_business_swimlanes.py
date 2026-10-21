"""Business-facing swimlanes: editable draw.io, SVG, PNG and a three-page A3 PDF.

Run: python -X utf8 scripts/documents/build_business_swimlanes.py
Only creates standalone review diagrams; does not replace numbered thesis figures.
"""
from pathlib import Path
import json
import math
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

import pymupdf as fitz
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A3

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/thesis/business-flow'
PDF = ROOT / 'output/pdf/业务流程图-导师讲解版.pdf'
FONT = 'BusinessSong'
pdfmetrics.registerFont(TTFont(FONT, 'C:/Windows/Fonts/simsun.ttc', subfontIndex=0))
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


s = scene('01-错题分析与巩固学习', '错题分析与巩固学习业务流程图', 2310,
          ['学生', '学习平台'],
          '前提：学生已登录。分析失败不删除错题或复习计划；按期复习流程见图 02。')
a = node(s, 'start', 0, 145, '开始：整理一道错题', 'terminal', 250, 52)
b = node(s, 'input', 0, 245, '填写科目、题干和答案\n确认并提交错题')
c = node(s, 'check', 1, 245, '检查录入信息')
d = node(s, 'valid', 1, 365, '信息是否符合要求？', 'decision', 270, 110)
f = node(s, 'fix', 0, 384, '根据提示补充或修改')
g = node(s, 'save', 1, 525, '保存错题\n同时安排五个节点的复习')
h = node(s, 'request', 0, 650, '查看已保存的错题\n查看或重新请求分析')
i = node(s, 'analyze', 1, 650, '参考本人同科目的相关题\n分析错题并提供解析')
j = node(s, 'success', 1, 790, '分析是否成功？', 'decision', 250, 110)
k = node(s, 'failure', 0, 809, '查看分析失败提示')
l = node(s, 'retry', 0, 960, '是否重新分析？', 'decision', 250, 110)
m = node(s, 'show', 1, 980, '展示知识点、辅助错因\n及解题解析')
n = node(s, 'extend', 0, 1190, '是否需要拓展练习？', 'decision', 270, 110)
o = node(s, 'resources', 1, 1209, '按学生选择提供相似题\n或生成三道变式题')
o2 = node(s, 'available', 1, 1335, '是否取得\n可用练习题？', 'decision', 250, 110)
p = node(s, 'original', 0, 1354, '选择原题练习')
q = node(s, 'practice', 0, 1505, '作答并对照答案\n自评对错、提交练习结果')
r = node(s, 'correct', 0, 1640, '学生自评是否正确？', 'decision', 270, 110)
t = node(s, 'up', 1, 1659, '原题掌握度增加 15\n最高为 100')
u = node(s, 'down', 1, 1820, '原题掌握度减少 20\n最低为 0')
v = node(s, 'record', 1, 2010, '保存练习记录\n和掌握度变化')
w = node(s, 'view', 0, 2010, '查看练习记录\n按需查看个人学情')
z = node(s, 'end', 0, 2165, '本次学习结束', 'terminal', 230, 52)
edge(s,a,b); edge(s,b,c,'r','l'); edge(s,c,d)
edge(s,d,f,'l','r',label='否',labelpos=(550,400))
edge(s,f,b,'l','l',[(100,420),(100,281)],label='修改后重新提交',labelpos=(203,340))
edge(s,d,g,label='是',labelpos=(830,505))
edge(s,g,h,'b','t',[(805,620),(295,620)])
edge(s,h,i,'r','l'); edge(s,i,j)
edge(s,j,k,'l','r',label='否',labelpos=(550,825))
edge(s,k,l)
edge(s,l,h,'l','l',[(65,1015),(65,686)],label='是：重新请求',labelpos=(170,745))
edge(s,l,n,label='否：继续学习',labelpos=(405,1100))
edge(s,j,m,label='是',labelpos=(830,945))
edge(s,m,n,'b','t',[(805,1135),(295,1135)])
edge(s,n,o,'r','l',label='是',labelpos=(550,1220))
edge(s,n,p,label='否',labelpos=(320,1335))
edge(s,p,q)
edge(s,o,o2)
edge(s,o2,p,'l','r',label='否',labelpos=(550,1365))
edge(s,o2,q,'b','t',[(805,1475),(295,1475)],label='是',labelpos=(830,1460))
edge(s,q,r)
edge(s,r,t,'r','l',label='是',labelpos=(550,1670))
edge(s,r,u,'b','l',[(295,1856)],label='否',labelpos=(320,1805))
edge(s,t,v,'r','t',[(1020,1695),(1020,1965),(805,1965)])
edge(s,u,v)
edge(s,v,w,'l','r'); edge(s,w,z)

s = scene('02-按期复习', '按期复习业务流程图', 1840,
          ['学生', '学习平台'],
          '练习提交与确认完成复习相互独立；作答对错不改变既定复习日期。')
a=node(s,'start',1,145,'错题保存后进入复习周期','terminal',300,52)
b=node(s,'plan',1,250,'安排第 1、2、4、7、15 天\n的五条复习任务',w=340)
c=node(s,'due',1,390,'是否有到期或逾期\n未完成任务？','decision',290,120)
d=node(s,'wait',0,414,'暂无待复习任务\n之后再次查看')
e=node(s,'tasks',1,585,'展示待复习任务\n针对当天到期任务\n发送站内提醒',h=92)
f=node(s,'choose',0,595,'查看任务并选择错题')
g=node(s,'review',0,745,'重看原题、答案与解析\n按需要进行练习')
h=node(s,'confirm',0,900,'是否确认完成\n本次复习？','decision',270,120)
i=node(s,'pending',1,924,'保留未完成状态\n逾期任务仍可继续处理')
j=node(s,'finish',1,1130,'记录该条复习任务已完成')
k=node(s,'more',0,1285,'是否继续处理\n其他待复习任务？','decision',290,120)
l=node(s,'report',0,1510,'按需查看个人学情\n之后按计划继续复习')
m=node(s,'end',0,1670,'本次复习结束','terminal',230,52)
edge(s,a,b);edge(s,b,c)
edge(s,c,d,'l','r',label='否',labelpos=(550,425))
edge(s,d,m,'l','l',[(65,450),(65,1696)],label='等待后续复习',labelpos=(170,1630))
edge(s,c,e,label='是',labelpos=(830,555))
edge(s,e,f,'l','r');edge(s,f,g);edge(s,g,h)
edge(s,h,i,'r','l',label='否',labelpos=(550,935))
edge(s,h,j,'b','l',[(295,1166)],label='是',labelpos=(320,1090))
edge(s,i,m,'r','r',[(1020,960),(1020,1755),(480,1755),(480,1696)])
edge(s,j,k,'b','t',[(805,1245),(295,1245)])
edge(s,k,f,'l','l',[(105,1345),(105,631)],label='是',labelpos=(130,1210))
edge(s,k,l,label='否',labelpos=(320,1460));edge(s,l,m)

s = scene('03-管理与学情查看', '基础管理与学情查看辅助业务流程图', 1220,
          ['管理员', '学习平台', '教师'],
          '上下两段为独立业务，不要求每次学习都执行管理操作；教师查看系统范围汇总。')
a=node(s,'adminstart',0,160,'开始：维护基础资料','terminal',270,52)
b=node(s,'manage',0,275,'维护科目、知识点\n查询或停用账号\n发布公告',w=290,h=108)
c=node(s,'apply',1,285,'保存管理操作\n提供可用资料与公告',w=260,h=88)
d=node(s,'adminend',0,455,'本次管理结束','terminal',240,52)
e=node(s,'teacherstart',2,630,'开始：查看汇总学情','terminal',270,52)
f=node(s,'request',2,758,'选择查看学情报告',w=250)
g=node(s,'aggregate',1,750,'按访问时的现有记录\n汇总系统范围学情',w=260,h=88)
h=node(s,'read',2,920,'查看错题、练习、复习\n及知识点掌握情况',w=280,h=88)
i=node(s,'teacherend',2,1075,'本次查看结束','terminal',240,52)
edge(s,a,b);edge(s,b,c,'r','l')
edge(s,c,d,'b','t',[(550,415),(210,415)])
edge(s,e,f);edge(s,f,g,'l','r')
edge(s,g,h,'b','l',[(550,964)])
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
            parts.append(f'<text x="{x}" y="{baseline}" text-anchor="middle" font-family="SimSun,宋体,serif" font-size="{size}" fill="{color}">{escape(line)}</text>')
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
            text(x+w/2,y+h/2,n['text'],21)
        else:
            rect(x,y,w,h,'#eef3f5' if n['kind']=='terminal' else '#ffffff',h/2 if n['kind']=='terminal' else 0)
            text(x+w/2,y+h/2,n['text'])
    for e in s['edges']:
        if e['label']:
            x,y=e['labelpos']; width=pdfmetrics.stringWidth(e['label'],FONT,20)+10
            c.setFillColor('#ffffff');c.rect(x-width/2,H-y-11,width,25,stroke=0,fill=1)
            parts.append(f'<rect x="{x-width/2}" y="{y-14}" width="{width}" height="25" fill="white"/>')
            text(x,y,e['label'],20)
    text(550,H-30,s['note'],18)
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
            style=f'edgeStyle=segmentEdgeStyle;rounded=0;html=0;endArrow=block;endFill=1;strokeColor={ACCENT};fontFamily=SimSun;fontSize=20;labelBackgroundColor=#ffffff;exitX={ex};exitY={ey};entryX={ix};entryY={iy};'
            el=ET.SubElement(graph,'mxCell',id='edge'+str(idx),value=e['label'],source=e['source'],target=e['target'],parent='1',edge='1',style=style)
            geo=ET.SubElement(el,'mxGeometry',relative='1',attrib={'as':'geometry'})
            if len(e['points'])>2:
                arr=ET.SubElement(geo,'Array',attrib={'as':'points'})
                for x,y in e['points'][1:-1]:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
        cell('note',s['note'],40,s['height']-55,1020,50,'text;html=0;fontFamily=SimSun;fontSize=18;align=center;')
    ET.ElementTree(root).write(BASE/'业务流程图.drawio',encoding='utf-8',xml_declaration=True)


def main():
    validate();BASE.mkdir(parents=True,exist_ok=True);PDF.parent.mkdir(parents=True,exist_ok=True)
    (BASE/'业务流程图.json').write_text(json.dumps(SCENES,ensure_ascii=False,indent=2),encoding='utf-8')
    drawio()
    c=canvas.Canvas(str(PDF),pagesize=A3);c.setTitle('错题分析与学习推荐系统：业务泳道图')
    for s in SCENES:
        pw,ph=A3;scale=min((pw-38)/1100,(ph-38)/s['height'])
        c.saveState();c.translate((pw-1100*scale)/2,(ph-s['height']*scale)/2);c.scale(scale,scale)
        draw(s,c);c.restoreState();c.showPage()
    c.save()
    doc=fitz.open(PDF)
    assert len(doc)==3
    for page,s in zip(doc,SCENES):
        assert s['title'] in page.get_text().replace('\n','')
        assert '\ufffd' not in page.get_text()
        pix=page.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False)
        pix.save(BASE/(s['slug']+'.png'))
    report=dict(pages=3,format='A3 portrait',editable_pages=3,
                nodes=[len(s['nodes']) for s in SCENES],edges=[len(s['edges']) for s in SCENES],
                checks=['unique node ids','all nodes reachable from starts','both outcomes for each decision',
                        'orthogonal connectors','connectors avoid unrelated nodes','node label width','PDF title extraction','no replacement characters'],
                visual_review='pending')
    (BASE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
