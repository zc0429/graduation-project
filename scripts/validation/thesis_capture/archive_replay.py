"""Local-only replay of committed GLM responses. Never calls a model service.

Knowledge content reuses the archived analysis verbatim. Embeddings are a local
index for navigating the replay corpus, NOT historical embedding-3 outputs.
Unknown questions/tasks fail closed; no answer or analysis is synthesized.
"""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json, hashlib, os
ROOT=Path(__file__).resolve().parents[3]
ARCHIVE=ROOT/'docs/experiments/gate5/results/experiment-results.json'
RUN=ROOT/'docs/validation/thesis-screenshots-20261117'
MAIN={
 'caseId':'BROWSER-GLM-225','subjectId':1,'expectedKnowledgePointId':3,
 'stem':'已知二次函数 y=x²-6x+5，学生配方后写成 y=(x-3)²+5，并判断顶点为 (3,5)。求正确顶点与最小值，并分析这一步错在哪里。',
 'correctAnswer':'y=(x-3)²-4，所以顶点为 (3,-4)，最小值为 -4；错误是配方时遗漏了补入 9 后应减去 9。',
 'wrongAnswer':'顶点为 (3,5)，最小值为5。',
 'analysis':{'predictedKnowledgePointId':3,'difficulty':3,'llmModel':'glm-4.7-flash',
 'errorCause':'配方时遗漏了补入 9 后应减去 9',
 'analysis':'正确配方应为 y=x²-6x+9-9+5=(x-3)²-4，因此顶点坐标为 (3,-4)，最小值为 -4。学生错误地将常数项 5 直接保留在完全平方项之后，导致顶点纵坐标计算错误。'},
 'source':'docs/thesis/screenshots/real-glm/05-question-detail-glm.png',
 'source_kind':'verbatim visual transcription; inputs also retained in web/e2e/real-ai/real-glm-evidence.spec.ts'}
VARIANTS=[
 '已知二次函数 y=x²+4x+3，学生配方后写成 y=(x+2)²+3，并判断顶点为 (-2,3)。求正确顶点与最小值，并分析这一步错在哪里。',
 '已知二次函数 y=x²-8x+12，学生配方后写成 y=(x-4)²+12，并判断顶点为 (4,12)。求正确顶点与最小值，并分析这一步错在哪里。',
 '已知二次函数 y=x²+2x-3，学生配方后写成 y=(x+1)²-3，并判断顶点为 (-1,-3)。求正确顶点与最小值，并分析这一步错在哪里。']
def corpus():
 data=json.loads(ARCHIVE.read_text())
 rows=[dict(c['dataset'],analysis=c['analysis'],source=str(ARCHIVE.relative_to(ROOT)),source_pointer=f"/cases/{i}/analysis") for i,c in enumerate(data['cases'])]
 return rows+[MAIN]
def locate(text):
 matches=[c for c in corpus() if c['stem'] in text]
 return min(matches,key=lambda c:text.index(c['stem'])) if matches else None
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  if self.headers.get('Transfer-Encoding','').lower()=='chunked':
   data=b''
   while True:
    size=int(self.rfile.readline().split(b';')[0],16)
    if not size:
     self.rfile.readline();break
    data+=self.rfile.read(size);self.rfile.read(2)
  else:data=self.rfile.read(int(self.headers.get('Content-Length',0)))
  req=json.loads(data)
  try:
   if self.path.endswith('/embeddings'):
    c=locate(req['input']);assert c,'Question absent from archive'
    vector=[0.0]*1024
    vector[c['subjectId']]=0.2;vector[c['analysis']['predictedKnowledgePointId']+32]=1.0
    # Deterministic local index only; not saved or represented as a GLM vector.
    result={'model':'archive-replay-index','data':[{'embedding':vector}]};kind='local_index'
   elif self.path.endswith('/chat/completions'):
    prompt=req['messages'][-1]['content'];c=locate(prompt);assert c,'Question absent from archive'
    if '【任务：知识学习】' in prompt or '一个字符串字段content' in prompt:
     result_body={'content':c['analysis']['analysis']};kind='knowledge_reuses_archived_analysis'
    elif 'knowledgePointId' in prompt:
     a=c['analysis'];result_body={'knowledgePointId':a['predictedKnowledgePointId'],'errorCause':a['errorCause'],'analysis':a['analysis'],'difficulty':a['difficulty']};kind='analysis'
    else:raise ValueError('No complete archived response for requested task; replay denied')
    result={'model':'glm-4.7-flash','choices':[{'message':{'content':json.dumps(result_body,ensure_ascii=False)}}]}
   else:raise ValueError('Unknown endpoint')
   body=json.dumps(result,ensure_ascii=False).encode();status=200
   with (RUN/'replay-requests.jsonl').open('a') as f:f.write(json.dumps({'task':kind,'case_id':c['caseId'],'source':c['source'],'response_sha256':hashlib.sha256(body).hexdigest()},ensure_ascii=False)+'\n')
  except Exception as e:
   status=422;body=json.dumps({'error':str(e)}).encode()
  self.send_response(status);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
if __name__=='__main__':
 RUN.mkdir(parents=True,exist_ok=True)
 print('Archive replay listening on 127.0.0.1:8091; no external network calls',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8091),Handler).serve_forever()
