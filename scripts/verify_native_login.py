"""Focused offscreen check of the actual native shell and login/Demo flow."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/desktop/src'))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['AETHERION_API_URL'] = json.loads((ROOT / '.runtime/verification-access.json').read_text(encoding='utf8'))['url']
from PySide6.QtCore import QSettings
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

output = ROOT / '.runtime/verification'
output.mkdir(parents=True, exist_ok=True)
app = QApplication([])
app.setApplicationName('AETHERIONIntegrationCheck')
app.setOrganizationName('TRUY TINH Verification')
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(output / 'qt-settings'))
for name in ('segoeui.ttf', 'segoeuib.ttf', 'seguisym.ttf'):
    font = Path('C:/Windows/Fonts') / name
    if font.exists():
        QFontDatabase.addApplicationFont(str(font))
from aetherion_desktop.main import AetherionWindow
checks = []


def wait_for(predicate, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return
        time.sleep(.02)
    raise AssertionError('Timed out waiting for native state')


def check(name, run):
    try:
        run()
        checks.append({'name': name, 'status': 'PASS'})
        print('PASS ' + name, flush=True)
    except Exception as exc:
        checks.append({'name': name, 'status': 'FAIL', 'error': str(exc)})
        print('FAIL ' + name + ': ' + str(exc), flush=True)


def require(value):
    assert value


print('Constructing actual AetherionWindow', flush=True)
window = AetherionWindow()
window.show()
app.processEvents()
check('Native cold start selects Login', lambda: require(window.pages.currentWidget() is window.login_page))
check('Native Demo visible without credentials', lambda: require(window.login_page.demo_button.isVisible() and window.login_page.demo_button.text() == 'Demo'))
check('Native login shell renders with actual product stylesheet', lambda: require(window.grab().save(str(output / 'native-login-shell.png'))))


def small_viewport():
    window.resize(1040, 650)
    app.processEvents()
    button = window.login_page.demo_button
    point = button.mapTo(window, button.rect().bottomRight())
    require(point.y() < window.height() and point.x() < window.width())
    window.grab().save(str(output / 'native-login-1040.png'))
    window.resize(1360, 850)


check('Native Demo fits the 1040x650 minimum window', small_viewport)


def demo():
    window.login_page.demo_button.click()
    app.processEvents()
    require(window.pages.currentWidget() is window.operations_home_page)
    require(window.hackathon_demo_page.pages.currentWidget() is window.hackathon_demo_page.briefing)
    window.grab().save(str(output / 'native-demo-intro.png'))


check('Native Demo opens NASA introduction first', demo)


def load_demo():
    window.hackathon_demo_page.start.click()
    wait_for(lambda: window.hackathon_demo_page.catalog is not None, 30)
    require(window.hackathon_demo_page.pages.currentWidget() is window.hackathon_demo_page.hub)
    window.grab().save(str(output / 'native-demo-data.png'))


check('Native introduction loads actual source data', load_demo)
window.pages.setCurrentWidget(window.login_page)
access = json.loads((ROOT / '.runtime/verification-access.json').read_text(encoding='utf8'))


def login():
    window.login_page.server_input.setText(access['url'])
    window.login_page.username_input.setText(access['username'])
    window.login_page.password_input.setText(access['password'])
    window.login_page.sign_in_button.click()
    wait_for(lambda: bool(window.access_token))
    require(window.pages.currentWidget() is window.operations_home_page)
    require(window.session_identity['username'] == access['username'])


check('Native sign-in uses real HTTP bearer session', login)
check('Native sign-out returns to Login and clears identity', lambda: (window.sign_out(), app.processEvents(), require(window.pages.currentWidget() is window.login_page and not window.access_token)))
window.close()
app.processEvents()
report = {'scope': 'Actual native Qt shell offscreen on Windows; real local HTTP login. Not a packaged EXE or physical-device claim.', 'qt_platform': os.environ['QT_QPA_PLATFORM'], 'checks': checks, 'passed': sum(item['status'] == 'PASS' for item in checks), 'total': len(checks)}
report['pass_percent'] = round(100 * report['passed'] / report['total'])
(output / 'native-report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print(json.dumps({'passed': report['passed'], 'total': report['total'], 'pass_percent': report['pass_percent']}), flush=True)
sys.exit(0 if report['passed'] == report['total'] else 1)
