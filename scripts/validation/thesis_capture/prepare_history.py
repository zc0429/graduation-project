"""Build one consistent isolated learning history through current business APIs.
Only chronology, teacher-role setup, and incomplete archived variant rows use SQL.
AI text comes from archive_replay; mastery/counts are never assigned manually.
"""
from pathlib import Path
from datetime import datetime,timedelta,date
import json, urllib.request, time, secrets, hashlib, sys
import pymysql
from archive_replay import corpus, MAIN, VARIANTS, ROOT, RUN
LOCAL=ROOT/'.local/thesis-screenshots-20261117'
BASE='http://127.0.0.1:8080/api'
TRACE=[]
def api(path,method='GET',data=None,token=None):
 h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 req=urllib.request.Request(BASE+path,data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,headers=h,method=method)
 with urllib.request.urlopen(req,timeout=45) as r:result=json.load(r)
 assert result['code']==0,(path,result)
 if '/auth/' not in path:TRACE.append({'method':method,'path':path,'code':0})
 return result['data']
def connect():
 env=dict(l.split('=',1) for l in (LOCAL/'database.env').read_text().splitlines())
 return pymysql.connect(host='127.0.0.1',port=3307,user='root',password=env['MYSQL_ROOT_PASSWORD'],database='thesis_capture',charset='utf8mb4',autocommit=True,cursorclass=pymysql.cursors.DictCursor)
