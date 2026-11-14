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
def _source_key_index() -> dict[str, str | None]:
    """Legacy UI text -> semantic key, only when the translation is unambiguous.

    Different screens can legitimately use the same visible text for different
    meanings. Never choose a random last-write-wins translation from a catalog:
    a collision could turn an outcome such as 'Better' into a care instruction.
    Ambiguous labels must be translated with explicit semantic keys by the
    owning screen. A None entry means 'leave this text untouched'.
    """
    vi, en = catalog("vi"), catalog("en")
    if vi.keys() != en.keys():
        raise ValueError("The Vietnamese and English locale keys must match")
    index: dict[str, str | None] = {}
    for key in vi:
        for literal in (vi[key], en[key]):
            if literal not in index:
                index[literal] = key
            else:
                previous = index[literal]
                if previous is not None and (
                    vi[previous] != vi[key] or en[previous] != en[key]
                ):
                    index[literal] = None
    return index


def translate_existing(text: str, locale: str) -> str:
    """Translate a unique legacy UI label; ambiguous labels require semantic IDs.

    This function must not be applied to medical facts, patient input, imported
    NASA source text, citations, identifiers or source attributions.
    """
    key = _source_key_index().get(text)
    return tr(locale, key) if key is not None else text


def translate_shell_widgets(root: object, locale: str) -> None:
    """Translate a caller-scoped UI subtree, not arbitrary NASA/clinical text.

    Does not mutate values in data tables, source document text, medical
    records, input values or event/API identifiers. Only presentation chrome
    with catalog-backed literal translations is modified.
    """
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import (
        QComboBox, QLabel, QLineEdit, QPushButton, QTabWidget,
        QTableWidget, QToolButton,
    )

    locale = normalize_locale(locale)
    for kind in (QLabel, QPushButton, QToolButton, QAction):
        for item in root.findChildren(kind):
            if item.text():
                item.setText(translate_existing(item.text(), locale))
            if item.toolTip():
                item.setToolTip(translate_existing(item.toolTip(), locale))
            if hasattr(item, "accessibleName") and item.accessibleName():
                item.setAccessibleName(translate_existing(item.accessibleName(), locale))
    for input_widget in root.findChildren(QLineEdit):
        original = input_widget.placeholderText()
        if original:
            input_widget.setPlaceholderText(translate_existing(original, locale))
        if input_widget.accessibleName():
            input_widget.setAccessibleName(translate_existing(input_widget.accessibleName(), locale))
    for tabs in root.findChildren(QTabWidget):
        for index in range(tabs.count()):
            tabs.setTabText(index, translate_existing(tabs.tabText(index), locale))
    for combo in root.findChildren(QComboBox):
        for index in range(combo.count()):
            combo.setItemText(index, translate_existing(combo.itemText(index), locale))
        if combo.accessibleName():
            combo.setAccessibleName(translate_existing(combo.accessibleName(), locale))
    for table in root.findChildren(QTableWidget):
        for index in range(table.columnCount()):
            header = table.horizontalHeaderItem(index)
            if header is not None:
                header.setText(translate_existing(header.text(), locale))
        if table.accessibleName():
            table.setAccessibleName(translate_existing(table.accessibleName(), locale))
