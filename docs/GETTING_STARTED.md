# AETHERION: install, run, and build

This guide covers the current local demo. The Server binds to loopback (`127.0.0.1`) by default. It is not a public internet service or a clinical deployment.

## 1. Download the project

Install Git, Python 3.11 or newer, and Node.js 22 LTS. In PowerShell:

```powershell
git clone https://github.com/huyng0699-arch/AETHERION.git
cd AETHERION
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e "apps/server[admin]" -e apps/desktop
npm ci --prefix apps/mobile
```

`apps/server[admin]` installs the Python HTTP server and its native Qt Server Control window. `apps/desktop` installs the separate native desktop client.

## 2. Run Mobile Web and Server together

From the repository root, start the local stack:

```powershell
.\scripts\start_mobile_local.ps1
```

The command type-checks and exports the Expo web app, then starts the Python Server and web app on **http://127.0.0.1:8765/**. Readiness is **http://127.0.0.1:8765/ready**. Keep this terminal open while using the app.

On an empty local database, the launcher creates a local administrator account and writes its credentials to `.runtime/local-access.json`. This file is private, excluded from Git, and must not be uploaded. Existing accounts are preserved. The public NASA Demo button does not require sign-in; health records and other protected routes do.

### Open the Server Admin panel against this same database

Open a second PowerShell window in the repository root and run:

```powershell
$env:AETHERION_DB_PATH = (Join-Path $PWD '.runtime\local.sqlite3')
.\.venv\Scripts\python.exe -m aetherion_server.admin_gui
```

Use the local owner credentials from `.runtime/local-access.json`. The Server is already running, so leave its address as `http://127.0.0.1:8765` and do not start a second copy. The Qt Admin window can manage users, inspect server status, configure AI, and create a SQLite backup.

### Run the native desktop client

In another terminal, from the repository root:

```powershell
$env:AETHERION_API_URL = 'http://127.0.0.1:8765'
.\.venv\Scripts\python.exe -m aetherion_desktop
```

Sign in with an account provisioned on that Server. The Desktop is a native PySide6 application. Its Server address must point to the same Server process and database.

### Run only the Python Server

If you do not need the web app, start the API in a terminal after installing `apps/server`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn aetherion_server.main:app --host 127.0.0.1 --port 8765
```

For a first administrator, launch `python -m aetherion_server.admin_gui`, click **Create first administrator**, and create a password of at least 12 characters. This setup is local to the machine and is locked after accounts exist. Alternatively, use `aetherion-bootstrap --help` from a private local terminal; never put bootstrap passwords in a committed file or shell history.

## 3. Configure AI

AI starts disabled. Configure it from the **Local / Cloud AI** tab in the native Server Control window, while signed in as an administrator. A button that says "configured" is not proof of inference; run the real model test and require a successful reply.

### Local model with Ollama

Install Ollama on the **same computer that runs the Python Server**, start its service, and install a model, for example:

```powershell
ollama pull qwen2.5:3b
ollama list
```

In Server Control, choose **Local AI only**, leave the Ollama URL at `http://127.0.0.1:11434`, select the exact model name shown by `ollama list`, choose a timeout, click **Discover installed models**, **Save AI settings**, then **Test actual AI inference**. Use **Local** in the signed-in app's AI screen after the test succeeds. If Ollama is not running or the named model is absent, AETHERION reports unavailable and generates no substitute answer.

### Gemini or OpenAI API key

Current Server Control supports **Gemini** and **OpenAI**. It does not have a NASA chat-model provider; a NASA API key is not interchangeable with a Gemini/OpenAI chat key.

1. Obtain a valid key from the provider account that owns it. Keep it private; do not put it in GitHub, the APK, or the mobile app.
2. In Server Control, open **Local / Cloud AI**, select **Gemini** or **OpenAI**, enter a model ID supported by that provider account, and paste the key into **API key (memory only)**.
3. Click **Configure API**, then **Run real AI request**. Confirm the returned status reports a real successful inference.
4. In the signed-in AETHERION client, choose **Cloud**. Cloud messages are sent to the selected provider only after the user gives the app's explicit consent.

The API key entered in Admin exists only in the Server process memory. It is not stored in the SQLite database and is cleared when the Server restarts; re-enter it and repeat the model test after a restart. An environment-key path is documented in [AI integration](AI_ONEPAD_INTEGRATION.md), but the Admin memory-only flow is preferred for the demo.

