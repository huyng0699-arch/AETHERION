import ast
import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VT_PATH = ROOT / "apps" / "desktop" / "src" / "aetherion_desktop" / "visual_theme.py"
KB_PATH = ROOT / "apps" / "desktop" / "src" / "aetherion_desktop" / "knowledge_browser.py"


def _load_visual_theme():
    try:
        import PySide6  # noqa: F401
    except ImportError:
        # Lightweight PySide6 stub for headless Linux CI without Qt installed.
        pyside6 = types.ModuleType("PySide6")
        qtcore = types.ModuleType("PySide6.QtCore")
        qtgui = types.ModuleType("PySide6.QtGui")
        qtwidgets = types.ModuleType("PySide6.QtWidgets")

        class _QColor:
            def __init__(self, val=""):
                self._val = str(val or "")
            def isValid(self):
                return self._val.startswith("#") and len(self._val) in (4, 7)
            def red(self): return int(self._val[1:3], 16) if len(self._val) == 7 else 0
            def green(self): return int(self._val[3:5], 16) if len(self._val) == 7 else 0
            def blue(self): return int(self._val[5:7], 16) if len(self._val) == 7 else 0
            def name(self, *_):
                if len(self._val) == 7:
                    return self._val.lower()
                return "#000000"

        class _QColorCtor(_QColor):
            class NameFormat:
                HexRgb = 0
            def __init__(self, *args):
                if len(args) == 3:
                    super().__init__(f"#{args[0]:02x}{args[1]:02x}{args[2]:02x}")
                else:
                    super().__init__(args[0] if args else "")

        qtcore.Qt = type("Qt", (), {"WidgetAttribute": type("WA", (), {"WA_TransparentForMouseEvents": 1, "WA_NoSystemBackground": 2})})
        qtcore.QSettings = object
        qtcore.QTimer = object
        qtgui.QBrush = object
        qtgui.QColor = _QColorCtor
        qtgui.QFont = object
        qtgui.QLinearGradient = object
        qtgui.QPainter = object
        qtgui.QPen = object
        qtgui.QRadialGradient = object
        qtwidgets.QWidget = object
        sys.modules["PySide6"] = pyside6
        sys.modules["PySide6.QtCore"] = qtcore
        sys.modules["PySide6.QtGui"] = qtgui
        sys.modules["PySide6.QtWidgets"] = qtwidgets

    spec = importlib.util.spec_from_file_location("aetherion_visual_theme_test", VT_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestQ0462QtTheme(unittest.TestCase):
    def test_stylesheet_modes_typography_focus_and_high_contrast(self):
        vt = _load_visual_theme()
        for mode in vt.MODES:
            p = vt.palette_for("orbit", mode, high_contrast=True)
            qss = vt.make_stylesheet(p, family="Inter", high_contrast=True, font_size=12)
            self.assertIn('font-family:"Inter"', qss)
            self.assertIn("font-size:12pt", qss)
            self.assertIn("QLineEdit:focus", qss)
            self.assertIn("QListWidget::item:selected", qss)
            self.assertIn("QTextBrowser", qss)
            self.assertIn("border:2px solid", qss)

    def test_knowledge_browser_uses_palette_table_and_active_font(self):
        src = KB_PATH.read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn("self.font().family()", src)
        self.assertIn("border-collapse:collapse", src)
        self.assertIn("p.surface_alt", src)
        self.assertNotIn('<body style="font-family: Segoe UI;', src)


if __name__ == "__main__":
    unittest.main()
