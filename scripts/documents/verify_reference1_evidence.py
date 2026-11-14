"""Reconcile observed MySQL columns/indexes and recompute retained Gate5 scores."""
from pathlib import Path
from collections import Counter
import csv,json,re,subprocess

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'docs/validation/thesis-align-reference1-20261113'

def main():
    audit=json.loads((RUN/'code-thesis-audit.json').read_text())
    rows=list(csv.DictReader((RUN/'schema-columns.tsv').open(),delimiter='\t'))
    observed={(r['TABLE_NAME'],r['COLUMN_NAME']):r for r in rows}
    expected={(t['name'],f['name']):f for t in audit['tables'] for f in t['fields']}
    assert observed.keys()==expected.keys()
    for key,f in expected.items():
        row=observed[key];c=f['constraint']
        assert row['COLUMN_TYPE'].upper()==f['type'],(key,row,f)
        assert (row['IS_NULLABLE']=='NO')==('NOT NULL' in c),(key,row,c)
        assert ('auto_increment' in row['EXTRA'])==('AUTO_INCREMENT' in c),(key,row,c)
        if 'PRIMARY KEY' in c:assert row['COLUMN_KEY']=='PRI'
        m=re.search(r"DEFAULT ('[^']*'|\w+)",c)
        if m:
            wanted=m[1].strip("'")
            actual=row['IFNULL(COLUMN_DEFAULT,\'<NULL>\')']
            assert actual.upper()==('<NULL>' if wanted=='NULL' else wanted.upper()),(key,actual,wanted)
    query="SELECT TABLE_NAME,INDEX_NAME,NON_UNIQUE,SEQ_IN_INDEX,COLUMN_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA='wrongbook_test' ORDER BY TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX;"
    command=['docker','--host=unix:///var/run/docker.sock','exec','thesis-align-mysql-20261113','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot --batch -e "$1"','sh',query]
    result=subprocess.check_output(command,text=True);(RUN/'schema-indexes.tsv').write_text(result)
    actual_indexes={}
    for r in csv.DictReader(result.splitlines(),delimiter='\t'):
        actual_indexes.setdefault((r['TABLE_NAME'],r['INDEX_NAME']),{'unique':r['NON_UNIQUE']=='0','columns':[]})['columns'].append(r['COLUMN_NAME'])
    expected_indexes={}
    for t in audit['tables']:
        expected_indexes[(t['name'],'PRIMARY')]={'unique':True,'columns':['id']}
        for idx in t['indexes']:
            m=re.fullmatch(r'(UNIQUE )?KEY (\w+) \(([^)]+)\)',idx)
            expected_indexes[(t['name'],m[2])]={'unique':bool(m[1]),'columns':[s.strip() for s in m[3].split(',')]}
    assert actual_indexes==expected_indexes,(actual_indexes,expected_indexes)
    gate=ROOT/'docs/experiments/gate5'
    scores=list(csv.DictReader((gate/'manual/error-cause-review.csv').open(encoding='utf-8-sig')))
    ab=list(csv.DictReader((gate/'manual/rag-ab-review.csv').open(encoding='utf-8-sig')))
    key=json.loads((gate/'results/rag-ab-key.json').read_text());values=[int(r['manualScore']) for r in scores]
    preferences=Counter(key[r['caseId']][r['preferred']] for r in ab)
    assert len(values)==27 and sum(values)==46 and preferences=={'RAG_ON':2,'RAG_OFF':4}
    results={'observed_mysql':{'version':'8.0.46','tables':len({r['TABLE_NAME'] for r in rows}),'columns':len(rows),'all_types_nullability_defaults_and_auto_increment_match':True,'all_primary_unique_and_ordinary_indexes_match':True,'index_count':len(actual_indexes)},
             'gate5_recalculation':{'new_model_calls':0,'cases':len(values),'score':sum(values),'maximum':len(values)*2,'mean':sum(values)/len(values),'distribution':dict(Counter(values)),'ab_cases':len(ab),'preferences':dict(preferences),'original_data_unchanged':'Protected file SHA verification in code-thesis-audit.json'},
             'scope':'New MySQL metadata verification; historical Gate5 statistics recomputed, no experiment output or manual score overwritten.'}
    (RUN/'runtime-schema-and-gate5.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(results,ensure_ascii=False))

if __name__=='__main__':main()
