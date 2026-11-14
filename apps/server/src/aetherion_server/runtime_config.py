"""Versioned, fail-closed configuration for the local-first HTTP process.

Public binding is not supported: this prototype has no production TLS or
network access-control layer. Validation runs before Uvicorn opens a socket.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PureWindowsPath
from typing import Mapping

CONFIG_VERSION = 1
DEFAULT_PORT = 8765
LOCAL_HOSTS = frozenset({"127.0.0.1", "::1"})


@dataclass(frozen=True)
class RuntimeConfig:
    version: int
    profile: str
    host: str
    port: int
    cloud_ai_opt_in: bool = False


def read_runtime_config(environ: Mapping[str, str] | None = None) -> RuntimeConfig:
    """Return validated settings; reject network exposure and unsafe release defaults.

    The release profile is a stricter configuration *gate*, not a claim that
    AETHERION is suitable for public deployment or clinical use.
    """
    values = os.environ if environ is None else environ
    version = values.get("AETHERION_CONFIG_VERSION", "1").strip()
    if version != str(CONFIG_VERSION):
        raise ValueError(f"Unsupported AETHERION_CONFIG_VERSION {version!r}; expected {CONFIG_VERSION}")

    profile = values.get("AETHERION_PROFILE", "development").strip().lower()
    if profile not in {"development", "release"}:
        raise ValueError("AETHERION_PROFILE must be 'development' or 'release'")

    host = values.get("AETHERION_HOST", "127.0.0.1").strip()
    if host not in LOCAL_HOSTS:
        raise ValueError("AETHERION_HOST must be a literal loopback address (127.0.0.1 or ::1); public bind is prohibited")

    port_text = values.get("AETHERION_PORT", str(DEFAULT_PORT)).strip()
    try:
        port = int(port_text)
    except ValueError as exc:
        raise ValueError("AETHERION_PORT must be an integer between 1 and 65535") from exc
    if not 1 <= port <= 65535:
        raise ValueError("AETHERION_PORT must be an integer between 1 and 65535")

    ttl = values.get("AETHERION_SESSION_TTL_SECONDS")
    if ttl is not None:
        try:
            ttl_seconds = int(ttl.strip())
        except ValueError as exc:
            raise ValueError("AETHERION_SESSION_TTL_SECONDS must be a positive integer no greater than 86400") from exc
        if not 1 <= ttl_seconds <= 86400:
            raise ValueError("AETHERION_SESSION_TTL_SECONDS must be a positive integer no greater than 86400")

    cloud_raw = values.get("AETHERION_ALLOW_CLOUD_AI", "false").strip().lower()
    if cloud_raw in {"true", "1", "yes"}:
        cloud_ai_opt_in = True
    elif cloud_raw in {"false", "0", "no", ""}:
        cloud_ai_opt_in = False
    else:
        raise ValueError("AETHERION_ALLOW_CLOUD_AI must be 'true' or 'false'")

    if profile == "release":
        db_path = values.get("AETHERION_DB_PATH", "").strip()
        if not db_path or not (Path(db_path).is_absolute() or PureWindowsPath(db_path).is_absolute()):
            raise ValueError("release profile requires an absolute AETHERION_DB_PATH (never the implicit dev DB)")
        if values.get("AETHERION_BOOTSTRAP_USER") or values.get("AETHERION_BOOTSTRAP_PASSWORD"):
            raise ValueError("release profile prohibits account bootstrap credentials in environment variables")

    return RuntimeConfig(
        version=CONFIG_VERSION,
        profile=profile,
        host=host,
        port=port,
        cloud_ai_opt_in=cloud_ai_opt_in,
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate AETHERION server configuration without revealing secrets")
    parser.add_argument("--check", action="store_true", help="Fail before starting the HTTP server if config is unsafe")
    parser.parse_args()
    try:
        config = read_runtime_config()
    except ValueError as exc:
        parser.exit(status=2, message=f"AETHERION configuration rejected: {exc}\n")
    cloud_label = "opt-in" if config.cloud_ai_opt_in else "disabled"
    print(f"AETHERION configuration v{config.version}: {config.profile}, http://{config.host}:{config.port} (loopback only, cloud_ai={cloud_label})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
