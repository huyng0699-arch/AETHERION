"""Q-0256: synthetic HTML fixtures, not a claim of official registration."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/verify_submission_team.py'
spec = importlib.util.spec_from_file_location('submission_team_checker', SCRIPT)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

OFFICIAL = '<h1>Create Health Monitoring Software for Astronauts on Space Missions</h1>'
TEAM = '<h1>TRUY TINH</h1><h2>AETHERION</h2>' + OFFICIAL
TEAM_URL = 'https://www.spaceappschallenge.org/2026/find-a-team/truy-tinh/'


class TeamVerificationTests(unittest.TestCase):
    def test_match_requires_official_team_project_and_challenge(self):
        got = verify.inspect_pages(OFFICIAL, TEAM, team_url=TEAM_URL)
        self.assertEqual(got['status'], 'TEAM_AND_PROJECT_VISIBLE_REVIEW_PENDING')
        self.assertFalse(got['official_project_tab_submission_verified'])

    def test_no_team_page_never_claims_team_proof(self):
        got = verify.inspect_pages(OFFICIAL)
        self.assertEqual(got['status'], 'BLOCKED_UNVERIFIED')

    def test_wrong_team_and_project_are_not_accepted(self):
        got = verify.inspect_pages(OFFICIAL, TEAM.replace('TRUY TINH', 'OTHER TEAM'), team_url=TEAM_URL)
        self.assertEqual(got['status'], 'BLOCKED_UNVERIFIED')
        got = verify.inspect_pages(OFFICIAL, TEAM.replace('AETHERION', 'OTHER PRODUCT'), team_url=TEAM_URL)
        self.assertEqual(got['status'], 'BLOCKED_UNVERIFIED')

    def test_wrong_challenge_cannot_pass(self):
        got = verify.inspect_pages('<h1>Other challenge</h1>', TEAM, team_url=TEAM_URL)
        self.assertFalse(got['official_challenge_title_match'])
        self.assertEqual(got['status'], 'BLOCKED_UNVERIFIED')

    def test_script_hidden_content_cannot_spoof_team(self):
        html = '<script>TRUY TINH AETHERION ' + verify.TITLE + '</script><h1>Other team</h1>'
        got = verify.inspect_pages(OFFICIAL, html, team_url=TEAM_URL)
        self.assertEqual(got['status'], 'BLOCKED_UNVERIFIED')

    def test_nonofficial_url_rejected(self):
        for url in ('http://www.spaceappschallenge.org/2026/find-a-team/x/',
                    'https://spaceappschallenge.org.attacker.example/2026/find-a-team/x/',
                    'https://www.spaceappschallenge.org/2025/find-a-team/x/',
                    'https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/'):
            with self.assertRaises(ValueError):
                verify.check_official_url(url, require_team=True)

    def test_no_url_cli_returns_nonzero_and_preserves_unverified_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'evidence.json'
            with redirect_stdout(StringIO()):
                status = verify.run(['--output', str(output)])
            self.assertEqual(status, 2)
            payload = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(payload['status'], 'BLOCKED_UNVERIFIED')
            self.assertFalse(payload['official_project_tab_submission_verified'])


if __name__ == '__main__':
    unittest.main()
