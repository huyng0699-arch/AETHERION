"""Q-0002 headless Portal contract tests (not Windows-native acceptance)."""
import ast
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / 'apps/desktop/src/aetherion_desktop/portal.py'
MAIN = ROOT / 'apps/desktop/src/aetherion_desktop/main.py'

spec = importlib.util.spec_from_file_location('aetherion_portal_under_test', PORTAL)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class PortalContractTests(unittest.TestCase):
    def test_exactly_five_distinct_navigation_destinations(self):
        self.assertEqual(len(module.PORTAL_CARDS), 5)
        self.assertEqual(len(module.PORTAL_ROUTES), 5)
        self.assertEqual(module.PORTAL_CARDS[0].title, 'Sức khỏe của tôi')
        self.assertEqual(module.PORTAL_CARDS[4].title, 'Phi hành đoàn')

    def test_portal_has_no_health_values_or_fabricated_status(self):
        content = PORTAL.read_text(encoding='utf-8')
        vi_i18n = (ROOT / 'apps/desktop/src/aetherion_desktop/i18n/vi.json').read_text(encoding='utf-8')
        self.assertNotIn('heart_rate =', content)
        self.assertNotIn('mock_sensor', content)
        self.assertNotIn('QWebEngineView', content)
        self.assertIn('portal.footer.trust', content)
        self.assertIn('KHÔNG TẠO SỐ ĐO GIẢ', vi_i18n)
        self.assertIn('Chỉ dữ liệu thật, có nguồn xác định và quyền truy cập hợp lệ', vi_i18n)

    def test_portal_does_not_require_qt_on_model_import(self):
        self.assertTrue(all(card.title and card.summary for card in module.PORTAL_CARDS))

    def test_main_places_portal_before_mission_and_keeps_home_route(self):
        source = MAIN.read_text(encoding='utf-8')
        ast.parse(source)
        self.assertIn('self.pages.addWidget(self.login_page)', source)
        self.assertIn('self.pages.addWidget(self.operations_home_page)', source)
        self.assertIn('self.pages.addWidget(self.portal_page)', source)
        self.assertLess(source.index('self.pages.addWidget(self.login_page)'),
                        source.index('self.pages.addWidget(self.operations_home_page)'))
        self.assertLess(source.index('self.pages.addWidget(self.portal_page)'),
                        source.index('self.pages.addWidget(self.mission_control_page)'))
        self.assertIn('self.portal_page.route_requested.connect(self.open_portal_route)', source)
        self.assertIn('def show_portal(self)', source)
        self.assertIn('def show_legacy_portal(self)', source)
        self.assertIn('self.pages.setCurrentWidget(self.login_page)', source)
        self.assertIn('self.pages.setCurrentWidget(self.operations_home_page)', source)
        self.assertIn('self.pages.setCurrentWidget(self.portal_page)', source)

    def test_main_preserves_mission_to_personal_handoff(self):
        source = MAIN.read_text(encoding='utf-8')
        self.assertIn('subject_activated.connect(self.open_personal_subject)', source)
        self.assertIn('select_subject(subject_id, access_token)', source)
        self.assertIn('def show_medical_library(self)', source)


if __name__ == '__main__':
    unittest.main()
