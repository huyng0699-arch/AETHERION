# AETHERION

### One Health. One Humanity. Beyond Earth.

AETHERION is an independent Truy Tinh project for the NASA Space Apps Challenge 2026. It combines a Python/FastAPI server, a native Python/Qt desktop client, and an Expo/React Native mobile client. It is not a NASA product or endorsement, a flight-ready system, a certified medical device, or a validated diagnostic system.

## Windows desktop evidence

The project owner confirms that AETHERION launched successfully on the Windows desktop. This actual 1920×1080 capture shows the AETHERION application window on its Portal screen, with the Demo entry visible.

![AETHERION running on the Windows desktop](docs/evidence/aetherion-desktop-portal-20261114.png)

[Open the desktop runtime evidence](docs/evidence/aetherion-desktop-portal-20261114.png) · [Submission package](submission/README.md)

## Start here

The fastest local demo runs the Expo web app and the Python server together. On Windows, install Git, Python 3.11+, and Node.js 22, then run:

```powershell
git clone https://github.com/huyng0699-arch/AETHERION.git
cd AETHERION
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e "apps/server[admin]" -e apps/desktop
npm ci --prefix apps/mobile
.\scripts\start_mobile_local.ps1
```

Open **http://127.0.0.1:8765/**. The first screen is Sign in with a visible **Demo** button. Demo opens the bundled, historical NASA Mercury-Atlas 7 archive and works without an account or server connection. It is historical astronaut research, not a current patient record or live sensor feed. The local launcher creates an owner account only when its local database is empty; its private credentials are written to `.runtime/local-access.json` and are ignored by Git.

See **[Getting started: Server, AI, Desktop and Android](docs/GETTING_STARTED.md)** for the local Admin setup, Ollama/Gemini/OpenAI configuration, desktop launch, APK installation, and build commands. The Android demo APK is published as a debug-signed prerelease by the “Build Android demo APK” workflow after a successful run; see [GitHub Releases](https://github.com/huyng0699-arch/AETHERION/releases) for available builds. The repository is public, so GitHub sign-in is not required to browse or clone it.

## What is in this first version

- **Mobile:** Expo SDK 54 / React Native source targets Android and iOS, with an Expo Web export. The Android demo contains the NASA MA-7 archive for offline viewing; an iOS package has not been built or verified. Sign-in, health records, the server-backed library, and chat need a reachable AETHERION server.
- **Server:** Python 3.11+ / FastAPI with SQLite, bearer sessions, access checks, an Admin Control interface, and optional local or cloud chat providers. The server defaults to loopback and is not configured as a public production service.
- **Desktop:** separate native PySide6 client; it is not a browser wrapped in a window and is not the same binary as the Expo app.
- **NASA library:** the catalog lists 119 official condition names; 118 source JSON documents are currently archived. A catalog entry does not guarantee a full original PDF, clinical review, or treatment protocol.
- **AI:** disabled until configured and successfully tested by an administrator. Local inference uses Ollama on the same host as the server. The current cloud choices are Gemini and OpenAI; keys are held in server-process memory when entered through Admin and are lost on restart. Chat does not silently invent a reply when no model is available.

## Platform support, stated accurately

Expo/React Native shares application code across **Android and iOS**, and Expo can export the web client. iOS packaging requires macOS/Xcode and Apple signing. This project has an Android APK build workflow; the APK is a demo build signed with the Android debug key, not a Play Store release. Windows has a separate Python/Qt desktop client. Expo does not export this app directly to Windows or Linux: those targets need their own client integration or packaging. A browser can run the web client on those operating systems.

The long-term aim is to let phones, watches, habitat systems, and future lunar or planetary rover interfaces use the same server and data contracts. A watch or rover will need its own tested hardware adapters, interface, offline behavior, security, and mission qualification. Those integrations are future work; the Android APK is not a rover or smartwatch app.

## Project guidance

- [Getting started and operations](docs/GETTING_STARTED.md)
- [Mobile delivery record and verification limits](docs/MOBILE_DELIVERY_20261115.md)
- [OnePad AI integration and provider boundaries](docs/AI_ONEPAD_INTEGRATION.md)
- [NASA catalog/archive audit](docs/NASA_CLIFF_119_ARCHIVE_AUDIT.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

The project is not yet validated for clinical use or real patient data. NASA material remains subject to its source and reuse terms; see the notices and source metadata before redistribution.

