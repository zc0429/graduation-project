"""Build editable black/white UML and DFD review figures; no application changes."""
from pathlib import Path
import argparse,base64,hashlib,io,json,math,subprocess,tempfile,xml.etree.ElementTree as ET
import fitz
from fontTools import subset
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/thesis/requirements-20261112/figures';OUT.mkdir(parents=True,exist_ok=True)
S=827/1200; FONT='Noto Serif CJK SC'; SCENES=[]
def scene(key,title,kind='dfd'):
 s=dict(key=key,title=title,kind=kind,nodes=[],edges=[]);SCENES.append(s);return s
def n(s,id,text,x,y,w=240,h=70,kind='external',logical=None):
 d=dict(id=id,text=text,x=x-w/2,y=y-h/2,w=w,h=h,kind=kind,logical=logical or id);s['nodes'].append(d);return d
def pt(a,side,off=0):
 x=a['x']+a['w']/2;y=a['y']+a['h']/2;w=a['w']/2;h=a['h']/2
 if side in 'lr':
  dx=w*math.sqrt(max(0,1-(off/h)**2)) if a['kind'] in ['process','usecase'] else w
  return (x+(-dx if side=='l' else dx),y+off)
 dy=h*math.sqrt(max(0,1-(off/w)**2)) if a['kind'] in ['process','usecase'] else h
 return (x+off,y+(-dy if side=='t' else dy))
def e(s,a,b,label,side='r',end='l',off=0,toff=0,bends=(),pos=None,fields=None):
 p=[pt(a,side,off),*bends,pt(b,end,toff)]
 if pos is None:pos=((p[0][0]+p[-1][0])/2,(p[0][1]+p[-1][1])/2-24)
 s['edges'].append(dict(id='e'+str(len(s['edges'])),source=a['id'],target=b['id'],label=label,points=p,pos=pos,fields=fields or [label],arrow=s['kind']!='uml'))
def proc(s,id,label,y,x=600):return n(s,id,id+'\n'+label,x,y,220,160,'process')
def store(s,id,label,y,x=1040,suffix=''):return n(s,id+suffix,id+' '+label,x,y,240,60,'store',id)
def ext(s,id,label,y,x=160,suffix=''):return n(s,id+suffix,label,x,y,210,80,'external',id)
def pair(s,a,b,ab,ba,fa=None,fb=None):
 e(s,a,b,ab,off=-23,toff=-23,fields=fa)
 e(s,b,a,ba,side='l',end='r',off=23,toff=23,pos=((pt(a,'r')[0]+pt(b,'l')[0])/2,pt(a,'r')[1]+50),fields=fb)
def read(s,d,p,label,off=0,fields=None):
 y=d['y']+d['h']/2-15
 e(s,d,p,label,side='l',end='r',off=-15,toff=off,bends=[(770,y)],pos=(850,y-24),fields=fields)
def write(s,p,d,label,off=0,fields=None):
 y=d['y']+d['h']/2+15
 e(s,p,d,label,off=off,toff=15,bends=[(770,y)],pos=(850,y+24),fields=fields)

s=scene('3-1','系统用例图','uml')
boundary=n(s,'boundary','',630,835,700,1470,'boundary')
a=n(s,'student','学生',110,530,65,105,'actor');t=n(s,'teacher','教师',110,1080,65,105,'actor');ad=n(s,'admin','管理员',110,1370,65,105,'actor');ai=n(s,'ai','AI模型',1090,540,65,105,'actor')
for i,(text,y) in enumerate([('管理个人错题',200),('分析错题',340),('学习知识内容',480),('开展做题练习',620),('完成复习',760),('查看个人学情',900)]):
 u=n(s,'u'+str(i),text,630,y,450,100,'usecase');e(s,a,u,'',fields=[])
 if i in [1,2,3]:e(s,u,ai,'',fields=[])
u=n(s,'teacher_use','查看全站聚合学情',630,1080,450,100,'usecase');e(s,t,u,'',fields=[])
for i,(text,y) in enumerate([('维护账号、科目与知识点',1280),('发布系统公告',1460)]):u=n(s,'admin_use'+str(i),text,630,y,450,100,'usecase');e(s,ad,u,'',fields=[])