## 4. Install and run the Android demo

### Download the APK from GitHub

1. Download [`AETHERION-Android-Demo-v0.1.0.apk`](https://github.com/huyng0699-arch/AETHERION/raw/refs/heads/main/downloads/AETHERION-Android-Demo-v0.1.0.apk) from the repository's stable APK path. GitHub sign-in is required because this repository is private.
2. Check [AETHERION Releases](https://github.com/huyng0699-arch/AETHERION/releases) for later versions.
3. Transfer the APK to Android, allow installation from that file source when Android asks, then install and open **AETHERION Mobile**.
4. Tap **Demo** on the first screen. The MA-7 historical NASA dataset is bundled in the app and can be viewed without a Server connection.

The APK is signed with a development/debug key for direct demonstration and sideloading. It is not signed for Google Play. Do not install an APK unless its release came from this repository and its workflow completed successfully.

### Build locally (Android Studio + SDK required)

Install Android Studio, JDK 17, Android SDK Platform 36, and Build Tools 36.0.0. Then run:

```powershell
Push-Location apps/mobile
npm ci
npx expo prebuild --platform android --no-install
Push-Location android
.\gradlew.bat assembleDebug
Pop-Location
Pop-Location
```

The installable APK is `apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk`. On macOS/Linux use `./gradlew assembleDebug` instead of `gradlew.bat`. For a connected development emulator, `npm run android --prefix apps/mobile` starts Expo's native development flow and requires the Android SDK.

The repository's GitHub Actions workflow is configured to build this demo APK on an Ubuntu runner, attach it to a GitHub prerelease, and keep a downloadable workflow artifact. A release appears only when a runner is available and Gradle succeeds; the stable APK path above remains available independently.

### Connect a physical Android phone to a Server

The bundled NASA Demo works offline. Live sign-in and server-backed health/library features need an HTTPS Server URL. In the login screen, expand **Connection**, enter the URL, and tap **Check connection** before signing in. The current Server deliberately accepts loopback addresses only; a LAN phone cannot connect to it directly, and this repository does not yet provide a safe public TLS gateway. Do not expose the prototype server to the public internet or use real patient data. Emulator/USB HTTP addresses are for a development build only:

- Android emulator: `http://10.0.2.2:8765`
- USB development: run `adb reverse tcp:8765 tcp:8765`, then use `http://127.0.0.1:8765`

## 5. What this release is and where it is going

**First version:** a polished, English-first Expo mobile demo with a prominent login-screen Demo flow and bundled NASA MA-7 records; a local Python/FastAPI and SQLite Server; a separate native PySide6 Desktop; source-linked NASA condition catalog and existing archive; and administrator-controlled AI provider setup. It does not provide a live biomedical sensor feed, a full 119-document archive, validated medical decisions, or an always-on AI model. The condition catalog contains 119 official names and the archive currently contains 118 source JSON records; see [the archive audit](NASA_CLIFF_119_ARCHIVE_AUDIT.md).

**Next stages:** make an authenticated HTTPS Server deployment with device-scoped access; improve offline sync and auditability; add validated mobile sensor integrations; then build separate interfaces and hardware adapters for smartwatches, habitats, and rover/mission systems. A lunar rover would require a local edge server, tested sensor and communications protocols, fail-safe offline operation, and extensive security, human-factors, clinical, and mission qualification. None of those flight systems are part of this APK.

### What can target which platform

| Target | Current state |
| --- | --- |
| Android phone/tablet | Expo app; demo APK at the stable GitHub path above |
| iOS/iPadOS | Expo source is a starting point; build/sign on macOS with Xcode; no iOS release verified yet |
| Web | Expo Web in a browser |
| Windows | Separate Python/Qt Desktop source; not the Expo APK |
| Linux | Web client in a browser; native packaging needs a separate verified build |
| Wearable or lunar rover | Future device-specific client/adapters and qualification; not supported by the current app |

Expo uses JavaScript/TypeScript and React Native to share app logic across Android and iOS, with a web target. It does **not** create Windows, Linux, smartwatch, or rover binaries automatically. AETHERION can pursue those platforms through additional clients that share the Python Server API and data contracts.

## Data and safety

AETHERION is an independent prototype, not affiliated with NASA and not clinically validated. Demo data is historical NASA material, not a current patient record. Do not use this version to make medical decisions or store real patient information. Preserve source attribution and third-party terms when redistributing project data.

