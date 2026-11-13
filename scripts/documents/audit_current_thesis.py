"""Reconcile all DDL columns/constraints/indexes and controller mappings with chapter 6."""
from pathlib import Path
import re,json,hashlib,subprocess
from collections import Counter
from validate_thesis_references import validate
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/validation/thesis-audit-20261112'
def normalize(s):return re.sub(r'\s+',' ',s.strip()).replace('`','')
def main():
 md=(ROOT/'docs/thesis/毕业论文.md').read_text();sql=(ROOT/'server/src/main/resources/db/schema.sql').read_text();tables=[]
 for m in re.finditer(r'CREATE TABLE IF NOT EXISTS `(\w+)` \((.*?)\) ENGINE[^;]+;',sql,re.S):
  name,body=m.groups();unique=re.findall(r'UNIQUE KEY \w+ \((\w+)\)',body);fields=[]
  for line in body.splitlines():
   f=re.match(r'\s*`?(\w+)`?\s+(BIGINT|VARCHAR\(\d+\)|CHAR\(\d+\)|TINYINT|INT|TEXT|DATETIME|DATE)\s+(.+)',line)
   if not f:continue
   key,typ,rest=f.groups();constraint=normalize(rest.split(' COMMENT ')[0].rstrip(','))
   if key=='id':constraint='PRIMARY KEY '+constraint
   if key in unique:constraint+=' UNIQUE'
   fields.append({'name':key,'type':typ,'constraint':constraint})
  section=re.search(r'\*\*表 6\.\d+[^\n]*（'+name+r'）\*\*(.*?)(?=\n\*\*表|\n###|\n\*\*（11）)',md,re.S)
  assert section,name
  rows=re.findall(r'^\| ([a-z_]+) \| ([^|]+) \| ([^|]+) \|',section[1],re.M)
  assert [(n,normalize(t),normalize(c)) for n,t,c in rows]==[(f['name'],f['type'],f['constraint']) for f in fields],(name,rows,fields)
  indexes=re.findall(r'(?:UNIQUE )?KEY \w+ \([^)]+\)',body)
  for idx in indexes:assert normalize(idx) in normalize(section[1]),(name,idx)
  tables.append({'name':name,'fields':fields,'indexes':indexes})
 assert len(tables)==11 and sum(len(t['fields']) for t in tables)==88
 from audit_thesis_figures import baseline
 endpoints=baseline()['endpoints'];assert len(endpoints)==39
 listed=set(re.findall(r'\| (GET|POST|PUT|DELETE) \| (/api/[^ |]+) \|',md));assert listed=={(e['method'],e['path']) for e in endpoints}
 labels={('public',):'公开',('authenticated',):'登录用户',('student',):'学生',('admin',):'管理员',('student','teacher'):'学生、教师'}
 for e in endpoints:
  row=re.search(r'\| '+e['method']+r' \| '+re.escape(e['path'])+r' \| ([^\n]+)',md)[1]
  assert '权限：'+labels[tuple(e['roles'])] in row,e
 assert sum(e['roles']==['public'] for e in endpoints)==3
 from build_requirements_review import balance,SCENES
 dfd=balance();assert all(v['balanced'] for v in dfd.values())
 for s in SCENES:
  nodes={x['id']:x for x in s['nodes']}
  for e in s['edges']:
   assert e['source'] in nodes and e['target'] in nodes
   if s['kind']=='dfd':assert any(nodes[e[k]]['kind']=='process' for k in ['source','target'])
 for target in re.findall(r'!\[[^]]*\]\(([^)]+)\)',md):assert (ROOT/'docs/thesis'/target).is_file(),target
 for kind in ['图','表']:
  nums=re.findall(r'^\*\*'+kind+r' (\d+)\.(\d+)',md,re.M)
  for ch in set(x[0] for x in nums):assert [int(n) for c,n in nums if c==ch]==list(range(1,sum(c==ch for c,n in nums)+1))
 # Compare immutable historical inputs/artifacts against the user's explicit baseline.
 tracked=subprocess.check_output(['git','ls-tree','-rz','--name-only','ed7d94c'],cwd=ROOT).decode().split('\0');protected={}
 for path in tracked:
  if path.startswith(('docs/materials/','docs/experiments/','output/','docs/thesis/requirements-20261112/','docs/thesis/delivery-20261112/','docs/thesis/screenshots/')) or path=='docs/thesis/开题报告.md':
   original=subprocess.check_output(['git','show','ed7d94c:'+path],cwd=ROOT)
   assert (ROOT/path).read_bytes()==original,('Protected original changed',path)
   protected[path]=hashlib.sha256(original).hexdigest()
 result={'baseline_commit':'ed7d94c','tables':tables,'table_count':len(tables),'field_count':sum(len(t['fields']) for t in tables),'endpoints':endpoints,'endpoint_count':len(endpoints),'public_endpoints':3,'authenticated_endpoints':36,'dfd_balance':dfd,'references':validate(),'protected_files':protected,'checked':'全部字段名称、类型、主键、非空、默认值、自增、唯一与普通索引；全部控制器路径方法及角色；DFD父子边界字段；图表编号与文件；受保护历史文件字节一致'}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'code-thesis-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['table_count','field_count','endpoint_count','public_endpoints','authenticated_endpoints']},ensure_ascii=False),'protected',len(protected))
if __name__=='__main__':main()