s=scene('3-6','系统0层数据流图（一）')
p=proc(s,'P1','认证与账户管理',300);a=ext(s,'E123','学生、教师\n管理员',300);d=store(s,'D1','账户资料',300)
pair(s,a,p,'登录与账户资料','身份与账户结果',['登录资料','账户维护资料'],['身份结果','账户结果']);pair(s,p,d,'账户变更','账户数据',['账户变更'],['账户数据'])
p=proc(s,'P2','基础资料维护',800);a=ext(s,'E123','学生、教师\n管理员',800,suffix='_base');d=store(s,'D2','科目与知识点',700);d6=store(s,'D6','消息与公告',900)
pair(s,a,p,'基础查询与维护资料','基础信息与维护结果',['基础查询','基础维护资料','公告资料'],['基础信息','维护结果'])
read(s,d,p,'基础记录',off=-40);write(s,p,d,'基础资料',off=-10);write(s,p,d6,'公告',off=35)
p=proc(s,'P5','学情与通知处理',1300);a=ext(s,'E123','学生、教师\n管理员',1300,suffix='_reports');d3=store(s,'D3','错题与解析',1140);d5=store(s,'D5','练习与复习记录',1300);d6=store(s,'D6','消息与公告',1460,suffix='_report')
pair(s,a,p,'报告查询／通知操作','报告与通知信息',['报告查询','通知查询','已读确认'],['报告信息','通知信息'])
read(s,d3,p,'错题统计',off=-50);read(s,d5,p,'练习复习数据',off=-15);read(s,d6,p,'消息与公告',off=30);write(s,p,d6,'消息状态',off=60)

s=scene('3-7','系统0层数据流图（二）')
p=proc(s,'P3','错题录入与分析',400);a=ext(s,'E1','学生',400);ai=ext(s,'E4','AI模型',120,x=600);d2=store(s,'D2','科目与知识点',280);d3=store(s,'D3','错题与解析',400);d5=store(s,'D5','练习与复习记录',580)
pair(s,a,p,'错题资料与查询','错题信息与导出',['错题资料','解析请求','错题导出查询'],['错题解析信息','错题导出结果'])
e(s,p,ai,'识别分析上下文','t','b',-35,-35,pos=(450,245),fields=['识别分析上下文']);e(s,ai,p,'识别分析结果','b','t',35,35,pos=(745,180),fields=['识别分析结果'])
read(s,d2,p,'科目知识点',off=-50);read(s,d3,p,'本人题目与参考',off=-18);write(s,p,d3,'错题与解析',off=25)
write(s,p,d5,'复习计划',off=45)
p=proc(s,'P4','学习练习与复习',1210);a=ext(s,'E1','学生',1210,suffix='_learning');ai=ext(s,'E4','AI模型',850,x=600,suffix='_learning')
pair(s,a,p,'学习、作答与复习资料','资源与学习反馈',['学习请求','作答数据','复习查询','完成确认'],['学习资源','练习反馈','复习信息'])
e(s,p,ai,'生成上下文','t','b',-35,-35,pos=(465,1010),fields=['生成上下文']);e(s,ai,p,'生成结果','b','t',35,35,pos=(735,955),fields=['生成结果'])
d2=store(s,'D2','科目与知识点',1020,suffix='_learning');d3=store(s,'D3','错题与解析',1160,suffix='_learning');d4=store(s,'D4','学习资源',1320);d5=store(s,'D5','练习与复习记录',1480,suffix='_learning')
read(s,d2,p,'科目知识点',off=-50,fields=['科目知识点']);read(s,d3,p,'本人原题／解析',off=-25,fields=['本人原题','解析']);write(s,p,d3,'掌握度',off=0,fields=['掌握度'])
read(s,d4,p,'知识内容／拓展题',off=20,fields=['知识内容','拓展题']);write(s,p,d4,'生成资源',off=38,fields=['生成资源'])
read(s,d5,p,'已练标识／任务',off=50,fields=['已练题标识','复习任务']);write(s,p,d5,'练习／复习状态',off=65,fields=['练习记录','复习状态'])

