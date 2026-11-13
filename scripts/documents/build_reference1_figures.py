"""Reflow existing DFD vector operations without changing labels or graph semantics."""
from pathlib import Path
from copy import deepcopy
import os,json
from reportlab.pdfgen import canvas
import fitz
ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('THESIS_SONG_FONT',str(Path.home()/'.local/share/fonts/uming.ttc'))
os.environ.setdefault('THESIS_LATIN_FONT','/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf')
import build_thesis_figures as r
OUT=ROOT/'docs/thesis/align-reference1-20261113/figures'

def compact(scene):
    s=deepcopy(scene);intervals=[]
    for o in s['ops']:
        if o['kind'] in ['rect','ellipse']:intervals.append((o['y']-3,o['y']+o['h']+3))
        elif o['kind']=='text':intervals.append((o['y']-o['size']-2,o['y']+3))
        elif o['kind']=='line':
            for a,b in zip(o['points'],o['points'][1:]):
                if abs(a[1]-b[1])<.01:intervals.append((a[1]-3,a[1]+3))
    merged=[]
    for a,b in sorted(intervals):
        if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:merged.append((a,b))
    gaps=[(merged[i][1],merged[i+1][0]) for i in range(len(merged)-1) if merged[i+1][0]-merged[i][1]>14]
    low=merged[0][0]
    def y(v):
        return v-low+8-sum(max(0,min(v,b)-a)*((b-a-14)/(b-a)) for a,b in gaps)
    for o in s['ops']:
        if 'y' in o:
            old=o['y'];o['y']=y(old)
            if 'h' in o:o['h']=y(old+o['h'])-y(old)
        if 'points' in o:o['points']=[(x,y(v)) for x,v in o['points']]
    s['height']=y(merged[-1][1])+8
    assert [o['text'] for o in s['ops'] if o['kind']=='text']==[o['text'] for o in scene['ops'] if o['kind']=='text']
    return s,gaps

def write(s,key):
    s['id']=key
    (OUT/(key+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
    (OUT/(key+'.svg')).write_text(r.svg(s).replace('Times New Roman, SimSun, serif','Liberation Serif, Noto Serif CJK SC, serif'))
    path=OUT/(key+'.pdf');c=canvas.Canvas(str(path),pagesize=(r.WIDTH,s['height']));r.render(s,c);c.save()
    with fitz.open(path) as d:d[0].get_pixmap(dpi=240).save(OUT/(key+'.png'))

def main():
    OUT.mkdir(parents=True,exist_ok=True);report=[]
    for n in range(5,10):
        path=ROOT/f'docs/thesis/delivery-20261112/figures/3-{n}.json';source=json.loads(path.read_text());s,gaps=compact(source);write(s,f'3-{n}')
        report.append({'source':str(path.relative_to(ROOT)),'target':f'3-{n}','before_height_pt':source['height'],'after_height_pt':s['height'],'removed_blank_intervals':gaps,'text_order_unchanged':True,'graph_semantics':'Only coordinate transformation of vector operations; original DFD graph retained.'})
    # The original tall save/analyse sequence pushed its introduction onto a mostly empty page.
    path=ROOT/'docs/thesis/structure-20261112/figures/sources/6-6.json'
    source=json.loads(path.read_text());s,gaps=compact(source)
    for op in s['ops']:
        if 'y' in op:op['y']*=.8
        if 'h' in op:op['h']*=.8
        if 'points' in op:op['points']=[(x,y*.8) for x,y in op['points']]
    s['height']*=.8;write(s,'5-3')
    report.append({'source':str(path.relative_to(ROOT)),'target':'5-3','before_height_pt':source['height'],'after_height_pt':s['height'],'removed_blank_intervals':gaps,'text_order_unchanged':True,'graph_semantics':'Same participants, messages and vertical order; vertical spacing scaled 0.8, all font sizes unchanged.'})
    ops=[{'kind':'rect','x':143,'y':7,'w':160,'h':32}, {'kind':'text','x':223,'y':27,'text':'AI错题分析与学习推荐系统','size':10},
         {'kind':'line','points':[(223,39),(223,56)]},{'kind':'line','points':[(73,56),(373,56)]}]
    for x,title,items in [(3,'学生学习业务',['错题录入与编辑','AI分析与参考检索','知识内容与持续练习','复习计划与练习记录','学情查看与错题导出']),
                          (153,'公共与统计服务',['登录与个人资料','本人消息与公共公告','学生本人学情','教师系统聚合学情']),
                          (303,'管理员基础维护',['账号查询与停用','科目与知识点维护','公告发布'])]:
        ops.extend([{'kind':'line','points':[(x+70,56),(x+70,75)]},{'kind':'rect','x':x,'y':75,'w':140,'h':140},
                    {'kind':'text','x':x+70,'y':94,'text':title,'size':10},{'kind':'line','points':[(x,104),(x+140,104)]}])
        for j,t in enumerate(items):ops.append({'kind':'text','x':x+70,'y':123+j*18,'text':t,'size':9})
    write({'caption':'系统功能模块','height':225,'ops':ops},'5-2')
    # Teacher report belongs to the same report module; annotate explicitly rather than inventing a role workflow.
    (OUT/'provenance.json').write_text(json.dumps({'dfd_reflow':report,'module_figure':'Derived from controller roles and actual services; teacher reads system aggregate report, student reads own report.'},ensure_ascii=False,indent=2)+'\n')
    print([(x['target'],round(x['after_height_pt'],1)) for x in report])

if __name__=='__main__':main()
