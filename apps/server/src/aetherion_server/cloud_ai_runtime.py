"""Server-owned cloud provider selection; no secrets in Desktop, DB or source.

The OnePad provider-dispatch idea is adopted, not its development Base64 store.
Administrator-provided API keys are in-process only and disappear on restart.
Environment credentials remain usable only with explicit cloud opt-in flags.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import re
from threading import RLock
from typing import Literal

Provider = Literal["gemini", "openai"]
_MODEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,119}\Z")
_LOCK = RLock()


@dataclass(frozen=True)
class CloudConfiguration:
    provider: Provider
    model: str
    api_key: str
    source: str


_SESSION: CloudConfiguration | None = None


def _model_name(value: str) -> str:
    model = str(value).strip()
    if not _MODEL_RE.fullmatch(model):
        raise ValueError("Invalid model identifier")
    return model


def set_cloud_configuration(
    *, provider: Provider, model: str, api_key: str | None, enabled: bool = True,
) -> dict:
    """Set a secret for this one Server process, not SQLite or QSettings."""
    global _SESSION
    if provider not in ("gemini", "openai"):
        raise ValueError("Cloud provider must be gemini or openai")
    selected_model = _model_name(model)
    with _LOCK:
        if not enabled:
            _SESSION = None
        else:
            key = (api_key or "").strip()
            if not key and _SESSION is not None and _SESSION.provider == provider:
                key = _SESSION.api_key
            if not 8 <= len(key) <= 4096 or any(ord(c) < 33 or ord(c) == 127 for c in key):
                raise ValueError("Provide a valid API key on Server Admin")
            _SESSION = CloudConfiguration(provider, selected_model, key, "admin_memory")
    return cloud_public_status()


def clear_cloud_configuration() -> dict:
    global _SESSION
    with _LOCK:
        _SESSION = None
    return cloud_public_status()


def _env_configuration() -> CloudConfiguration | None:
    if os.getenv("AETHERION_ALLOW_CLOUD_AI", "false").lower() not in ("true", "1", "yes"):
        return None
    if os.getenv("AETHERION_ENABLE_CLOUD_CHAT", "false").lower() not in ("true", "1", "yes"):
        return None
    provider = os.getenv("AETHERION_CHAT_CLOUD_PROVIDER", "openai").strip().lower()
    if provider not in ("openai", "gemini"):
        return None
    key = os.getenv("AETHERION_GEMINI_API_KEY" if provider == "gemini" else
                    "AETHERION_OPENAI_API_KEY", "").strip()
    model = os.getenv("AETHERION_CHAT_CLOUD_MODEL", "").strip()
    if not key or not _MODEL_RE.fullmatch(model):
        return None
    return CloudConfiguration(provider, model, key, "environment")


def resolve_cloud_configuration() -> CloudConfiguration | None:
    with _LOCK:
        config = _SESSION
    return config if config is not None else _env_configuration()


def cloud_public_status() -> dict:
    config = resolve_cloud_configuration()
    return {
        "enabled": config is not None,
        "provider": config.provider if config is not None else None,
        "model": config.model if config is not None else None,
        "key_configured": config is not None,
        "secret_storage": "memory_only" if config is not None and
                          config.source == "admin_memory" else "environment",
        "source": config.source if config is not None else "none",
        "requires_user_consent": True,
        "tested": False,  # configuration is not proof of real inference
    }