s=scene('3-8','学习练习加工1层数据流图（一）')
p=proc(s,'P4.1','查询可用资源',400);a=ext(s,'E1','学生',400);pair(s,a,p,'学习请求','已有学习资源',['学习请求'],['学习资源'])
for id,label,y,flow,off,fields in [('D2','科目与知识点',180,'科目知识点',-55,['科目知识点']),('D3','错题与解析',380,'本人原题／解析',-20,['本人原题','解析']),('D4','学习资源',580,'知识内容／拓展题',20,['知识内容','拓展题']),('D5','练习与复习记录',780,'已练题标识',55,['已练题标识'])]:
 d=store(s,id,label,y);read(s,d,p,flow,off=off,fields=fields)
q=proc(s,'P4.2','生成与校验入库',1180);ai=ext(s,'E4','AI模型',1180);d=store(s,'D4','学习资源',1180,suffix='_new');a=ext(s,'E1','学生',1480,x=1040,suffix='_new')
e(s,p,q,'未满足的资源请求','b','t',pos=(455,820),fields=['缺少的资源请求'])
pair(s,ai,q,'生成结果','生成上下文',['生成结果'],['生成上下文']);write(s,q,d,'生成资源',fields=['生成资源'])
e(s,q,a,'学习资源／失败提示','b','l',bends=[(600,1480)],pos=(790,1450),fields=['学习资源'])

s=scene('3-9','学习练习加工1层数据流图（二）')
p=proc(s,'P4.3','记录作答结果',440);a=ext(s,'E1','学生',440);pair(s,a,p,'作答数据','练习反馈',['作答数据'],['练习反馈'])
d=store(s,'D3','错题与解析',240);read(s,d,p,'本人原题／解析',off=-40,fields=['本人原题','解析']);write(s,p,d,'掌握度',off=-10,fields=['掌握度'])
d=store(s,'D4','学习资源',480);read(s,d,p,'拓展题',off=20,fields=['拓展题'])
d=store(s,'D5','练习与复习记录',700);write(s,p,d,'练习记录',off=50,fields=['练习记录'])
p=proc(s,'P4.4','更新复习状态',1210);a=ext(s,'E1','学生',1210,suffix='_review');pair(s,a,p,'复习查询／完成确认','复习信息',['复习查询','完成确认'],['复习信息']);d=store(s,'D5','练习与复习记录',1210,suffix='_review');pair(s,p,d,'复习状态','复习任务',['复习状态'],['复习任务'])

# Context flows are aggregates of the external interfaces in both 0-layer panels.
s=scene('3-5','系统顶层数据流图')
p=n(s,'P0','0\n错题分析与\n学习推荐系统',600,850,300,270,'process');a=ext(s,'E1','学生',850);t=ext(s,'E2','教师',260,x=600);ad=ext(s,'E3','管理员',1440,x=600);ai=ext(s,'E4','AI模型',850,x=1040)
pair(s,a,p,'学生业务资料','学习结果与通知',['登录资料','账户维护资料','基础查询','错题资料','解析请求','错题导出查询','学习请求','作答数据','复习查询','完成确认','报告查询','通知查询','已读确认'],['身份结果','账户结果','基础信息','错题解析信息','错题导出结果','学习资源','练习反馈','复习信息','报告信息','通知信息'])
pair(s,p,ai,'模型请求上下文','模型处理结果',['识别分析上下文','生成上下文'],['识别分析结果','生成结果'])
e(s,t,p,'账户资料与业务查询','b','t',-45,-45,pos=(365,540),fields=['登录资料','账户维护资料','基础查询','报告查询','通知查询','已读确认']);e(s,p,t,'账户、基础与查询结果','t','b',45,45,pos=(825,540),fields=['身份结果','账户结果','基础信息','报告信息','通知信息'])
e(s,ad,p,'账户、查询与维护资料','t','b',-45,-45,pos=(355,1155),fields=['登录资料','账户维护资料','基础查询','基础维护资料','公告资料','通知查询','已读确认']);e(s,p,ad,'账户、维护与查询结果','b','t',45,45,pos=(835,1155),fields=['身份结果','账户结果','基础信息','维护结果','通知信息'])
SCENES.sort(key=lambda s:tuple(map(int,s['key'].split('-'))))

