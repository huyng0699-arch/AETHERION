#!/usr/bin/env python3
"""Independently check official 2026 Space Apps team/project association.

A repository README is never evidence of official team membership or submission.
No NASA account sign-in or project submission is performed here.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

CHALLENGE_URL = 'https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/'
TITLE = 'Create Health Monitoring Software for Astronauts on Space Missions'
TEAM = 'TRUY TINH'
PROJECT = 'AETHERION'
HOST = 'www.spaceappschallenge.org'


class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'template', 'noscript'):
            self.depth += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'template', 'noscript'):
            self.depth = max(0, self.depth - 1)

    def handle_data(self, data):
        if self.depth == 0:
            self.text.append(data)


def visible_text(html: str) -> str:
    p = _VisibleText()
    p.feed(html)
    return ' '.join(' '.join(p.text).casefold().split())


def check_official_url(url: str, *, require_team: bool = False) -> None:
    u = urlsplit(url)
    if u.scheme != 'https' or (u.hostname or '').lower() != HOST or u.username or u.password or u.port:
        raise ValueError('Expected HTTPS URL on the official 2026 NASA Space Apps host')
    if not u.path.startswith('/2026/'):
        raise ValueError('Expected official 2026 page')
    if require_team and not (u.path.startswith('/2026/find-a-team/') or u.path.startswith('/2026/teams/')):
        raise ValueError('Expected official team page, not general challenge content')


def inspect_pages(challenge_html: str, team_html: str | None = None,
                  *, team_url: str | None = None) -> dict[str, object]:
    """Return a conservative evidence matrix from independently retrieved HTML."""
    challenge = visible_text(challenge_html)
    official_challenge_matched = TITLE.casefold() in challenge
    team = visible_text(team_html) if team_html is not None else ''
    team_page = False
    if team_url:
        check_official_url(team_url, require_team=True)
        team_page = True
    fields = {
        'schema_version': '1.0.0',
        'official_challenge_url': CHALLENGE_URL,
        'official_challenge_title_match': official_challenge_matched,
        'team_page_url': team_url,
        'official_team_page_checked': team_page and team_html is not None,
        'team_name_visible': TEAM.casefold() in team,
        'project_name_visible': PROJECT.casefold() in team,
        'team_challenge_visible': TITLE.casefold() in team,
        'official_project_tab_submission_verified': False,
    }
    # Text on a public team page proves only visible content, not successful submission.
    fields['status'] = ('TEAM_AND_PROJECT_VISIBLE_REVIEW_PENDING'
                        if all((fields['official_challenge_title_match'],
                                fields['official_team_page_checked'],
                                fields['team_name_visible'], fields['project_name_visible'],
                                fields['team_challenge_visible']))
                        else 'BLOCKED_UNVERIFIED')
    fields['reason'] = ('Official Project tab submission and team ownership require independent proof; '
                        'text appearance alone is insufficient.' if fields['status'].startswith('TEAM_')
                        else 'Official team/project association was not independently demonstrated.')
    return fields


def fetch_official_page(url: str) -> tuple[str, str]:
    check_official_url(url)
    req = Request(url, headers={'User-Agent': 'AETHERION-Source-Verification/1.0'})
    with urlopen(req, timeout=15) as response:
        final_url = response.geturl()
        check_official_url(final_url)
        data = response.read(3_000_001)
        if len(data) > 3_000_000:
            raise ValueError('Official page unexpectedly exceeds 3 MB limit')
        return data.decode('utf-8', errors='strict'), final_url


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--team-url', help='Known public official 2026 Space Apps team page URL')
    parser.add_argument('--output', type=Path, help='Save a JSON evidence report')
    args = parser.parse_args(argv)
    output: dict[str, object] = {
        'schema_version': '1.0.0',
        'official_challenge_url': CHALLENGE_URL,
        'team_page_url': args.team_url,
        'status': 'BLOCKED_UNVERIFIED',
        'official_project_tab_submission_verified': False,
        'reason': 'No verified official public team page URL supplied.',
    }
    try:
        if args.team_url:
            check_official_url(args.team_url, require_team=True)
            challenge_html, _ = fetch_official_page(CHALLENGE_URL)
            team_html, final_team = fetch_official_page(args.team_url)
            check_official_url(final_team, require_team=True)
            output = inspect_pages(challenge_html, team_html, team_url=final_team)
    except (HTTPError, URLError, UnicodeDecodeError, ValueError, TimeoutError) as exc:
        output['reason'] = f'Official URL fetch/verification failed: {type(exc).__name__}: {exc}'
    output['checked_at_utc'] = datetime.now(timezone.utc).isoformat()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    # 0 only means a verified visible association, NEVER the Project tab has been submitted.
    return 0 if output['status'] == 'TEAM_AND_PROJECT_VISIBLE_REVIEW_PENDING' else 2


if __name__ == '__main__':
    raise SystemExit(run())
