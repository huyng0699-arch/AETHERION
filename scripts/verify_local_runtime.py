"""Read-only normal-runtime check; creates/revokes only an owner session."""
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
root = Path(__file__).resolve().parents[1]
access = json.loads((root / '.runtime/local-access.json').read_text(encoding='utf8'))
def request(route, token=None, data=None):
    return urlopen(Request(access['url'] + route, data=None if data is None else json.dumps(data).encode(), headers={'Content-Type': 'application/json', **({'Authorization': 'Bearer ' + token} if token else {})}), timeout=5)
ready = json.load(request('/ready'))
assert ready['database'] == 'ok'
assert '_expo/static/js/web/' in request('/').read().decode()
login = json.load(request('/api/v1/auth/login', data={'username': access['username'], 'password': access['password']}))
assert login['user']['role'] == 'admin'
token = login['access_token']
subjects = json.load(request('/api/v1/subjects', token))
assert not any(row['subject_id'].startswith('integration-') for row in subjects['subjects'])
assert request('/api/v1/admin/overview', token).status == 200
assert json.load(request('/api/v1/admin/ai/settings', token))['settings']['mode'] == 'off'
knowledge = json.load(request('/api/v1/knowledge/status'))
assert knowledge['json_articles'] == 118
assert knowledge['full_text_records'] == 118
assert knowledge['metadata_only_records'] == 0
assert knowledge['missing_slots'] == ['CLIFF-119']
conditions = json.load(request('/api/v1/knowledge/conditions'))
assert conditions['total'] == conditions['matched'] == len(conditions['items']) == 119
try:
    request('/api/unknown-integration-route')
    raise AssertionError('Unknown API path unexpectedly succeeded')
except HTTPError as error:
    assert error.code == 404 and 'application/json' in error.headers.get('Content-Type', '')
try:
    request('/.runtime/local-access.json')
    raise AssertionError('Private account file is exposed')
except HTTPError as error:
    assert error.code == 404
json.load(request('/api/v1/auth/logout', token, data={}))
result = {'url': access['url'], 'readiness': 'PASS', 'web_export': 'PASS', 'owner_admin_login': 'PASS', 'admin_overview': 'PASS', 'ai_settings_default_off': 'PASS', 'test_profiles_in_normal_database': False, 'registered_normal_profiles': subjects['total'], 'nasa_conditions': conditions['total'], 'knowledge_records': knowledge['json_articles'], 'missing_knowledge_slots': knowledge['missing_slots'], 'unknown_api_json_404': 'PASS', 'private_credentials_not_served': 'PASS'}
(root / 'docs/evidence/mobile-normal-runtime.json').write_text(json.dumps(result, indent=2), encoding='utf8')
print(json.dumps(result))