def xml(s):
 root=ET.Element('mxfile',host='app.diagrams.net',type='device');d=ET.SubElement(root,'diagram',name=s['title'],id=s['key']);m=ET.SubElement(d,'mxGraphModel',page='1',pageScale='1',pageWidth='827',pageHeight='1169',background='#ffffff');r=ET.SubElement(m,'root');ET.SubElement(r,'mxCell',id='0');ET.SubElement(r,'mxCell',id='1',parent='0')
 common=f'html=0;whiteSpace=nowrap;fontFamily={FONT};fontSize={24*S};fontColor=#000000;strokeColor=#000000;fillColor=#ffffff;strokeWidth={1.4*S};align=center;verticalAlign=middle;spacing=0;'
 def v(id,text,x,y,w,h,style):
  c=ET.SubElement(r,'mxCell',id=id,value=text,style=common+style,vertex='1',parent='1');ET.SubElement(c,'mxGeometry',x=str(x*S),y=str(y*S),width=str(w*S),height=str(h*S),attrib={'as':'geometry'})
 v('title',s['title'],60,30,1080,55,'strokeColor=none;fillColor=none;fontStyle=1;fontSize='+str(30*S)+';')
 for a in s['nodes']:
  shape={'process':'shape=ellipse;','usecase':'shape=ellipse;','external':'rounded=0;','store':'shape=partialRectangle;left=0;right=0;top=1;bottom=1;','actor':'shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;','boundary':'rounded=0;fillColor=none;'}[a['kind']]
  v(a['id'],a['text'],a['x'],a['y'],a['w'],a['h'],shape)
 nodes={a['id']:a for a in s['nodes']}
 for a in s['edges']:
  src=nodes[a['source']];dest=nodes[a['target']];first=a['points'][0];last=a['points'][-1]
  style=f"edgeStyle=none;rounded=0;html=0;strokeColor=#000000;strokeWidth={1.4*S};endArrow={'block' if a['arrow'] else 'none'};endSize={8*S};endFill=1;exitX={(first[0]-src['x'])/src['w']};exitY={(first[1]-src['y'])/src['h']};entryX={(last[0]-dest['x'])/dest['w']};entryY={(last[1]-dest['y'])/dest['h']};exitPerimeter=0;entryPerimeter=0;"
  c=ET.SubElement(r,'mxCell',id=a['id'],value='',style=style,edge='1',parent='1',source=a['source'],target=a['target']);g=ET.SubElement(c,'mxGeometry',relative='1',attrib={'as':'geometry'})
  if len(a['points'])>2:
   pts=ET.SubElement(g,'Array',attrib={'as':'points'})
   for x,y in a['points'][1:-1]:ET.SubElement(pts,'mxPoint',x=str(x*S),y=str(y*S))
  if a['label']:
   x,y=a['pos'];v(a['id']+'_label',a['label'],x-160,y-18,320,36,'strokeColor=none;fillColor=none;fontSize='+str(20*S)+';')
 return root

def embed(path,s):
 text=s['title']+''.join(a['text'] for a in s['nodes'])+''.join(a['label'] for a in s['edges']);css=[]
 for weight,style in [(400,'Regular'),(700,'Bold')]:
  fp=subprocess.check_output(['fc-match','-f','%{file}',f'{FONT}:style={style}'],text=True);font=TTFont(fp,fontNumber=2);opt=subset.Options();opt.flavor='woff';sub=subset.Subsetter(options=opt);sub.populate(text=text);sub.subset(font);font.flavor='woff';buf=io.BytesIO();font.save(buf);css.append("@font-face{font-family:'"+FONT+"';font-weight:"+str(weight)+";src:url(data:font/woff;base64,"+base64.b64encode(buf.getvalue()).decode()+") format('woff');}")
 ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns);t=ET.parse(path);r=t.getroot();defs=r.find('{'+ns+'}defs')
 if defs is None:defs=ET.SubElement(r,'{'+ns+'}defs')
 ET.SubElement(defs,'{'+ns+'}style').text='\n'.join(css);t.write(path,encoding='utf-8',xml_declaration=True)

