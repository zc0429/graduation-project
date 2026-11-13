"""HTTP + real MySQL audit, confined to the task's disposable local databases.

The model is explicitly Mock. Assertions concern persistence and access control,
never GLM content quality. SQL fixtures for due dates/messages are labelled.
"""
from datetime import date, timedelta
from pathlib import Path
import json
import re
import time
import pymysql
from probe_consistency_defects import call, ROOT, RUN


def main():
    password = dict(line.split('=', 1) for line in (ROOT / '.local/mysql.env').read_text().splitlines())['MYSQL_ROOT_PASSWORD']
    db = pymysql.connect(host='127.0.0.1', port=3307, user='root', password=password,
                         database='wrongbook_browser', autocommit=True, cursorclass=pymysql.cursors.DictCursor)
    rows = []

    def sql(query, args=()):
        with db.cursor() as cursor:
            cursor.execute(query, args)
            return cursor.fetchall()

    def check(name, path, method='GET', data=None, token=None, expected=200):
        status, body = call(path, method, data, token)
        assert status == expected, (name, status, body)
        # Never log tokens or full login/profile responses.
        rows.append({'case': name, 'method': method, 'path': path, 'http_status': status,
                     'business_code': body.get('code'), 'assertion': 'passed'})
        return body.get('data')

    tokens, users = {}, {}
    for role in ['student', 'teacher', 'admin']:
        data = check('seed login ' + role, '/auth/login', 'POST', {'username': role, 'password': '123456'})
        tokens[role] = data['token']; users[role] = data['user']['id']
    student, teacher, admin = (tokens[x] for x in ['student', 'teacher', 'admin'])
    name = 'audit_' + str(time.time_ns())[-14:]
    uid = check('FR01 registration', '/auth/register', 'POST', {'username': name, 'password': 'audit123456'})
    other = check('FR01 new student login', '/auth/login', 'POST', {'username': name, 'password': 'audit123456'})['token']
    check('FR01 duplicate registration', '/auth/register', 'POST', {'username': name, 'password': 'audit123456'}, expected=400)
    check('FR01 invalid credentials', '/auth/login', 'POST', {'username': name, 'password': 'wrong'}, expected=401)
    check('FR01 profile update', '/user/profile', 'PUT', {'nickname': '审计临时账号', 'className': '仅文本无班级绑定'}, other)
    assert check('FR01 profile readback', '/user/profile', token=other)['nickname'] == '审计临时账号'

    inventory = json.loads((RUN / 'inventory.json').read_text())
    permission_rows = []
    for endpoint in inventory['endpoints']:
        if endpoint['roles'] == ['public']:
            continue
        path = re.sub(r'\{[^}]+\}', '1', endpoint['path'].removeprefix('/api'))
        if path.endswith('/tree') or path.endswith('/list') or path.endswith('/similar'):
            path += '?questionId=1&subjectId=1'
        status, _ = call(path, endpoint['method'])
        assert status == 401, (endpoint, status)
        permission_rows.append({'method': endpoint['method'], 'path': endpoint['path'], 'role': 'anonymous', 'expected': 401, 'actual': status})
        if endpoint['roles'] == ['authenticated']:
            continue
        for role, token in tokens.items():
            if role not in endpoint['roles']:
                status, _ = call(path, endpoint['method'], token=token)
                assert status == 403, (endpoint, role, status)
                permission_rows.append({'method': endpoint['method'], 'path': endpoint['path'], 'role': role, 'expected': 403, 'actual': status})

    subject = check('FR02 create subject', '/subject', 'POST', {'name': '审计科目' + name, 'code': 'AUDIT', 'sort': 99}, admin)
    check('FR02 update subject', f'/subject/{subject}', 'PUT', {'name': '审计科目修订' + name, 'code': 'AUDIT2', 'sort': 98}, admin)
    assert any(s['id'] == subject and s['code'] == 'AUDIT2' for s in check('FR02 subject readback', '/subject/list', token=student))
    chapter = check('FR03 create chapter', '/knowledge-point', 'POST', {'subjectId': subject, 'parentId': 0, 'name': '审计章节'}, admin)
    leaf = check('FR03 create leaf', '/knowledge-point', 'POST', {'subjectId': subject, 'parentId': chapter, 'name': '审计考点'}, admin)
    tree = check('FR03 tree readback', f'/knowledge-point/tree?subjectId={subject}', token=student)
    assert tree[0]['id'] == chapter and tree[0]['children'][0]['id'] == leaf
    check('FR03 parent cannot delete before child', f'/knowledge-point/{chapter}', 'DELETE', token=admin, expected=400)

    qid = check('FR04 create question', '/question', 'POST', {'subjectId': 1, 'stem': '审计：求二次函数的值域', 'answer': '[0,4]', 'source': name}, student)
    q2 = check('FR07 same-owner reference question', '/question', 'POST', {'subjectId': 1, 'stem': '审计：另一道二次函数值域', 'answer': '[0,9]'}, student)
    foreign_q = check('FR04 other student question', '/question', 'POST', {'subjectId': 1, 'stem': '他人的私有题'}, other)
    cycle = []

    def snapshot(step):
        value = sql('SELECT (SELECT COUNT(*) FROM learning_content WHERE question_id=%s) knowledge_rows,'
                    '(SELECT COUNT(*) FROM variant_question WHERE question_id=%s) variant_rows,'
                    '(SELECT COUNT(*) FROM practice_record p LEFT JOIN variant_question v ON p.variant_id=v.id WHERE p.question_id=%s OR v.question_id=%s) practice_rows,'
                    '(SELECT COUNT(*) FROM review_plan WHERE question_id=%s) plan_rows,'
                    '(SELECT COUNT(*) FROM review_plan WHERE question_id=%s AND status=1) finished_plans,'
                    '(SELECT mastery FROM question WHERE id=%s) mastery', (qid,) * 7)[0]
        cycle.append({'step': step, **value})
        return value

    try:
        plans = sql('SELECT plan_date,review_stage FROM review_plan WHERE question_id=%s ORDER BY review_stage', (qid,))
        assert [p['plan_date'] for p in plans] == [date.today() + timedelta(days=i) for i in [1, 2, 4, 7, 15]]
        snapshot('create: five fixed dates')
        knowledge = check('FR06 first knowledge', f'/learning/knowledge/{qid}', 'POST', token=student)
        assert not knowledge['reused']
        repeated = check('FR06 cache reuse', f'/learning/knowledge/{qid}', 'POST', token=student)
        assert repeated['reused'] and repeated['id'] == knowledge['id']
        snapshot('knowledge generated once and reused')
        original = check('FR08 original first', f'/learning/practice/next/{qid}', 'POST', token=student)
        assert original['source'] == 'original' and original['questionId'] == qid
        assert snapshot('get without submission')['practice_rows'] == 0
        # Explicitly verifies the old variant endpoint has its own pool boundary.
        variants = check('FR08 legacy variant generation before original attempt', f'/variant/generate/{qid}', 'POST', token=student)
        assert len(variants) == 3
        assert check('FR08 unified next still returns original', f'/learning/practice/next/{qid}', 'POST', token=student)['source'] == 'original'
        check('FR10 incorrect original consumes only original', '/practice', 'POST', {'questionId': qid, 'isCorrect': 0}, student)
        assert check('FR08 reuse stored unpracticed variant', f'/learning/practice/next/{qid}', 'POST', token=student)['source'] == 'existing'
        for v in variants:
            check('FR10 submit each variant', '/practice', 'POST', {'variantId': v['id'], 'isCorrect': 0}, student)
        snapshot('three variants all submitted')
        generated = check('FR08 exhausted pool generates new batch', f'/learning/practice/next/{qid}', 'POST', token=student)
        assert generated['source'] == 'generated'
        assert snapshot('continue after exhaustion')['variant_rows'] == 6
        check('FR10 explicit original redo', '/practice', 'POST', {'questionId': qid, 'isCorrect': 1, 'userAnswer': '[0,4]'}, student)
        final = snapshot('redo: no generated resources or completed plans')
        assert final['mastery'] == 15 and final['practice_rows'] == 5 and final['finished_plans'] == 0
        history = check('FR10 history is own', '/practice/page?pageSize=100', token=student)
        assert all(p['userId'] == users['student'] for p in history['records'])
        check('FR10 exclusive target validation', '/practice', 'POST', {'questionId': qid, 'variantId': variants[0]['id'], 'isCorrect': 1}, student, expected=400)
        for suffix, method in [(f'/question/{qid}', 'GET'), (f'/question/{qid}', 'DELETE'),
                               (f'/ai/analysis/{qid}', 'GET'), (f'/ai/analyze/{qid}', 'POST'),
                               (f'/learning/knowledge/{qid}', 'POST'), (f'/learning/practice/next/{qid}', 'POST'),
                               (f'/learning/practice/progress/{qid}', 'GET'), (f'/variant/list?questionId={qid}', 'GET'),
                               (f'/variant/generate/{qid}', 'POST'), (f'/recommend/similar?questionId={qid}', 'GET')]:
            check('cross-user object isolation', suffix, method, token=other, expected=403)
        check('cross-user answer isolation', '/practice', 'POST', {'variantId': variants[0]['id'], 'isCorrect': 1}, other, expected=403)
        check('FR05 trigger asynchronous Mock analysis', f'/ai/analyze/{qid}', 'POST', token=student)
        analysis = None
        for _ in range(40):
            analysis = check('FR05 poll real persisted Mock state', f'/ai/analysis/{qid}', token=student)
            if analysis and analysis['status'] != 0:
                break
            time.sleep(.2)
        assert analysis['status'] == 1 and analysis['llmModel'] == 'mock-llm'
        # Declare candidate fixtures; vector behavior is tested with the live services.
        kp = analysis['knowledgePointId']
        vector = sql('SELECT embedding FROM question WHERE id=%s', (qid,))[0]['embedding']
        sql('UPDATE question SET knowledge_point_id=%s,difficulty=2,embedding=%s WHERE id=%s', (kp, vector, q2))
        sql('UPDATE question SET knowledge_point_id=%s,difficulty=2,embedding=%s WHERE id=%s', (kp, vector, foreign_q))
        similar = check('FR07 same-owner recommendation', f'/recommend/similar?questionId={qid}', token=student)
        assert any(q['id'] == q2 for q in similar)
        assert all(q['userId'] == users['student'] and q['id'] != qid for q in similar)
        # SQL moves exactly one owned plan to today for review UI/API; no GLM experiment date is changed.
        pid = sql('SELECT id FROM review_plan WHERE question_id=%s ORDER BY review_stage LIMIT 1', (qid,))[0]['id']
        sql('UPDATE review_plan SET plan_date=CURRENT_DATE WHERE id=%s', (pid,))
        due = check('FR09 due list', '/review-plan/today', token=student)
        assert any(p['id'] == pid for p in due)
        check('FR09 foreign finish denied', f'/review-plan/{pid}/finish', 'PUT', token=other, expected=403)
        mastery = sql('SELECT mastery FROM question WHERE id=%s', (qid,))[0]['mastery']
        check('FR09 finish independently', f'/review-plan/{pid}/finish', 'PUT', token=student)
        assert sql('SELECT mastery FROM question WHERE id=%s', (qid,))[0]['mastery'] == mastery
        check('FR09 repeated finish rejected', f'/review-plan/{pid}/finish', 'PUT', token=student, expected=400)
        for role in ['student', 'teacher']:
            report = check('FR11 ' + role + ' report', '/report/weekly', token=tokens[role])
            expected_count = sql('SELECT COUNT(*) n FROM question WHERE status=1' + (' AND user_id=%s' if role == 'student' else ''), (users['student'],) if role == 'student' else ())[0]['n']
            assert report['totalQuestionCount'] == expected_count
            assert len(report['dailyNewQuestions']) == len(report['dailyPractices']) == 7
        check('FR11 generate notification', '/report/generate', 'POST', token=student)
        messages = check('FR13 own messages', '/message/page?pageSize=100', token=student)
        assert all(m['userId'] == users['student'] for m in messages['records'])
        mid = messages['records'][0]['id']
        check('FR13 foreign read denied', f'/message/{mid}/read', 'PUT', token=other, expected=403)
        check('FR13 mark read', f'/message/{mid}/read', 'PUT', token=student)
        assert sql('SELECT is_read FROM message WHERE id=%s', (mid,))[0]['is_read'] == 1
        check('FR13 unread count', '/message/unread-count', token=student)
        aid = check('FR14 publish', '/announcement', 'POST', {'title': '审计临时公告' + name, 'content': '隔离环境发布回读'}, admin)
        for role in tokens:
            assert any(a['id'] == aid for a in check('FR14 visible to ' + role, '/announcement/list', token=tokens[role]))
        sql('DELETE FROM announcement WHERE id=%s', (aid,))
        # Recognition is explicitly disabled. This proves fallback, not image quality.
        check('FR04 recognition unavailable retains manual workflow', '/question-recognition/recognize', 'POST', {'imageBase64': 'data:image/png;base64,iVBORw0KGgo='}, student, expected=400)
        check('FR04 core edit invalidates persisted derived rows', f'/question/{qid}', 'PUT', {'subjectId': 1, 'stem': '审计修改后的有效题干', 'answer': '[0,5]'}, student)
        for table in ['learning_content', 'variant_question', 'ai_analysis']:
            assert sql('SELECT COUNT(*) n FROM ' + table + ' WHERE question_id=%s', (qid,))[0]['n'] == 0
        check('FR01 admin cannot disable itself', f'/user/{users["admin"]}', 'DELETE', token=admin, expected=400)
        check('FR01 disable user', f'/user/{uid}', 'DELETE', token=admin)
        check('FR01 old session rejected after disable', '/user/profile', token=other, expected=401)
        check('FR01 disabled login rejected', '/auth/login', 'POST', {'username': name, 'password': 'audit123456'}, expected=401)
    finally:
        for question_id in [qid, q2]:
            call(f'/question/{question_id}', 'DELETE', token=student)
        # Direct cleanup is confined to disposable fixtures, including a now disabled user.
        for question_id in [qid, q2, foreign_q]:
            for table in ['learning_content', 'ai_analysis', 'variant_question', 'review_plan']:
                sql('DELETE FROM ' + table + ' WHERE question_id=%s', (question_id,))
            sql('DELETE FROM question WHERE id=%s', (question_id,))
        call(f'/knowledge-point/{leaf}', 'DELETE', token=admin)
        call(f'/knowledge-point/{chapter}', 'DELETE', token=admin)
        sql('DELETE FROM subject WHERE id=%s', (subject,))
        sql('DELETE FROM user WHERE id=%s', (uid,))
    (RUN / 'runtime-api-audit.json').write_text(json.dumps({'model': 'explicit Mock; no external GLM request',
        'cases': rows, 'permission_sweep': permission_rows, 'cycle_snapshots': cycle,
        'fixtures': 'SQL declares candidate vectors, one due date, and removes only task data; not historical experiments',
        'passed': True}, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'api_steps': len(rows), 'permission_assertions': len(permission_rows), 'cycle_snapshots': len(cycle), 'passed': True}))
    db.close()


if __name__ == '__main__':
    main()
