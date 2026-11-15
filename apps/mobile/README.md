# AETHERION Mobile

Expo SDK 54 / React Native / TypeScript. English is the initial language; VI/EN and appearance preferences persist. The owner's Solo artwork and navigation pattern are retained with AETHERION naming and attribution.

## Entry flow

**Every launch opens Sign in.** The visible **Demo** button opens a short NASA briefing, then the read-only MA-7 archive. A saved session offers an explicit Continue action; it never bypasses the login screen automatically. Desktop uses the same Login → Demo introduction flow.

After sign-in, Home opens Health, Monitor, AI, Library and Care. More opens Crew/profiles, connection, Settings, language, appearance, privacy and help. Back navigation and edge swipe return to the previous screen; a bottom-tab Back returns to Home.

## Run the web app and API together

From the repository root on Windows, install Python 3.11+ and Node, then:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e apps/server
cd apps/mobile
npm ci
cd ../..
.\scripts\start_mobile_local.ps1
```

Open **http://127.0.0.1:8765/**. The FastAPI process serves both the Expo export and API on the same loopback origin. The launcher reuses an existing runtime only when its server-source fingerprint, client export and database scope match; it refuses to create a second listener on an occupied port.

On a new local database only, the launcher creates a local owner account with a random password. Its credentials are written to `.runtime/local-access.json`; this directory is ignored by Git and is outside the served web export. No patient or measurement is created. Existing users are preserved.

The local database is `.runtime/local.sqlite3`. Verification uses a separate `.runtime/verification.sqlite3`; test fixtures do not enter the normal monitoring query.

## Android development

```powershell
cd apps/mobile
$env:AETHERION_ALLOW_DEV_HTTP='1'
npm run android
```

For an Android emulator, use `http://10.0.2.2:8765`; for USB development, run `adb reverse tcp:8765 tcp:8765` and use `http://127.0.0.1:8765`. These HTTP addresses are development-only. A physical release client requires HTTPS, while the current Server intentionally remains loopback-only.

To build an installable debug-signed demo APK locally, install Android Studio, JDK 17, Android SDK Platform 36 and Build Tools 36.0.0, then run:

```powershell
npm ci
npx expo prebuild --platform android --no-install
Set-Location android
.\gradlew.bat assembleDebug
```

The APK is `android/app/build/outputs/apk/debug/app-debug.apk`. The GitHub workflow `.github/workflows/android-demo-apk.yml` builds the same APK and publishes it to the repository Releases after Gradle succeeds. It is a sideloadable demo, not a Play Store-signed release. See [the full install and operations guide](../../docs/GETTING_STARTED.md).

`npm run export:android` and `npm run export:android:js` export JavaScript bundles only; neither command creates an APK.

## Server contract

Readiness checks `/ready` and requires SQLite `ok`. Auth uses real bearer sessions. Subject discovery uses the authenticated `/api/v1/subjects` list, never the permission wildcard as a profile ID. Health, paged monitoring, Care and AI use the server's authoritative endpoints. Changing server origin clears the session and navigation; stale tokens cannot be sent to another origin. Cloud AI still requires per-request consent and an available server provider.

MA-7 is a separate historical NASA source: 4 groups, 19 timepoints, 18 metrics and 83 reported values. Missing metrics remain missing. Library uses the server's 118 existing CliFF JSON records; CLIFF-119 and original-PDF/clinical validation remain unresolved. JSON verification flags do not independently verify original PDF bytes.

## Focused checks

```powershell
npm run typecheck --prefix apps/mobile
npm run export:web --prefix apps/mobile
python scripts/run_mobile_local.py --verification --port 8769
# In another terminal:
node scripts/verify_mobile_web.mjs --api-only
node scripts/verify_mobile_clients.mjs
node scripts/verify_mobile_state.mjs
node scripts/verify_mobile_storage.mjs
python scripts/verify_mobile_acl.py
```

Use `node scripts/verify_mobile_web.mjs` for actual headless browser checks when the host permits Chromium to launch. Browser rendering, physical Android, a packaged Windows EXE and configured AI-model completion require their own observed acceptance. See `docs/MOBILE_DELIVERY_20261115.md` for recorded results and limits.

The verification port is deliberately separate from the normal local server. Reuse an existing matching verification runtime on that port; do not run the fixture checks against a normal-use database.
