"""One-time, guarded alignment against the frozen opening report; no metadata changes."""
from pathlib import Path
import re,json,difflib,subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/notes/thesis-run-20260920'
def read(p):return (ROOT/p).read_text(encoding='utf-8-sig')
def write(name,s):(OUT/name).write_text(s,encoding='utf-8')
def main():
    p=ROOT/'docs/thesis/毕业论文.md'; old=p.read_text(encoding='utf-8')
    if '### 2.2 国内研究现状' in old: raise SystemExit('Already aligned; refusing to remap twice.')
    opening=read('docs/thesis/开题报告.md')
    refs={int(n):s for n,s in re.findall(r'^\[(\d+)\]\s*(.+)$',old,re.M)}
    oprefs={int(n):s for n,s in re.findall(r'^\[(\d+)\]\s*(.+)$',opening,re.M)}
    def norm(s):return re.sub(r'[\s*]','',s)
    mapping={i:next(j for j,t in refs.items() if norm(t)==norm(s)) for i,s in oprefs.items()}
    core=opening.split('## 二、文献综述\n')[1].split('## 三、研究内容')[0].strip()
    core=re.sub(r'\[(\d+)\]',lambda m:f'[{mapping[int(m[1])]}]',core)
    for n,title in enumerate(['前言','国内研究现状','国外研究现状','总结'],1):core=core.replace(f'**{title}**',f'### 2.{n} {title}')
    supplement='作为补充，吴永和等探讨多智能体教育应用[21]，本课题不实现该路线。贾洪愿等研究课程 RAG 知识库[22]，提示检索资源须匹配课程任务。唐颖川的 Python 课程研究[23]及张鲁燕、巩清波的“双师课堂”研究[24]强调教学情境，不能直接证明个人错题系统的教学效果。\n\n'
    core=core.replace('### 2.3 国外研究现状',supplement+'### 2.3 国外研究现状')
    new=old[:old.index('## 2 文献综述')]+ '## 2 文献综述\n\n'+core+'\n\n'+old[old.index('## 3 系统分析'):]
    body,tail=new.split('## 参考文献',1)
    # The citation tokenizer touches bracketed numeric references only, before bibliography.
    seen=[]
    for m in re.finditer(r'\[(\d+)\]',body):
        n=int(m[1]); assert n in refs
        if n not in seen:seen.append(n)
    assert set(seen)==set(refs)
    newno={n:i+1 for i,n in enumerate(seen)}
    body=re.sub(r'\[(\d+)\]',lambda m:f'[{newno[int(m[1])]}]',body)
    after='## 致'+tail.split('## 致',1)[1]
    new=body+'## 参考文献\n\n'+'\n\n'.join(f'[{newno[n]}] {refs[n]}' for n in seen)+'\n\n'+after
    new=new.replace('参考文献角标 [n] 与 `docs/references/gb7714-list.md` 顺序编码一致。','参考文献角标 [n] 按本文首次出现顺序排列；与主库的身份对应见 `../notes/thesis-run-20260920/REFERENCE-MAP.md`，主库编号保持不变。')
    p.write_text(new,encoding='utf-8')
    write('CHAPTER2-BEFORE.md',old[old.index('## 2 文献综述'):old.index('## 3 系统分析')])
    write('CHAPTER2-AFTER.md',new[new.index('## 2 文献综述'):new.index('## 3 系统分析')])
    write('THESIS-CHANGES.diff',''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='baseline/毕业论文.md',tofile='review/毕业论文.md')))
    bib=read('docs/references/references.bib')
    bibrows=re.findall(r'% \[(\d+)\]\s*@\w+\{([^,]+),(.*?)(?=\n% \[|\Z)',bib,re.S)
    bibmap={int(n):(key, re.search(r'year\s*=\s*\{(\d+)\}',fields)[1], (re.search(r'doi\s*=\s*\{([^}]+)\}',fields) or [None,'无'])[1]) for n,key,fields in bibrows}
    assert len(bibmap)==24
    rows=['# 文献身份映射\n\n原主库编号不变；新论文编号按首次引用生成。开题报告与系统填报稿未修改。\n','|开题编号|主库编号|论文新编号|BibTeX key|年份|DOI|文献|','|---|---|---|---|---|---|---|']
    for n in seen:
        k,y,d=bibmap[n]; o=next((str(i) for i,j in mapping.items() if j==n),'补充')
        rows.append(f'|{o}|{n}|{newno[n]}|{k}|{y}|{d}|{refs[n]}|')
    write('REFERENCE-MAP.md','\n'.join(rows)+'\n')
    write('reference-map.json',json.dumps(dict(opening_to_library=mapping,library_to_thesis=newno,bib=bibmap),ensure_ascii=False,indent=2))
    # Conservative count: Chinese characters; supplemental counts expose English/code inflation.
    stats={}
    for i in range(1,8):
        section=re.search(r'^## '+str(i)+r' .*?(?=^## |\Z)',new,re.S|re.M)[0]
        clean=re.sub(r'!\[[^]]*\]\([^)]+\)','',section)
        clean=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',clean)
        clean=re.sub(r'\[\d+\]|[#*`|]','',clean)
        stats[str(i)]=dict(chinese=len(re.findall(r'[\u4e00-\u9fff]',clean)),nonspace=len(re.sub(r'\s','',clean)))
    stats['total_chinese']=sum(v['chinese'] for v in stats.values())
    stats['body_3_to_6_chinese']=sum(stats[str(i)]['chinese'] for i in range(3,7))
    write('word-count.json',json.dumps(stats,ensure_ascii=False,indent=2))
    write('REFERENCE-AUDIT.md',f'''# 引用检查

2026-09-20；范围为本地作者现稿与已提供开题稿，不代表学校系统在线核对。

20 篇核心条目逐项以规范化完整题录匹配主库，全部唯一匹配；BibTeX key、年份、DOI见 REFERENCE-MAP。题录无新增疑点，本轮未重查出版商，也未改元数据。Zhao RAG采用2026期刊版。

新论文共有24篇，正文首引编号恰为1—24，文末24项唯一且无缺引。原主库和开题编号保留，论文独立编号。此次没有“仅限20篇”的明确要求，保留额外4篇既有用途，不为凑数增加条目。

|主库条目|原位置|新位置与处理理由|近三年计数影响|
|---|---|---|---|
|21 吴永和 2024|原2.3 多智能体讨论|2.2核心14篇后的补充段，界定多智能体未实现|保留+1|
|22 贾洪愿 2025|原2.3 教育RAG|同段，课程资源与个人题库差异|保留+1|
|23 唐颖川 2025|原2.3 Python课程|同段，课程情境约束|保留+1|
|24 张鲁燕 2026|原2.3 双师课堂|同段，人机教学分工边界|保留+1|

学校原规范写“近三年”但没有明确年份基点。按当前写作年2026的2024—2026口径：20篇核心12篇，24篇共16篇，满足15篇。若最终按毕业年2027的2025—2027口径，24篇仅6篇，需导师明确计年基点后补充真实相关研究；不擅自更改年份或宣称2027口径已达标。

综述汉字数{stats['2']['chinese']}，去空白字符数{stats['2']['nonspace']}（含英文术语、标点，不含链接路径和引用编号）。汉字口径处于2000—3000；最终校方系统统计仍须核验。核心14篇国内、6篇国外逐篇保留，4篇补充单独成段，不替换核心评述。

状态：内容与引用检查 done；最终提交年份口径 partial。未修改已提交开题材料。差异见 THESIS-CHANGES.diff。
''')
    print(json.dumps(stats,ensure_ascii=False))
if __name__=='__main__':main()