def main():
 db=connect();cur=db.cursor();account=json.loads((LOCAL/'account.json').read_text());login=api('/auth/login','POST',account);token=login['token'];uid=login['user']['id']
 assert login['user']['nickname']=='赵灿' and login['user']['role']=='student'
 cur.execute('SELECT COUNT(*) AS n FROM question WHERE user_id=%s',(uid,));assert cur.fetchone()['n']==0,'Refuse to duplicate an existing history'
 excluded={'MATH-LINEAR-002','MATH-CONG-001','PHYSICS-FRIC-001','PHYSICS-N2-002','ENGLISH-TENSE-003'}
 rows=[c for c in corpus() if c['caseId'] not in excluded]
 assert len(rows)==23
 # Interleave subjects by date rather than creating blocks of all mathematics first.
 rows.sort(key=lambda c:hashlib.sha256(c['caseId'].encode()).hexdigest())
 rows.remove(MAIN);rows.insert(8,MAIN)
 ages=[26,25,23,22,21,20,18,17,16,15,14,12,11,10,9,8,7,6,4,3,2,1,0]
 today=date(2026,11,17);mapping=[]
 for i,(c,age) in enumerate(zip(rows,ages)):
  created=datetime.combine(today-timedelta(days=age),datetime.min.time()).replace(hour=17+i%4,minute=(13+i*11)%60,second=(7+i*17)%60)
  payload={'subjectId':c['subjectId'],'stem':c['stem'],'answer':c['correctAnswer'],'source':['课后习题订正','单元巩固练习','期中复习卷'][i%3]+' · '+['数学','物理','英语'][c['subjectId']-1]}
  qid=api('/question','POST',payload,token)
  # Preserve the actual five-stage plan offsets; only relocate the fixture calendar.
  cur.execute('UPDATE question SET create_time=%s,update_time=%s WHERE id=%s',(created,created,qid))
  cur.execute('UPDATE review_plan SET create_time=%s,plan_date=DATE_SUB(plan_date,INTERVAL %s DAY) WHERE question_id=%s',(created,age,qid))
  api(f'/ai/analyze/{qid}','POST',{},token)
  for _ in range(100):
   analysis=api(f'/ai/analysis/{qid}',token=token)
   if analysis and analysis['status']!=0:break
   time.sleep(.1)
  assert analysis['status']==1,(c['caseId'],analysis)
  assert analysis['analysis']==c['analysis']['analysis'],c['caseId']
  assert analysis['errorCause']==c['analysis']['errorCause'],c['caseId']
  cur.execute('UPDATE ai_analysis SET create_time=%s WHERE question_id=%s',(created+timedelta(minutes=2),qid))
  cur.execute('SELECT MAX(id) AS id FROM message WHERE user_id=%s',(uid,));message_id=cur.fetchone()['id']
  cur.execute('UPDATE message SET create_time=%s WHERE id=%s',(created+timedelta(minutes=2),message_id))
  mapping.append({'case_id':c['caseId'],'question_id':qid,'created_at':str(created),'source':c['source'],'source_pointer':c.get('source_pointer'),'expected_analysis':c['analysis'],'subject_id':c['subjectId'],'age_days':age,'input':payload})
  print('Archived analysis accepted:',c['caseId'],qid,flush=True)
 # Replay preserved variant stems; hidden answers were not archived and remain NULL.
 mainrow=next(m for m in mapping if m['case_id']==MAIN['caseId']);mainid=mainrow['question_id']
 for stem in VARIANTS:
  cur.execute('INSERT INTO variant_question(question_id,stem,answer,difficulty,create_time) VALUES(%s,%s,NULL,3,%s)',(mainid,stem,mainrow['created_at']))
 # Main question is replayed again after the corpus exists so displayed references
 # are actual same-account IDs returned by current RagService over the local index.
 api(f'/ai/analyze/{mainid}','POST',{},token)
 for _ in range(100):
  a=api(f'/ai/analysis/{mainid}',token=token)
  if a and a['status']==1:break
  time.sleep(.1)
 assert a['analysis']==MAIN['analysis']['analysis'] and json.loads(a['referenceIds'])
 cur.execute('UPDATE ai_analysis SET create_time=%s WHERE question_id=%s',(mainrow['created_at'],mainid))
 knowledge=api(f'/learning/knowledge/{mainid}','POST',{},token)
 assert knowledge['content']==MAIN['analysis']['analysis'] and not knowledge['reused']
 assert api(f'/learning/knowledge/{mainid}','POST',{},token)['reused']
 cur.execute('UPDATE learning_content SET create_time=%s,update_time=%s WHERE question_id=%s',(mainrow['created_at'],mainrow['created_at'],mainid))
 # Actual original-question submissions derive every mastery value via +15/-20.
 patterns={1:[[0,1,1,1],[1,1,0,1,1]],2:[[1,1,1,1],[1,1,1,0,1,1,1,0,1]],3:[[1,1,1,0,1,1,1,1],[1,1,1,0,1,1,1,0,1,1]]}
 for i,m in enumerate(mapping):
  c=next(c for c in rows if c['caseId']==m['case_id']);seq=patterns[c['subjectId']][i%2]
  if m['age_days']<2:seq=[0,1] if m['age_days']==1 else [0]
  if m['case_id']==MAIN['caseId']:seq=[1,1,1,0,1,1,1,0,1]
  original=api(f"/learning/practice/next/{m['question_id']}",'POST',{},token);assert original['source']=='original'
  for j,correct in enumerate(seq):
   pid=api('/practice','POST',{'questionId':m['question_id'],'isCorrect':correct,'userAnswer':c['correctAnswer'] if correct else c['wrongAnswer'],'duration':57+(i*23+j*37)%189},token)
   # Chronological replay spans the question's life, ending on the capture day.
   base=datetime.fromisoformat(m['created_at']);span=(datetime(2026,11,17,19,20)-base).total_seconds()
   stamp=base+timedelta(seconds=max(180,span*(j+1)/(len(seq)+1)))
   cur.execute('UPDATE practice_record SET create_time=%s WHERE id=%s',(stamp,pid))
  cur.execute('UPDATE question SET update_time=%s WHERE id=%s',(stamp,m['question_id']))
 # Complete prior stages via the actual finish endpoint; leave only two past-due
 # rows and some current/future work. Finish dates retain planned sequence.
 cur.execute('SELECT * FROM review_plan WHERE user_id=%s ORDER BY plan_date,id',(uid,));plans=cur.fetchall();overdue=[]
 for p in plans:
  if p['plan_date']<today and p['plan_date']>=today-timedelta(days=3) and len(overdue)<2:
   overdue.append(p['id']);continue
  if p['plan_date']<today or (p['plan_date']==today and p['id']%3==0):
   api(f"/review-plan/{p['id']}/finish",'PUT',{},token)
   finish=datetime.combine(p['plan_date'],datetime.min.time()).replace(hour=19+p['id']%2,minute=p['id']*7%60)
   cur.execute('UPDATE review_plan SET finish_time=%s WHERE id=%s',(finish,p['id']))
 # Apply the existing daily scheduler's overdue transition to replay chronology.
 cur.execute('UPDATE review_plan SET status=2 WHERE user_id=%s AND status=0 AND plan_date<%s',(uid,today))
 report=api('/report/generate','POST',{},token)
 messages=api('/message/page?pageSize=100',token=token)['records']
 for m in messages[3:]:api(f"/message/{m['id']}/read",'PUT',{},token)
 # Existing teacher account is renamed in this isolated DB; no production data.
 teacherfile=LOCAL/'teacher.json'
 teacher={'username':'hutaoteacher','password':secrets.token_urlsafe(16),'nickname':'胡韬'}
 tid=api('/auth/register','POST',teacher);cur.execute("UPDATE user SET role='teacher' WHERE id=%s",(tid,))
 teacherfile.write_text(json.dumps(teacher,ensure_ascii=False));teacherfile.chmod(0o600)
 t=api('/auth/login','POST',teacher);teacher_report=api('/report/weekly',token=t['token'])
 assert {**teacher_report,'knowledgeMastery':sorted(teacher_report['knowledgeMastery'],key=lambda x:x['knowledgePointId'])}=={**report,'knowledgeMastery':sorted(report['knowledgeMastery'],key=lambda x:x['knowledgePointId'])},'Teacher aggregate must equal this isolated single-student corpus'
 cur.execute('SELECT subject_id,COUNT(*) AS count,ROUND(AVG(mastery),1) AS mastery FROM question WHERE user_id=%s GROUP BY subject_id',(uid,));subjects=cur.fetchall()
 cur.execute('SELECT COUNT(*) AS count,SUM(is_correct) AS correct,MIN(create_time) AS first,MAX(create_time) AS last FROM practice_record WHERE user_id=%s',(uid,));practices=cur.fetchone()
 cur.execute('SELECT status,COUNT(*) AS count FROM review_plan WHERE user_id=%s GROUP BY status',(uid,));reviews=cur.fetchall()
 record={'system_commit':'bb7bc56e449ab8168fcb4cb87879e71b0a3ca41c','capture_date':str(today),'student':{'id':uid,'nickname':'赵灿','role':'student'},'teacher':{'id':tid,'nickname':'胡韬','role':'teacher'},'questions':mapping,'main_question_id':mainid,'subjects':subjects,'practice_summary':practices,'review_summary':reviews,'student_report':report,'teacher_report':teacher_report,'same_aggregate':True,'generation':'Current branch HTTP business APIs plus explicitly recorded archive/chronology imports','sql_exceptions':['Relocate fixture dates across 2026-10-22..2026-11-17; never overwrite mastery/counts','Import 3 archived variant stems/difficulty; unarchived answers NULL','Apply existing overdue status rule to historical calendar','Assign named teacher role in isolated database'],'model':'Archived GLM only; local replay endpoint; no external calls','embedding':'Local deterministic replay index; not original embedding-3 vectors','knowledge':'Verbatim archived analysis reused as content; no newly authored AI text','variants_source':'docs/thesis/screenshots/real-glm/08-variants.png','http_trace':TRACE}
 (RUN/'business-history.json').write_text(json.dumps(record,ensure_ascii=False,indent=2,default=str)+'\n')
 print(json.dumps({k:record[k] for k in ['subjects','practice_summary','review_summary','main_question_id']},ensure_ascii=False,default=str))
if __name__=='__main__':main()
