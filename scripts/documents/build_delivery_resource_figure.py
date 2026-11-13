"""Render the additional implemented resource relationship; retain prior figure evidence."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import pymupdf
from delivery_svg_fonts import embed
from reportlab.pdfgen import canvas
import build_thesis_figures as renderer
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/thesis/delivery-20261112/figures'

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 scene={'id':'6-9','caption':'图 6.9　知识内容与个人资源关联','height':320,'ops':[]}
 ops=scene['ops']; boxes=[('u',14,10,'用户 user','id'),('q',260,10,'错题 question','id / user_id'),('l',260,210,'知识内容 learning_content','question_id（唯一）'),('k',14,210,'知识点 knowledge_point','id')]
 for _,x,y,title,detail in boxes:
  ops.extend([{'kind':'rect','x':x,'y':y,'w':172,'h':64},{'kind':'text','x':x+86,'y':y+25,'text':title,'size':10.5},{'kind':'text','x':x+86,'y':y+47,'text':detail,'size':10.5}])
 for pts in [[[186,42],[260,42]],[[346,74],[346,210]],[[186,242],[260,242]]]:ops.append({'kind':'line','points':pts})
 for x,y,t in [(202,35,'1'),(246,35,'N'),(357,91,'1'),(366,198,'0..1'),(202,234,'0..1'),(246,234,'N')]:ops.append({'kind':'text','x':x,'y':y,'text':t,'size':10.5})
 ops.append({'kind':'text','x':223,'y':305,'text':'逻辑关联；知识内容归属由原题与当前学生共同校验','size':10.5})
 (OUT/'6-9.json').write_text(json.dumps(scene,ensure_ascii=False,indent=2))
 (OUT/'6-9.svg').write_text(embed(renderer.svg(scene),scene))
 c=canvas.Canvas(str(OUT/'6-9.pdf'),pagesize=(595.2756,841.8898));renderer.render(scene,c,dx=77.95,top=735);renderer.draw_text(c,300,760,scene['caption'],10.5);c.save()
 # Crop for thesis insertion, retaining the standalone A4 PDF separately.
 c=canvas.Canvas(str(OUT/'6-9-crop.pdf'),pagesize=(renderer.WIDTH,320));renderer.render(scene,c);c.save()
 with pymupdf.open(OUT/'6-9-crop.pdf') as d:d[0].get_pixmap(matrix=pymupdf.Matrix(300/72,300/72)).save(OUT/'6-9.png')
 (OUT/'6-9-crop.pdf').unlink()
 root=ET.Element('mxfile',host='app.diagrams.net');dia=ET.SubElement(root,'diagram',id='resource',name='知识内容关联');model=ET.SubElement(dia,'mxGraphModel',page='1',pageWidth='827',pageHeight='1169');r=ET.SubElement(model,'root');ET.SubElement(r,'mxCell',id='0');ET.SubElement(r,'mxCell',id='1',parent='0')
 for id,x,y,title,detail in boxes:
  cell=ET.SubElement(r,'mxCell',id=id,value=title+'\n'+detail,style='rounded=0;whiteSpace=wrap;html=0;fillColor=#ffffff;strokeColor=#000000;fontColor=#000000;fontSize=15;',vertex='1',parent='1');ET.SubElement(cell,'mxGeometry',x=str(x*1.6),y=str(y*1.6),width='275',height='102',**{'as':'geometry'})
 for i,(a,b,label) in enumerate([('u','q','1 : N'),('q','l','1 : 0..1'),('k','l','0..1 : N')]):
  cell=ET.SubElement(r,'mxCell',id='e'+str(i),source=a,target=b,value=label,style='edgeStyle=orthogonalEdgeStyle;endArrow=none;startArrow=none;strokeColor=#000000;fontSize=15;',edge='1',parent='1');ET.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})
 ET.ElementTree(root).write(OUT/'6-9.drawio',encoding='utf-8',xml_declaration=True)
if __name__=='__main__':main()
