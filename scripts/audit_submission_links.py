#!/usr/bin/env python3
"""Unauthenticated reviewer-link audit for submission Markdown.

No cookies, API tokens, authorization headers or GitHub credentials are used.
An HTTP success is not proof that a judge can see the intended content.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]]+\]\((https?://[^\s)]+)\)|(?<![\w/])(https?://[^\s<>\)\]]+)")
ALLOWED_HOSTS = {"github.com", "www.github.com", "spaceappschallenge.org", "www.spaceappschallenge.org"}


class NoCrossHostRedirect(HTTPRedirectHandler):
    """Do not forward a request to a different host during audit."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).hostname != urlsplit(req.full_url).hostname:
            raise URLError("cross-host redirect requires manual review")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def extract_links(paths: list[Path]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            url = (match.group(1) or match.group(2)).rstrip(".,;:")
            found.setdefault(url, []).append(str(path.relative_to(ROOT)))
    return found


def check_url(url: str, timeout: float) -> dict[str, object]:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        return {"result": "MANUAL_REVIEW", "reason": "not HTTPS"}
    if parsed.username or parsed.password:
        return {"result": "FAIL", "reason": "credentials embedded in URL"}
    if parsed.hostname not in ALLOWED_HOSTS:
        return {"result": "MANUAL_REVIEW", "reason": "external host requires explicit review"}
    opener = build_opener(NoCrossHostRedirect())
    # GET rather than HEAD: some sites return 200 for HEAD but a login wall for GET.
    request = Request(url, headers={"User-Agent": "AETHERION-public-link-audit/1.0", "Accept": "text/html"})
    try:
        with opener.open(request, timeout=timeout) as response:
            code = response.status
            final_url = response.url
            sample = response.read(16384).decode("utf-8", errors="replace").lower()
        if "sign in to github" in sample or "log in to github" in sample:
            return {"result": "FAIL", "http_status": code, "reason": "login wall", "final_url": final_url}
        if "/login" in urlsplit(final_url).path or "/signin" in urlsplit(final_url).path:
            return {"result": "FAIL", "http_status": code, "reason": "redirected to login", "final_url": final_url}
        return {"result": "HTTP_OK_MANUAL_CONTENT_REVIEW", "http_status": code, "final_url": final_url}
    except HTTPError as exc:
        return {"result": "FAIL", "http_status": exc.code, "reason": "HTTP error"}
    except (URLError, TimeoutError, OSError) as exc:
        return {"result": "UNVERIFIED", "reason": type(exc).__name__ + ": " + str(exc.reason if isinstance(exc, URLError) else exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    parser.add_argument("--offline", action="store_true", help="Extract URLs without network requests")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    files = sorted((ROOT / "submission").rglob("*.md"))
    links = extract_links(files)
    rows = []
    for url, locations in sorted(links.items()):
        result = {"url": url, "files": sorted(set(locations))}
        result.update({"result": "UNVERIFIED_OFFLINE"} if args.offline else check_url(url, args.timeout))
        rows.append(result)
    summary = {status: sum(row["result"] == status for row in rows) for status in sorted({row["result"] for row in rows})}
    report = {"checked_without_credentials": not args.offline, "scanned_files": len(files), "unique_urls": len(rows), "summary": summary, "links": rows}
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    # Offline is explicitly not a passing audit; manual review always remains required.
    return 1 if any(row["result"] == "FAIL" for row in rows) else (2 if args.offline or any(row["result"] in {"UNVERIFIED", "MANUAL_REVIEW"} for row in rows) else 0)


if __name__ == "__main__":
    sys.exit(main())
