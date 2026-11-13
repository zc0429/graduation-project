"""Capture a separate real-DB API trace, explicitly using Mock (not a new GLM experiment)."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json, subprocess

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'docs/validation/thesis-align-reference1-20261113'
BASE='http://127.0.0.1:8080/api'

def call(path, method='GET', data=None, token=None):
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    req=Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=headers,method=method)
    try:
        with urlopen(req,timeout=20) as r:return r.status,json.load(r)
    except HTTPError as e:return e.code,json.loads(e.read())

def snapshot(qid):
    query=f"SELECT (SELECT COUNT(*) FROM learning_content WHERE question_id={qid}) AS knowledge_rows,(SELECT COUNT(*) FROM variant_question WHERE question_id={qid}) AS variant_rows,(SELECT COUNT(*) FROM practice_record p LEFT JOIN variant_question v ON p.variant_id=v.id WHERE p.question_id={qid} OR v.question_id={qid}) AS practice_rows,(SELECT COUNT(*) FROM review_plan WHERE question_id={qid}) AS plan_rows,(SELECT mastery FROM question WHERE id={qid}) AS mastery;"
    cmd=['docker','--host=unix:///var/run/docker.sock','exec','thesis-align-mysql-20261113','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot --batch wrongbook_browser -e "$1"','sh',query]
    lines=subprocess.check_output(cmd,text=True).splitlines()
    return dict(zip(lines[0].split('\t'),map(int,lines[1].split('\t'))))

def main():
    _,login=call('/auth/login','POST',{'username':'student','password':'123456'})
    token=login['data']['token'];rows=[]
    _,created=call('/question','POST',{'subjectId':1,'stem':'求函数 y=x² 在区间 [0,2] 上的值域。','answer':'[0,4]','source':'2026-11-13 专项API回读，显式Mock'},token)
    qid=created['data']
    def record(step,response):rows.append({'step':step,'response':response,'database':snapshot(qid)})
    try:
        record('创建原题',{'questionId':qid})
        _,a=call(f'/learning/knowledge/{qid}','POST',{},token);assert not a['data']['reused'];record('首次知识请求',{'reused':a['data']['reused']})
        _,a=call(f'/learning/knowledge/{qid}','POST',{},token);assert a['data']['reused'];record('再次知识请求',{'reused':a['data']['reused']})
        _,a=call(f'/learning/practice/next/{qid}','POST',{},token);assert a['data']['source']=='original';record('获取未练原题',{'source':a['data']['source'],'questionId':a['data']['questionId'],'variantId':a['data']['variantId']})
        _,a=call('/practice','POST',{'questionId':qid,'isCorrect':0,'userAnswer':'专项自评：答错'},token);assert a['code']==0;record('原题答错提交',{'code':a['code']})
        _,a=call(f'/learning/practice/next/{qid}','POST',{},token);assert a['data']['source']=='generated';first=a['data']['variantId'];record('首次补充变式',{'source':a['data']['source'],'variantId':first})
        _,a=call(f'/learning/practice/next/{qid}','POST',{},token);assert a['data']['source']=='existing' and a['data']['variantId']==first;record('重复获取未提交题',{'source':a['data']['source'],'variantId':a['data']['variantId']})
        _,a=call(f'/variant/list?questionId={qid}',token=token);assert len(a['data'])==3
        for v in a['data']:
            _,saved=call('/practice','POST',{'variantId':v['id'],'isCorrect':0},token);assert saved['code']==0
        record('三道变式全部提交',{'submitted':3})
        _,a=call(f'/learning/practice/next/{qid}','POST',{},token);assert a['data']['source']=='generated';record('耗尽后继续',{'source':a['data']['source'],'variantId':a['data']['variantId']})
        _,a=call('/practice','POST',{'questionId':qid,'isCorrect':1},token);assert a['code']==0;record('主动重做原题',{'code':a['code']})
        final=snapshot(qid);assert final=={'knowledge_rows':1,'variant_rows':6,'practice_rows':5,'plan_rows':5,'mastery':15},final
        (RUN/'learning-cycle-trace.json').write_text(json.dumps({'date':'2026-11-13','model':'explicit Mock','scope':'One independent API trace with database snapshots; not added to browser test counts','question_id':qid,'steps':rows,'assertions_passed':True},ensure_ascii=False,indent=2)+'\n')
        print('Trace saved: 10 states, real database, Mock model; no credentials logged.')
    finally:
        call(f'/question/{qid}','DELETE',token=token)

if __name__=='__main__':main()
