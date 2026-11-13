"""Reproduce three data integrity boundaries on an explicitly isolated audit DB.

Use --phase before for observed baseline behavior, --phase after for regressions.
No model calls or credentials are written to the evidence file.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'docs/validation/thesis-system-consistency-20261113'
BASE = os.environ.get('AUDIT_API', 'http://127.0.0.1:8080/api')


def call(path, method='GET', data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = Request(BASE + path, json.dumps(data).encode() if data is not None else None,
                      headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.loads(error.read())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['before', 'after'], required=True)
    phase = parser.parse_args().phase
    _, login = call('/auth/login', 'POST', {'username': 'student', 'password': '123456'})
    student = login['data']['token']
    _, login = call('/auth/login', 'POST', {'username': 'admin', 'password': '123456'})
    admin = login['data']['token']
    rows = []

    def observe(name, result, expect_rejection=True):
        status, body = result
        rows.append({'case': name, 'http_status': status, 'response': body,
                     'expected': 'HTTP 400; no invalid write' if expect_rejection else 'HTTP 200'})
        if phase == 'after':
            assert status == (400 if expect_rejection else 200), (name, status, body)
        return body.get('data')

    qid = observe('Q01 nonexistent subject must not create question and plans', call(
        '/question', 'POST', {'subjectId': 9223372036854770000, 'stem': '审计：无效科目边界'}, student))
    if qid:
        call(f'/question/{qid}', 'DELETE', token=student)

    _, root = call('/knowledge-point', 'POST', {'subjectId': 1, 'parentId': 0, 'name': '审计临时章节'}, admin)
    root_id = root['data']
    _, leaf = call('/knowledge-point', 'POST', {'subjectId': 1, 'parentId': root_id, 'name': '审计临时考点'}, admin)
    leaf_id = leaf['data']
    third_id = observe('K01 a leaf must not accept a third hierarchy level', call(
        '/knowledge-point', 'POST', {'subjectId': 1, 'parentId': leaf_id, 'name': '审计不应保存的第三级'}, admin))
    if third_id:
        call(f'/knowledge-point/{third_id}', 'DELETE', token=admin)

    # Use the model-independent DB fixture explicitly: normal APIs do not allow
    # students to assign a knowledge point manually. Do not alter seed records.
    import pymysql
    password = dict(line.split('=', 1) for line in (ROOT / '.local/mysql.env').read_text().splitlines())['MYSQL_ROOT_PASSWORD']
    db = pymysql.connect(host='127.0.0.1', port=3307, user='root', password=password,
                         database='wrongbook_browser', autocommit=True)
    _, question = call('/question', 'POST', {'subjectId': 1, 'stem': '审计关联知识点删除边界'}, student)
    qid = question['data']
    try:
        with db.cursor() as cursor:
            cursor.execute('UPDATE question SET knowledge_point_id=%s WHERE id=%s', (leaf_id, qid))
        observe('K02 referenced knowledge point must remain available', call(
            f'/knowledge-point/{leaf_id}', 'DELETE', token=admin))
        with db.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM knowledge_point WHERE id=%s', (leaf_id,))
            remaining = cursor.fetchone()[0]
        rows[-1]['remaining_knowledge_point_rows'] = remaining
        if phase == 'after':
            assert remaining == 1
    finally:
        call(f'/question/{qid}', 'DELETE', token=student)
        call(f'/knowledge-point/{leaf_id}', 'DELETE', token=admin)
        call(f'/knowledge-point/{root_id}', 'DELETE', token=admin)
        db.close()
    (RUN / f'defect-probes-{phase}.json').write_text(json.dumps({
        'phase': phase, 'scope': 'isolated wrongbook_browser; explicit Mock; direct SQL only for declared fixture',
        'observations': rows, 'regression_assertions_passed': phase == 'after'}, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'phase': phase, 'observed': len(rows), 'statuses': [r['http_status'] for r in rows]}))


if __name__ == '__main__':
    main()
