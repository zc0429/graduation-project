"""Independently fetch all 32 prior bibliography sources; never equate HTTP 200 with verification."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, re
import requests, fitz
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'docs/validation/thesis-align-reference1-20261113'
CACHE = Path('/workspace/scratch/thesis-align/sources')

def fetch(rec):
    result = {'old_number': rec['number'], 'key': rec['key'], 'entry': rec['entry'],
              'year': rec['year'], 'source_url': rec['source_url'], 'checked_on': '2026-11-13'}
    attempts = []
    for url in [rec['source_url']] + (['https://api.crossref.org/works/' + rec['doi']] if rec.get('doi') else []):
        attempt = {'url': url}
        try:
            r = requests.get(url, timeout=22, headers={'User-Agent': 'Mozilla/5.0 (bibliographic verification)'})
            attempt.update(status=r.status_code, final_url=r.url, sha256=hashlib.sha256(r.content).hexdigest(), bytes=len(r.content))
            if r.status_code == 200:
                if r.content[:4] == b'%PDF':
                    d = fitz.open(stream=r.content, filetype='pdf'); text = '\n'.join(p.get_text() for p in list(d)[:2])
                elif 'api.crossref.org' in url:
                    m = r.json()['message']; text = json.dumps({k:m.get(k) for k in ['title','author','published','published-print','published-online','volume','issue','page','container-title','DOI']}, ensure_ascii=False)
                    attempt['crossref_metadata'] = json.loads(text)
                else:
                    r.encoding = r.apparent_encoding or 'utf-8'
                    soup = BeautifulSoup(r.text, 'html.parser')
                    for s in soup(['script','style','nav']): s.decompose()
                    text = soup.get_text(' ', strip=True)
                (CACHE / f"{rec['number']:02}-{len(attempts)}.txt").write_text(text)
                title = re.split(r'［[JMC]］', rec['entry'].split('．', 1)[1])[0]
                clean = lambda s: re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', s.lower())
                attempt['title_match'] = clean(title) in clean(text)
                attempt['year_present'] = str(rec['year']) in text
                pos = text.find(title[:12])
                attempt['metadata_excerpt'] = text[max(0,pos-60):max(0,pos-60)+650]
        except Exception as exc:
            attempt['error'] = type(exc).__name__ + ': ' + str(exc)[:160]
        attempts.append(attempt)
    result['attempts'] = attempts
    result['status'] = '题名及年份命中，仍需核对题录' if any(x.get('title_match') and x.get('year_present') for x in attempts) else '直接访问未核实，转官方检索或记录限制'
    return result

def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    recs = json.loads((ROOT/'docs/references/reference-audit-20261112.json').read_text())['records']
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(fetch, recs))
    (RUN/'reference-network-verification.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n')
    for row in rows:
        print(row['old_number'], row['status'], [(x.get('status'), x.get('title_match')) for x in row['attempts']])

if __name__ == '__main__':
    main()
