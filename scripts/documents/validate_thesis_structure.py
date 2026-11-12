"""Validate nine-chapter migration against its committed seven-chapter source."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/validation/thesis-structure-20261112'
PACK=ROOT/'docs/thesis/structure-20261112'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 baseline=json.loads((OUT/'baseline.json').read_text());mapping=json.loads((PACK/'migration-map.json').read_text())
 old=subprocess.check_output(['git','show',baseline['stage1_commit']+':docs/thesis/毕业论文.md'],cwd=ROOT).decode()
 new=(ROOT/'docs/thesis/毕业论文.md').read_text()
 allowed={'docs/thesis/毕业论文.md','docs/notes/HANDOFF.md','docs/notes/进度记录.md','scripts/documents/validate_requirements_review.py'}
 changed=[f for f,h in baseline['files'].items() if not (ROOT/f).exists() or sha(ROOT/f)!=h]
 assert set(changed)<=allowed,changed
 chapters=re.findall(r'^## ([1-9]) (.+)$',new,re.M);assert [a for a,b in chapters]==list('123456789')
 def body(s,a,b):return s[s.index(a):s.index(b)]
 assert body(old,'## 2 文献综述','## 3 系统需求分析')==body(new,'## 2 文献综述','## 3 系统需求分析')
 assert body(old,'## 3 系统需求分析','## 4 系统概要设计')==body(new,'## 3 系统需求分析','## 4 相关技术概述')
 assert old[old.index('## 参考文献'):]==new[new.index('## 参考文献'):]
 kept=[];missing=[]
 # Only abstracts and organizational outline were rewritten; original substantive paragraphs remain.
 source=body(old,'## 2 文献综述','## 参考文献')
 for paragraph in source.split('\n\n'):
  if not paragraph.strip() or paragraph.startswith('#') or paragraph.startswith('**图') or paragraph.startswith('**表') or paragraph.startswith('!['):continue
  text=re.sub(r'图\s*([456]\.\d+)',lambda m:'图 '+mapping['figure_numbers'].get(m[1],m[1]),paragraph)
  text=re.sub(r'表\s*([456]\.\d+)',lambda m:'表 '+mapping['table_numbers'].get(m[1],m[1]),text).replace('第 6.3 节','第7.3节')
  if text not in new:missing.append(paragraph[:100])
  else:kept.append(hashlib.sha256(paragraph.encode()).hexdigest())
 assert not missing,missing
 for item in mapping['assets']:
  a=ROOT/item['from'];b=ROOT/item['to'];assert sha(a)==item['source_sha256'] and sha(b)==item['target_sha256']
  if item['change']=='byte-identical':assert a.read_bytes()==b.read_bytes()
  else:
   x=json.loads(a.read_text());y=json.loads(b.read_text());x.pop('id');x.pop('caption');y.pop('id');y.pop('caption');assert x==y
 figures=re.findall(r'^\*\*图\s+(\d+\.\d+)\s+(.+?)\*\*$',new,re.M)
 tables=re.findall(r'^\*\*表\s+(\d+\.\d+)\s+(.+?)\*\*$',new,re.M)
 assert len(figures)==27 and len(tables)==21
 for kind,items in [('图',figures),('表',tables)]:
  ids=[a for a,b in items];assert len(set(ids))==len(ids)
  for chapter in {n.split('.')[0] for n in ids}:
   nums=[int(n.split('.')[1]) for n in ids if n.startswith(chapter+'.')];assert nums==list(range(1,len(nums)+1)),(kind,chapter,nums)
  for n in re.findall(kind+r'\s*(\d+\.\d+)',new):assert n in ids,(kind,n)
 images=re.findall(r'!\[([^\]]*)\]\(([^)]+)\)',new);assert len(images)==len(figures)
 inventory=[]
 for (alt,path),(number,caption) in zip(images,figures):
  image=ROOT/'docs/thesis'/path;assert image.exists();inventory.append({'figure':number,'caption':caption,'image':str(image.relative_to(ROOT)),'sha256':sha(image)})
 assert len(re.findall(r'^\|[^\n]*\| /api/',body(new,'**表 6.11','### 6.4'),re.M))==36
 assert len(re.findall(r'^\*\*表 6\.(?:[1-9]|10)　',new,re.M))==10
 fields=0
 for i in range(1,11):
  block=body(new,f'**表 6.{i}　',f'**表 6.{i+1}　')
  fields+=len(re.findall(r'^\| [a-z_]+ \|',block,re.M))
 assert fields==80,fields
 ids=re.findall(r'^\[(\d+)\]',new,re.M);assert ids==[str(i) for i in range(1,21)]
 assert not re.search(r'glm-\d|embedding-\d|deepseek-',new,re.I)
 assert all((ROOT/'docs/thesis'/x.split('#')[0]).exists() for x in re.findall(r'\]\(([^)]+)\)',new) if not x.startswith(('http:','https:','#')))
 result={'source_commit':baseline['stage1_commit'],'chapters':chapters,'preserved_paragraphs_or_tables':len(kept),'preserved_paragraph_sha256':kept,'literature_and_chapter3_unchanged':True,'references_and_acknowledgments_unchanged':True,'figures':inventory,'table_count':len(tables),'database_tables':10,'database_fields':fields,'controller_mappings':36,'reused_asset_files':len(mapping['assets']),'allowed_modified_stage1_files':changed,'protected_stage1_files':len(baseline['files'])-len(changed),'no_model_version_labels':True,'note':'No rendering claimed for unchanged inherited artwork; stage1 rendered evidence remains unchanged. No application tests executed.'}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['preserved_paragraphs_or_tables','table_count','database_tables','controller_mappings','reused_asset_files','protected_stage1_files']},ensure_ascii=False))
if __name__=='__main__':main()
