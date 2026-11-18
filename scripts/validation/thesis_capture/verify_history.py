"""Read back database, original GLM archive and current role-scoped API aggregates."""
import json,hashlib
from datetime import date
from prepare_history import *
def canonical(r):
 return {**r,'knowledgeMastery':sorted(r['knowledgeMastery'],key=lambda x:x['knowledgePointId']),'weakPoints':sorted(r['weakPoints'],key=lambda x:x['knowledgePointId'])}
def verify():
 cur=connect().cursor();s=api('/auth/login','POST',json.loads((LOCAL/'account.json').read_text()));t=api('/auth/login','POST',json.loads((LOCAL/'teacher.json').read_text()));uid=s['user']['id']
 student=api('/report/weekly',token=s['token']);teacher=api('/report/weekly',token=t['token']);assert canonical(student)==canonical(teacher)
 qpage=api('/question/page?pageSize=100',token=s['token']);cur.execute('SELECT * FROM question WHERE user_id=%s AND status=1 ORDER BY id',(uid,));questions=cur.fetchall()
 assert len(questions)==qpage['total']==student['totalQuestionCount']==23
 allcases=corpus();mapping=[]
 for q in questions:
  c=next(c for c in allcases if c['stem']==q['stem']);cur.execute('SELECT * FROM ai_analysis WHERE question_id=%s',(q['id'],));a=cur.fetchone()
  assert a['status']==1 and a['analysis']==c['analysis']['analysis'] and a['error_cause']==c['analysis']['errorCause']
  cur.execute('SELECT * FROM practice_record WHERE question_id=%s OR variant_id IN (SELECT id FROM variant_question WHERE question_id=%s) ORDER BY id',(q['id'],q['id']));records=cur.fetchall();mastery=0
  for r in records:mastery=max(0,min(100,mastery+(15 if r['is_correct'] else -20)));assert r['user_id']==uid
  assert mastery==q['mastery'],(q['id'],mastery,q['mastery'])
  cur.execute('SELECT * FROM review_plan WHERE question_id=%s ORDER BY review_stage',(q['id'],));plans=cur.fetchall();assert len(plans)==5
  assert [(p['plan_date']-q['create_time'].date()).days for p in plans]==[1,2,4,7,15]
  mapping.append({'case_id':c['caseId'],'question_id':q['id'],'subject_id':q['subject_id'],'created_at':q['create_time'],'mastery':mastery,'practice_count':len(records),'archive':c['source'],'archive_pointer':c.get('source_pointer'),'analysis_sha256':hashlib.sha256(a['analysis'].encode()).hexdigest(),'error_cause_sha256':hashlib.sha256(a['error_cause'].encode()).hexdigest(),'reference_ids':json.loads(a['reference_ids'] or '[]'),'input':{'stem':q['stem'],'answer':q['answer'],'source':q['source']}})
 main=next(m for m in mapping if m['case_id']==MAIN['caseId']);mid=main['question_id']
 cur.execute('SELECT * FROM variant_question WHERE question_id=%s ORDER BY id',(mid,));variants=cur.fetchall();assert [v['stem'] for v in variants]==VARIANTS;assert all(v['answer'] is None and v['difficulty']==3 for v in variants)
 cur.execute('SELECT * FROM learning_content WHERE question_id=%s',(mid,));k=cur.fetchone();assert k['content']==MAIN['analysis']['analysis']
 cur.execute('SELECT subject_id,COUNT(*) AS count,ROUND(AVG(mastery),1) AS mastery FROM question WHERE user_id=%s AND status=1 GROUP BY subject_id',(uid,));subjects=cur.fetchall()
 cur.execute('SELECT COUNT(*) AS count,SUM(is_correct) AS correct,MIN(create_time) AS first,MAX(create_time) AS last FROM practice_record WHERE user_id=%s',(uid,));practices=cur.fetchone()
 cur.execute('SELECT status,COUNT(*) AS count FROM review_plan WHERE user_id=%s GROUP BY status',(uid,));reviews=cur.fetchall();assert {r['status'] for r in reviews}=={0,1,2}
 cur.execute('SELECT is_read,COUNT(*) AS count FROM message WHERE user_id=%s GROUP BY is_read',(uid,));messages=cur.fetchall();assert {m['is_read'] for m in messages}=={0,1}
 # AI completion message chronology follows its parent question, while report
 # generation keeps its actual capture-day timestamp.
 refs=main['reference_ids'];assert refs and all(r in [q['id'] for q in questions] and r!=mid for r in refs)
 for r in refs:assert next(q for q in questions if q['id']==r)['subject_id']==1
 sources=['docs/experiments/gate5/results/experiment-results.json',MAIN['source'],'docs/thesis/screenshots/real-glm/08-variants.png','web/e2e/real-ai/real-glm-evidence.spec.ts']
 record={'system_commit':'bb7bc56e449ab8168fcb4cb87879e71b0a3ca41c','system_branch':'claude/thesis-voice-cleanup-20261117','capture_date':'2026-11-17','student':{'id':uid,'nickname':'赵灿','role':'student'},'teacher':{'id':t['user']['id'],'nickname':'胡韬','role':'teacher'},'main_question_id':mid,'questions':mapping,'subjects':subjects,'practice_summary':practices,'review_summary':reviews,'message_summary':messages,'student_report':student,'teacher_report':teacher,'same_aggregate':True,'all_mastery_recomputed_from_submissions':True,'all_ai_text_equals_archive':True,'sources':[{ 'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in sources], 'generation':'Actual current-branch HTTP create/analyze/knowledge/practice/review/report flows; local-only archived GLM response gateway','chronology':'Isolated replay fixture relocated to 2026-10-22..2026-11-17; not a claim of actual weeks of human use','sql_exceptions':['Fixture creation/finish dates relocated; fixed plan offsets retained','Three archived variant stems/difficulty imported, unarchived answers NULL','Existing overdue rule applied to replay dates','Named teacher role assigned in isolated database'],'ai_source':'Original Gate5 JSON and exact historical browser screenshot transcription; no new calls or authored AI text','knowledge_source':'Archived analysis copied verbatim as cached knowledge content','embedding_source':'Local deterministic replay index, not historical embedding-3 vectors; current RAG returns real IDs from this same account','variant_answers':'Not preserved in original screenshot; NULL, not reconstructed','business_source_changes':[],'passed':True}
 (RUN/'business-history.json').write_text(json.dumps(record,ensure_ascii=False,indent=2,default=str)+'\n')
 print(json.dumps({k:record[k] for k in ['subjects','practice_summary','review_summary','message_summary','main_question_id','passed']},ensure_ascii=False,default=str))
if __name__=='__main__':verify()