def balance():
 # Parent P4 versus union of both 1-layer panels; duplicated stores retain logical IDs.
 def interfaces(scenes,prefix):
  result={}
  for s in scenes:
   ns={n['id']:n for n in s['nodes']}
   for e in s['edges']:
    a=ns[e['source']]['logical'];b=ns[e['target']]['logical']
    if a.startswith(prefix) and not b.startswith(prefix):key=(b,'out')
    elif b.startswith(prefix) and not a.startswith(prefix):key=(a,'in')
    else:continue
    result.setdefault(key,set()).update(e['fields'])
  return result
 parent=interfaces([next(s for s in SCENES if s['key']=='3-7')],'P4');children=interfaces([s for s in SCENES if s['key'] in ['3-8','3-9']],'P4.')
 assert parent==children,(parent,children)
 p4={'parent':'P4','children':['P4.1','P4.2','P4.3','P4.4'],'interfaces':{a+':'+b:sorted(v) for (a,b),v in parent.items()},'balanced':True}
 top=interfaces([s for s in SCENES if s['key']=='3-5'],'P0')
 zero={}
 # Shared actors on the 0-layer panels have role-specific fields, not identical privileges.
 for s in [s for s in SCENES if s['key'] in ['3-6','3-7']]:
  ns={n['id']:n for n in s['nodes']}
  for edge in s['edges']:
   a=ns[edge['source']]['logical'];b=ns[edge['target']]['logical']
   if a.startswith('E'):entity,direction,process=a,'in',b
   elif b.startswith('E'):entity,direction,process=b,'out',a
   else:continue
   for role in (['E1','E2','E3'] if entity=='E123' else [entity]):
    fields=set(edge['fields'])
    if process=='P2' and role!='E3':fields-={'基础维护资料','公告资料','维护结果'}
    if process=='P5' and role=='E3':fields-={'报告查询','报告信息'}
    zero.setdefault((role,direction),set()).update(fields)
 assert top==zero,{'top':top,'zero':zero}
 return {'P4_to_1':p4,'top_to_0':{'balanced':True,'interfaces':{a+':'+b:sorted(v) for (a,b),v in top.items()},'scope':'P2维护限管理员；P5报告限学生本人和教师聚合，其余共有资料按权限访问'}}

def build(drawio):
 logs=[];combined=fitz.open();checks=balance()
 for s in SCENES:
  path=OUT/(s['key']+'.drawio');ET.ElementTree(xml(s)).write(path,encoding='utf-8',xml_declaration=True)
  with tempfile.TemporaryDirectory() as td:
   for fmt in ['svg','pdf']:
    dst=Path(td)/(s['key']+'.'+fmt);cmd=[drawio,'--no-sandbox','--headless','--disable-gpu','--disable-update','--export','--theme','light','--format',fmt,'--output',str(dst),str(path)]
    if fmt=='svg':cmd[cmd.index('--output'):cmd.index('--output')]=['--size','page']
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=60);assert dst.exists(),p.stderr
    logs.append({'figure':s['key'],'format':fmt,'returncode':p.returncode,'note':'export file independently parsed; shutdown SIGILL is not GUI edit/save acceptance'})
    if fmt=='svg':(OUT/dst.name).write_bytes(dst.read_bytes());embed(OUT/dst.name,s)
    else:
     src=fitz.open(dst);doc=fitz.open();pg=doc.new_page(width=595.27559055,height=841.88976378);pg.show_pdf_page(pg.rect,src,0);doc.save(OUT/dst.name,garbage=4,deflate=True);pg.get_pixmap(dpi=300).save(OUT/(s['key']+'.png'));combined.insert_pdf(doc)
 combined.save(OUT/'需求分析图册-A4.pdf',garbage=4,deflate=True)
 (OUT/'diagrams.json').write_text(json.dumps(SCENES,ensure_ascii=False,indent=2)+'\n');(OUT/'dfd-balance.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');(OUT/'export-log.json').write_text(json.dumps(logs,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--drawio',required=True);a=p.parse_args();build(a.drawio)
