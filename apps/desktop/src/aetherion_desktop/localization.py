"""Bilingual, native Qt UI strings. Never translate scientific source records here.

Semantic IDs are the contract. translate_existing() is a migration adapter for
the original one-language shell; new UI should call tr(locale, key) directly.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

SUPPORTED_LOCALES = ("vi", "en")
DEFAULT_LOCALE = "vi"


def normalize_locale(value: object) -> str:
    code = str(value or "").strip().replace("_", "-").split("-", 1)[0].lower()
    return code if code in SUPPORTED_LOCALES else DEFAULT_LOCALE


@lru_cache(maxsize=2)
def catalog(locale: str) -> dict[str, str]:
    language = normalize_locale(locale)
    path = Path(__file__).resolve().parent / "i18n" / f"{language}.json"
    with path.open("r", encoding="utf-8") as stream:
        content = json.load(stream)
    if not isinstance(content, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in content.items()
    ):
        raise ValueError(f"Invalid locale catalog: {path.name}")
    return content


def tr(locale: str, key: str, /, **placeholders: object) -> str:
    """Return a localized UI message; fail explicitly for missing keys."""
    try:
        template = catalog(locale)[key]
    except KeyError as error:
        raise KeyError(f"Missing {normalize_locale(locale)} translation: {key}") from error
    return template.format(**placeholders)


@lru_cache(maxsize=1)
def _source_key_index() -> dict[str, str]:
    """Temporary bridge for legacy shell literals; future pages use semantic IDs."""
    vi, en = catalog("vi"), catalog("en")
    if vi.keys() != en.keys():
        raise ValueError("The Vietnamese and English locale keys must match")
    index: dict[str, str] = {}
    for key in vi:
        index[vi[key]] = key
        index[en[key]] = key
    return index


def translate_existing(text: str, locale: str) -> str:
    """Translate exact known legacy labels, never arbitrary clinical content."""
    key = _source_key_index().get(text)
    return tr(locale, key) if key else text


def translate_shell_widgets(root: object, locale: str) -> None:
    """Update ONLY caller-selected UI containers, never medical document content."""
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QLabel, QPushButton, QToolButton

    for kind in (QLabel, QPushButton, QToolButton, QAction):
        for item in root.findChildren(kind):
            if item.text():
                item.setText(translate_existing(item.text(), locale))
            if item.toolTip():
                item.setToolTip(translate_existing(item.toolTip(), locale))
            if hasattr(item, "accessibleName") and item.accessibleName():
                item.setAccessibleName(translate_existing(item.accessibleName(), locale))
