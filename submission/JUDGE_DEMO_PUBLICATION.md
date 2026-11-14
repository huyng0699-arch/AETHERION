# Q-0260 — Seven-slide demonstration publication and acceptance

**Date:** 2026-11-14 UTC. **Status:** `COMPONENT_READY`; public-access acceptance **NOT VERIFIED**. Independent reviewer required. This file is not a claim of a published NASA submission.

## Prepared deliverable

- [Seven-slide AETHERION briefing](JUDGE_DEMO_7_SLIDES.html): **one standalone HTML file**, seven distinct screens, user-selectable English and Vietnamese, arrow/Home/End and touch-swipe navigation, built-in browser **Print / PDF**, and layouts suitable for small screens and printing.
- All narrative is project-authored. No NASA logo, external scripts, CDN fonts, screenshots, fictional instrument plots or downloadable patient records are embedded. NASA scientific hyperlinks open original public sources when online; the slide content itself renders without a network connection.
- Slide 5 expressly states that the **latest Windows Qt render remains unverified**. The file is an explanatory **seven-slide alternative**, not a screen recording, proof of an EXE, live astronaut telemetry, completed clinical advice, or NASA endorsement.
- The source repository is **private** at preparation time; a GitHub `blob/main/...` or `raw/main/...` link to this file is **not** a judge-accessible anonymous URL. Do not submit it as public without an actual logged-out check.

## Publication procedure (requires a public host and explicit operator action)

1. Retrieve the exact `submission/JUDGE_DEMO_7_SLIDES.html` bytes from the current main commit. Review accuracy against the **latest** source before distribution; development may change between slide authoring and NASA submission.
2. Publish that HTML as a **single public HTTPS document** using an already authorized, independently accessible host. Do not turn on a public server, duplicate the AETHERION app, change repository visibility, expose GitHub credentials, or deploy behind authentication to satisfy this checklist.
3. From a **private/incognito browser session with no GitHub or host login**, open the resulting HTTPS URL. Verify that the document renders with no login, payment, expiring authentication token, or restricted sharing prompt. Check access from a second browser or mobile session if possible.
4. Count **exactly seven slides**. Select English and Vietnamese, use Next/Back, keyboard arrows, Home/End, mobile swipe, and Print / PDF; confirm all expected content is visible and can be read. Test original NASA source hyperlinks separately; they are not telemetry feeds. Do not replace real screenshots with generated artwork.
5. Capture the public URL, UTC validation time, response code, final redirect URL, browser, screenshot **of the hosted deck** with SHA-256 if possible, and an independent reviewer decision. Add the record to the Q-0260 Quest file. Publish the valid URL in the official NASA **Project tab** separately; code in a private GitHub repository is not a submission.

Example PowerShell read-only public HTTP response check (only **after** there is an actual published URL):

```powershell
$u = 'https://REPLACE-WITH-VERIFIED-PUBLIC-URL'
curl.exe --location --fail --silent --show-error --output judge-deck-check.html --write-out 'HTTP %{http_code}; FINAL %{url_effective}\n' $u
if ($LASTEXITCODE -ne 0) { throw 'Public URL not retrievable' }
Select-String -Path judge-deck-check.html -Pattern 'AETHERION' -Quiet
Get-FileHash -Algorithm SHA256 judge-deck-check.html
```

This command alone cannot confirm anonymous browser access, correct visuals or language controls. A response of HTTP 200 from a login page is **not** acceptance.

## Evidence snapshot for this implementation

- Source file committed under `submission/JUDGE_DEMO_7_SLIDES.html`.
- Author-time structural check: seven numbered `section.slide` blocks in order 1–7; both `data-lang=vi` and `data-lang=en` elements; keyboard/touch navigation, print stylesheet, no external stylesheet, image or script assets.
- **No externally published URL supplied.** No incognito test executed, no browser rendering/screenshot obtained, no Windows desktop/EXE testing. Publication and independent review remain blocked.
- **Quest disposition:** record `COMPONENT_READY`, `review: PENDING` and `status: BLOCKED` until the publication/review gates actually pass. The user or an authorized publishing operator must publish to a public host and validate it; never fabricate a public link.

## Scientific and privacy boundary

This artifact describes repository implementation, intended care workflow and NASA hazard context, not medically validated patient treatment. AETHERION's historical NASA literature, manual observations and explicitly fictional demo records must remain separate. Do not publish private patient data, keys, downloaded restricted materials or rights-uncleared figures.
