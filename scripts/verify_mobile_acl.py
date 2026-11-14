"""ACL/pagination checks use only the explicit, separate verification database."""
import json
from pathlib import Path
import secrets
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'apps/server/src'))
from aetherion_server.bootstrap import ensure_bootstrap_user
access = json.loads((root / '.runtime/verification-access.json').read_text(encoding='utf8'))
checks = []


def api(route, token=None, body=None, method='GET', extra=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    headers.update(extra or {})
    request = Request(access['url'] + route, data=None if body is None else json.dumps(body).encode(), method=method, headers=headers)
    try:
        response = urlopen(request, timeout=10)
    except HTTPError as response:
        return response.code, json.loads(response.read())
    with response:
        return response.status, json.loads(response.read())


def check(name, action):
    try:
        action()
        checks.append({'name': name, 'status': 'PASS'})
        print('PASS ' + name, flush=True)
    except Exception as exc:
        checks.append({'name': name, 'status': 'FAIL', 'error': str(exc)})
        print('FAIL ' + name + ': ' + str(exc), flush=True)


def require(value):
    assert value


status, login = api('/api/v1/auth/login', body={'username': access['username'], 'password': access['password']}, method='POST')
assert status == 200
operator = login['access_token']
crew_password = secrets.token_urlsafe(24)
ensure_bootstrap_user(root / '.runtime/verification.sqlite3', username='integration-crew', password=crew_password, role='crew', allowed_subjects=['integration-acl-allowed'])
api('/api/v1/subjects', operator, {'subject_id': 'integration-acl-allowed', 'display_name': 'ACL verification only', 'scope': 'CREW'}, 'POST')
status, login = api('/api/v1/auth/login', body={'username': 'integration-crew', 'password': crew_password}, method='POST')
assert status == 200
crew = login['access_token']
check('Crew list exposes only authorized subject', lambda: require([row['subject_id'] for row in api('/api/v1/subjects', crew)[1]['subjects']] == ['integration-acl-allowed']))
check('Crew cannot read another subject summary', lambda: require(api('/api/v1/subjects/integration-check-profile/summary', crew)[0] == 403))
check('Crew cannot register another subject', lambda: require(api('/api/v1/subjects', crew, {'subject_id': 'not-authorized', 'display_name': 'Must not persist'}, 'POST')[0] == 403))
check('Crew cannot create care records for another subject', lambda: require(api('/api/v1/care/episodes', crew, {'subject_id': 'integration-check-profile', 'chief_concern': 'Denied integration check', 'symptom_terms': [], 'interview_answers': {}, 'explicit_consent': True}, 'POST')[0] == 403))


def fixtures():
    for index in range(3):
        body = {'subject_id': 'integration-acl-allowed', 'scope': 'CREW', 'metric': 'heart_rate', 'value': 57 + index, 'unit': 'bpm', 'source_id': 'integration_test_fixture', 'observed_at': f'2026-11-14T00:00:0{index}Z', 'quality': 'UNVERIFIED', 'verification_state': 'TEST_FIXTURE'}
        for _ in range(2):
            code, result = api('/api/v1/observations', operator, body, 'POST', {'Idempotency-Key': 'mobile-integration-fixture-' + str(index)})
            assert code in (200, 201), code
    code, result = api('/api/v1/observations?subject_id=integration-acl-allowed&include_non_live=true', operator)
    assert code == 200 and len(result['observations']) == 3
    code, live = api('/api/v1/observations?subject_id=integration-acl-allowed&include_non_live=false', operator)
    assert code == 200 and live['observations'] == []


check('Test fixtures are idempotent and excluded from normal monitoring', fixtures)


def pagination():
    code, page = api('/api/v1/observations?subject_id=integration-acl-allowed&include_non_live=true&limit=2', operator)
    assert code == 200 and len(page['observations']) == 2 and page['has_more']
    from urllib.parse import quote
    code, next_page = api('/api/v1/observations?subject_id=integration-acl-allowed&include_non_live=true&limit=2&cursor=' + quote(page['next_cursor']), operator)
    assert code == 200 and len(next_page['observations']) == 1 and not next_page['has_more']
    assert not ({row['id'] for row in page['observations']} & {row['id'] for row in next_page['observations']})


check('Observation cursor advances without duplicating records', pagination)
report = {'scope': 'Live HTTP ACL/idempotency/pagination on separate verification DB; fixtures never enter normal monitoring.', 'checks': checks, 'passed': sum(row['status'] == 'PASS' for row in checks), 'total': len(checks)}
report['pass_percent'] = round(report['passed'] * 100 / report['total'])
(root / '.runtime/verification/acl-report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print(json.dumps({'passed': report['passed'], 'total': report['total'], 'pass_percent': report['pass_percent']}))
sys.exit(0 if report['passed'] == report['total'] else 1)
