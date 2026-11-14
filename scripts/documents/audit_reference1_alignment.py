"""Record immutable inputs and actual PDF chapter/figure distributions before editing."""
from pathlib import Path
import hashlib, json, re, subprocess
import fitz

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'docs/validation/thesis-align-reference1-20261113'
BASE = 'bbe1c5104ad6db8fea0a0294c6921d63b86cd1ff'

def norm(s):
    return re.sub(r'\s+', '', s)

def inventory(path):
    doc = fitz.open(path)
    headings = []
    for i, page in enumerate(doc):
        text = page.get_text(sort=True)
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        for line in lines[:8]:
            m = re.fullmatch(r'([1-9])\s+([^\d.]{2,35})', line)
            if m and not any(c in line for c in '.…'):
                if not any(h['chapter'] == int(m[1]) for h in headings):
                    headings.append({'chapter': int(m[1]), 'title': m[2], 'pdf_start': i + 1})
    assert [h['chapter'] for h in headings] == list(range(1, 10)), headings
    start = headings[0]['pdf_start']
    refs = next(i + 1 for i in range(headings[-1]['pdf_start'], len(doc))
                if any(norm(x) == '参考文献' for x in doc[i].get_text(sort=True).splitlines()[:7]))
    for k, h in enumerate(headings):
        end = headings[k + 1]['pdf_start'] if k < 8 else refs
        h['body_start'] = h['pdf_start'] - start + 1
        h['pages'] = end - h['pdf_start']
        text = '\n'.join(doc[i].get_text() for i in range(h['pdf_start'] - 1, end - 1))
        h['figures'] = sorted(set(re.findall(r'图\s*' + str(k + 1) + r'\.(\d+)\s*[^.\d]', text)), key=int)
        h['tables'] = sorted(set(re.findall(r'表\s*' + str(k + 1) + r'\.(\d+)\s*[^.\d]', text)), key=int)
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'pdf_pages': len(doc), 'body_pdf_start': start, 'references_pdf_start': refs,
            'chapters': headings, 'toc': doc.get_toc()}

def main():
    RUN.mkdir(parents=True, exist_ok=True)
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'codex/thesis-align-reference1-20261113'
    if (RUN / 'baseline.json').exists():
        raise SystemExit('Baseline already captured; refusing to replace it.')
    data = {'base_commit': BASE, 'reference': inventory(ROOT / 'docs/materials/参考论文/论文正文/参考论文1.pdf'),
            'before': inventory(ROOT / 'output/thesis/thesis-audit-20261112/毕业论文.pdf')}
    files = subprocess.check_output(['git', 'ls-tree', '-rz', '--name-only', BASE], cwd=ROOT).decode().split('\0')
    protected = {}
    for name in files:
        if name.startswith(('docs/materials/', 'docs/experiments/', 'docs/validation/', 'output/', 'docs/thesis/screenshots/',
                            'docs/thesis/requirements-', 'docs/thesis/delivery-', 'docs/thesis/structure-', 'docs/thesis/thesis-audit-', 'server/', 'web/')) or '开题报告' in name:
            path = ROOT / name
            if path.is_file():
                protected[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (RUN / 'baseline.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (RUN / 'protected-files.json').write_text(json.dumps(protected, ensure_ascii=False, indent=2) + '\n')
    changes = [
        '可行性从需求章移入绪论；按背景、目的意义、可行性、研究内容组织。',
        '合并近期研究到国内/国外综述；先中文后外文，正文首次引用同步重排。',
        '保留全部泳道、用例、分层DFD和数据字典；去重复并压缩图面空白。',
        '仅解释实际框架和模型职责，控制约两页。',
        '补功能模块图；将总体核心流程移入本章；分别说明可靠性与安全。',
        '按数据库、分层、接口、表示层四节组织；11表88字段、39映射重新审计。',
        '按项目结构、实体/数据访问、核心业务、控制器和前端展开；补真实代码及来源。',
        '按目的、单元、集成、历史模型实验、测试报告组织；用例对应批次和证据。',
        '精简为主要工作、局限与展望，约一页。',
    ]
    lines = ['# 参考论文1结构对齐审计（修改前）', '',
             '分支基线与PR #6同为 `'+BASE+'`。远程dev为 `6c667e0c2d72430c7f6638c52a6cb700b7a7a002`。', '',
             '优先级：本轮用户转述的导师明确要求 > 2027学校规范及指定模板 > 参考论文1 > 旧稿。原始材料与历史成果按SHA-256保护。', '',
             '两份PDF均逐页提取正文与目录后统计；页数由下一章起始页减去本章起始页计算，不使用用户的约数代替实测。参考论文共106页，包含正文后的附录；其目录本身有附录未定义书签错误，不复刻该缺陷。', '',
             '|章节|参考正文页码/页数|旧稿正文页码/页数|调整依据|', '|---|---|---|---|']
    for a, b, change in zip(data['reference']['chapters'], data['before']['chapters'], changes):
        lines.append(f"|第{a['chapter']}章|{a['body_start']}—{a['body_start']+a['pages']-1} / {a['pages']}|{b['body_start']}—{b['body_start']+b['pages']-1} / {b['pages']}|{change}|")
    lines += ['', '需求证据：`docs/notes/需求决策-个人资源复用-20261112.md`及其中的会议核对来源；最新用户指示补充中文文献优先、正文核心代码、取消真人测试。该指示不等于已取得微信群完整原文。', '',
              '学校规范实际存在章标题三号/四号、行距等冲突；按导师指定正文模板实际四号黑体、正文固定20磅执行，保留模板原始页眉与布局。', '',
              '原始代码/DDL及全部既存验证文件不因论文调整而改写。静态代码核对与历史真实数据库证据分开记录；新业务测试必须有新日志才标为本轮执行。', '',
              '参考图表与旧稿逐章分布、PDF目录和页码保存在 `baseline.json`；历史保护文件共'+str(len(protected))+'项。']
    (RUN / '逐章差异与审计.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k: [(c['chapter'], c['body_start'], c['pages']) for c in data[k]['chapters']] for k in ['reference', 'before']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
