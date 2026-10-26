"""Local isolated-test API checks. No real model calls and no credentials logged.

Requires the seeded test database, Mock backend on 8080, and a second GLM
backend with NO key on 8082. Do not point these processes at development data.
RUN_ADVISOR_API_CHECK=true python scripts/validation/advisor_runtime_check.py
"""
import http.client
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'docs/validation/advisor-20261026/runtime-check.json'


def run(port, mode):
    token = ''

    def api(method, path, data=None, expected=200):
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=15)
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        conn.request(method, '/api'+path, json.dumps(data) if data is not None else None, headers)
        response = conn.getresponse()
        body = json.loads(response.read())
        conn.close()
        assert response.status == expected, (mode, method, path, response.status)
        return body

    login = api('POST', '/auth/login', {'username': 'student', 'password': os.environ.get('TEST_STUDENT_PASSWORD', '123456')})
    token = login['data']['token']
    created = api('POST', '/question', {
        'subjectId': 1, 'stem': '<p onclick="x()">二次函数 x<sup>2</sup> - 5x + 6</p><ul><li>求零点</li></ul>',
        'answer': 'x = 2 或 x = 3', 'source': '__advisor_isolated_runtime_20261026__',
    })['data']
    try:
        detail = api('GET', f'/question/{created}')['data']
        assert '<sup>2</sup>' in detail['stem'] and 'onclick' not in detail['stem']
        summary = dict(mode=mode, rich_text_saved=True)
        if mode == 'glm-without-key':
            analysis = api('POST', f'/ai/analyze/{created}', expected=400)
            recognition = api('POST', '/question-recognition/recognize',
                              {'imageBase64': 'data:image/png;base64,iVBORw0KGgo='}, expected=400)
            variant = api('POST', f'/variant/generate/{created}', expected=400)
            assert 'LLM_API_KEY' in analysis['message'] and '未配置' in analysis['message']
            assert '未配置' in recognition['message'] and '手工录入' in recognition['message']
            assert 'LLM_API_KEY' in variant['message']
            assert api('GET', f'/ai/analysis/{created}')['data'] is None
            assert api('GET', f'/question/{created}')['data']['stem'] == detail['stem']
            summary.update(manual_input_available=True, ai_missing_key_explicit=True,
                           image_missing_key_explicit=True, variant_missing_key_explicit=True,
                           no_mock_fallback=True, failed_request_keeps_question=True)
        else:
            api('POST', f'/ai/analyze/{created}')
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                analysis = api('GET', f'/ai/analysis/{created}')['data']
                if analysis and analysis['status'] != 0:
                    break
                time.sleep(.2)
            assert analysis['status'] == 1 and analysis['llmModel'] == 'mock-llm'
            variants = api('POST', f'/variant/generate/{created}')['data']
            assert len(variants) == 3
            api('POST', '/practice', {'variantId': variants[0]['id'], 'isCorrect': 1, 'userAnswer': '学生自行确认'})
            assert api('GET', f'/question/{created}')['data']['mastery'] == 15
            api('POST', '/practice', {'questionId': created, 'isCorrect': 0})
            assert api('GET', f'/question/{created}')['data']['mastery'] == 0
            report = api('GET', '/report/weekly')
            assert report['data'] is not None
            summary.update(analysis_success=True, model='mock-llm', variant_count=3,
                           mastery_after_correct=15, mastery_after_wrong=0, weekly_report=True)
        return summary
    finally:
        api('DELETE', f'/question/{created}')


if __name__ == '__main__':
    assert os.environ.get('RUN_ADVISOR_API_CHECK') == 'true', 'Explicit isolated-test opt-in required'
    result = {'date': '2026-10-26', 'real_glm_network_test': 'not run: no configured key',
              'checks': [run(8080, 'mock'), run(8082, 'glm-without-key')]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
