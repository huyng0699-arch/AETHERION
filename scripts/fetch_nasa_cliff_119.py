#!/usr/bin/env python3
"""Download NASA's original 2023 CliFF 119 documents; never generate medical content."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SOURCE = "https://www.nasa.gov/integrated-medical-model-documentation/"
OUTPUT = Path("knowledge/nasa/cliff_119_2023")
ORIGINAL = OUTPUT / "original"
EXPECTED = 119


def normalize(value: str) -> str:
    return " ".join(value.split())


def safe_filename(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (result[:105].rstrip("-") or "untitled")


def nasa_host(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return hostname == "nasa.gov" or hostname.endswith(".nasa.gov") or hostname == "nasa.sharepoint.com"


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "AETHERION-NASA-CliFF-Archive/1.0 (source attribution; research)"})
    retry = Retry(total=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def read_index(s: requests.Session):
    r = s.get(SOURCE, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    target = None
    index_119 = None
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows[:3]:
            headers = [normalize(cell.get_text(" ", strip=True)).lower() for cell in row.find_all(["th", "td"], recursive=False)]
            matches = [i for i, header in enumerate(headers) if "cliff 119" in header.replace("–", "-")]
            if matches:
                target, index_119 = table, matches[0]
                break
        if target is not None:
            break
    if target is None:
        raise RuntimeError("NASA page did not expose the CliFF 119 table in HTML; refusing to substitute other data.")

    entries = []
    section = ""
    for row in target.find_all("tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) < index_119 + 1:
            continue
        if any(cell.name == "th" for cell in cells) and "cliff 119" in normalize(row.get_text(" ", strip=True)).lower():
            continue
        first = normalize(cells[0].get_text(" ", strip=True))
        if first:
            section = first
        cell = cells[index_119]
        name = normalize(cell.get_text(" ", strip=True))
        if not name:
            continue
        anchors = cell.find_all("a", href=True)
        urls = [
            urljoin(SOURCE, a.get("href", "").strip())
            for a in anchors if a.get("href", "").strip()
        ]
        # A single cell can contain more than one document.
        if urls:
            for a, url in zip(anchors, urls):
                title = normalize(a.get_text(" ", strip=True)) or name
                entries.append({"category": section, "title": title, "source_url": url})
        else:
            entries.append({"category": section, "title": name, "source_url": None})
    urls = [item["source_url"] for item in entries]
    if len(entries) != EXPECTED or any(not url for url in urls):
        raise RuntimeError(f"NASA CliFF 119 table is not exactly {EXPECTED} linked originals: {len(entries)} rows; {sum(bool(u) for u in urls)} links. Refusing incomplete or inferred data.")
    if len(set(urls)) != EXPECTED:
        raise RuntimeError("NASA CliFF 119 source links are not unique; refusing to claim 119 distinct originals.")
    return entries


def download(s: requests.Session, entry: dict, index: int):
    url = entry["source_url"]
    if not url:
        return {"status": "missing_link", **entry}
    if not nasa_host(url):
        return {"status": "non_nasa_host", **entry}
    try:
        response = s.get(url, timeout=90, allow_redirects=True)
        response.raise_for_status()
        content = response.content
        final_url = response.url
        if not nasa_host(final_url):
            return {"status": "redirected_off_nasa", "final_url": final_url, **entry}
        if content.startswith(b"%PDF-"):
            suffix = ".pdf"
        elif content.startswith(b"PK\x03\x04") and ".docx" in urlparse(final_url).path.lower():
            suffix = ".docx"
        elif content.startswith(b"\xd0\xcf\x11\xe0"):
            suffix = ".doc"
        else:
            return {"status": "not_downloadable_document", "final_url": final_url,
                    "http_content_type": response.headers.get("Content-Type", ""), **entry}
        stem = safe_filename(entry["title"].removesuffix("(2023)"))
        relative = Path("original") / f"{index:03d}-{stem}{suffix}"
        destination = OUTPUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return {"status": "downloaded", "path": str(relative).replace("\\", "/"),
                "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content),
                "final_url": final_url, **entry}
    except (requests.RequestException, OSError) as exc:
        return {"status": "download_failed", "error": str(exc)[:250], **entry}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    s = session()
    entries = read_index(s)
    print(f"Found {len(entries)} CliFF 119 rows on the NASA page", flush=True)
    results = []
    for index, item in enumerate(entries, 1):
        result = download(s, item, index)
        results.append(result)
        print(f"{index:03d}/{len(entries):03d} {result['status']}: {item['title']}", flush=True)
    good = sum(item["status"] == "downloaded" for item in results)
    complete = len(entries) == EXPECTED and good == EXPECTED
    manifest = {
        "dataset": "NASA Integrated Medical Model - CliFF 119 (2023)",
        "source": SOURCE,
        "publisher": "NASA",
        "expected_documents": EXPECTED,
        "source_rows_found": len(entries),
        "downloaded_documents": good,
        "complete": complete,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy": "Original NASA documents only. No derived content and no legacy repository data.",
        "files": results,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Downloaded {good}/{EXPECTED}; COMPLETE={complete}", flush=True)
    if not complete:
        print("INCOMPLETE: check manifest.json. Do not represent this archive as 119/119 verified.", flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
