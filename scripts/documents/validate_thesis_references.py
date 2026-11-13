"""Check audited bibliography, citation order and the protected approved proposal."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[2]
def validate():
 data=json.loads((ROOT/'docs/references/reference-audit-20261113.json').read_text())
 md=(ROOT/'docs/thesis/毕业论文.md').read_text();records=data['records']
 actual=re.findall(r'^\[(\d+)\]\s*(.+)$',md,re.M)
 expected=[(str(x['number']),x['entry']) for x in records]
 assert actual==expected,'Manuscript and verified metadata differ'
 assert actual==re.findall(r'^\[(\d+)\]\s*(.+)$',(ROOT/'docs/references/gb7714-list.md').read_text(),re.M)
 assert [x['number'] for x in records]==list(range(1,len(records)+1))
 body=re.sub(r'```.*?```','',md.split('## 参考文献')[0],flags=re.S)
 citations=[int(n) for n in re.findall(r'\[(\d+)\]',body)]
 first=list(dict.fromkeys(citations));assert first==list(range(1,len(records)+1)),first
 assert hashlib.sha256((ROOT/'docs/thesis/开题报告.md').read_bytes()).hexdigest()==data['opening_report_sha256']
 bib=(ROOT/'docs/references/references.bib').read_text()
 blocks=re.findall(r'@\w+\{.*?\n\}',bib,re.S);assert len(blocks)==len(records)
 for rec,block in zip(records,blocks):
  assert re.search(r'\{([^,]+)',block)[1]==rec['key']
  assert int(re.search(r'year\s*=\s*\{(\d+)',block)[1])==rec['year']
  assert rec['source_url'].startswith('https://') and rec['citation_sections']
 counts={'total':len(records),'2024-2026':sum(2024<=x['year']<=2026 for x in records),'2025-2027_published_by_audit':sum(2025<=x['year']<=2026 for x in records),'foreign_language':sum(x['language']=='foreign' for x in records),'citation_first_appearance':first,'opening_report_unchanged':True}
 assert 25<=counts['total']<=28 and counts['2024-2026']>=15 and counts['2025-2027_published_by_audit']>=15 and counts['foreign_language']>=2
 languages=[x['language'] for x in records]
 assert languages==sorted(languages,key=lambda x:0 if x=='zh' else 1),'Chinese sources must precede foreign sources'
 counts['chinese_first']=True
 return counts
if __name__=='__main__':print(json.dumps(validate(),ensure_ascii=False,indent=2))
