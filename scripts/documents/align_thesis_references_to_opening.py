"""Keep the thesis reference identities and numbering identical to the opening report."""
from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'docs/notes/thesis-run-20260920'


def main():
    thesis=ROOT/'docs/thesis/毕业论文.md'
    original=thesis.read_text(encoding='utf-8')
    opening=(ROOT/'docs/thesis/开题报告.md').read_text(encoding='utf-8')
    pattern=r'^\[(\d+)\]\s*(.+)$'
    target=dict(re.findall(pattern,opening,re.M))
    current=dict(re.findall(pattern,original,re.M))
    assert list(target)==[str(i) for i in range(1,21)]
    norm=lambda s:re.sub(r'\s','',s)
    mapping={n:next(k for k,v in target.items() if norm(v)==norm(text))
             for n,text in current.items() if any(norm(text)==norm(v) for v in target.values())}
    assert len(mapping)==20
    extras=set(current)-set(mapping)
    body,tail=original.split('## 参考文献',1)
    if extras:
        paragraphs=body.split('\n\n')
        removed=[p for p in paragraphs if p.startswith('作为补充，') and set(re.findall(r'\[(\d+)\]',p))==extras]
        assert len(removed)==1,'Extra references require an explicit content review.'
        body='\n\n'.join(p for p in paragraphs if p not in removed)
        # These two broad background claims retain their already cited core
        # sources; never transfer the removed papers' specific claims to others.
        body=body.replace('相关技术有公开文档与既有研究可供参考[6][7][19]',
                          '相关技术有公开文档与既有研究可供参考[6][7]')
        body=body.replace('提供技术依据[4]-[7][14]-[19]',
                          '提供技术依据[4][6][7][14]')
    assert not(set(re.findall(r'\[(\d+)\]',body)) & extras)
    body=re.sub(r'\[(\d+)\]',lambda m:'['+mapping[m[1]]+']',body)
    body=re.sub(r'(?:\[\d+\]){2,}',lambda m:''.join(f'[{n}]' for n in sorted(map(int,re.findall(r'\d+',m[0])))),body)
    body=body.replace('参考文献角标 [n] 按本文首次出现顺序排列；','参考文献及正文角标 [n] 统一采用正式开题报告的20篇文献与编号顺序；')
    acknowledgment='## 致　谢'+tail.split('## 致　谢',1)[1]
    result=body+'## 参考文献\n\n'+'\n\n'.join(f'[{n}] {v}' for n,v in target.items())+'\n\n'+acknowledgment
    assert set(re.findall(r'\[(\d+)\]',body))==set(target)
    chapter2=body.split('## 2 文献综述',1)[1].split('## 3 系统分析',1)[0]
    assert re.findall(r'\[(\d+)\]',chapter2)==list(target)
    # Existing identity metadata is reused; the master reference library is an archive.
    rows=[]
    for line in (RUN/'REFERENCE-MAP.md').read_text(encoding='utf-8').splitlines():
        cells=line.strip('|').split('|')
        if len(cells)==7 and cells[0].isdigit():
            cells[2]=cells[0];cells[6]=target[cells[0]];rows.append(cells)
    rows.sort(key=lambda r:int(r[0]));assert len(rows)==20
    maptext='# 文献身份映射\n\n2026-09-22：按用户明确要求，论文仅使用正式开题报告的20篇文献，编号与顺序完全一致；正文按文献身份同步改号，不另按首次出现重新编号。开题报告和归档主库未改。\n\n'
    maptext+='|开题编号|主库编号|论文编号|BibTeX key|年份|DOI|文献|\n|---|---|---|---|---|---|---|\n'
    maptext+='\n'.join('|'+ '|'.join(r)+'|' for r in rows)+'\n'
    thesis.write_text(result,encoding='utf-8')
    (RUN/'REFERENCE-MAP.md').write_text(maptext,encoding='utf-8')
    years=[{'number':int(r[0]),'key':r[3],'year':int(r[4])} for r in rows]
    audit={'date':'2026-09-22','reference_count':20,'matches_opening_exactly':True,'chapter2_order':list(range(1,21)),
           'body_citations':len(re.findall(r'\[\d+\]',body)),'2024-2026':sum(2024<=r['year']<=2026 for r in years),
           '2025-2027':sum(2025<=r['year']<=2027 for r in years),'entries':years,
           'publication_metadata':'Reused existing identity map, not reverified online in this turn.'}
    (RUN/'opening-reference-check.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='entries'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
