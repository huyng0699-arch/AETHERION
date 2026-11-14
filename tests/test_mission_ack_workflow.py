import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACK_PATH = ROOT / "apps" / "desktop" / "src" / "aetherion_desktop" / "features" / "mission" / "ack_workflow.py"


def _load_ack():
    spec = importlib.util.spec_from_file_location("mission_ack_workflow_test", ACK_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestMissionAckWorkflow(unittest.TestCase):
    def test_valid_ack_updates_state_without_creating_incident(self):
        m = _load_ack()
        initial = (
            m.IncidentAckState("EVT-101"),
            m.IncidentAckState("EVT-102"),
        )
        res = m.apply_incident_ack(
            initial,
            event_id="EVT-101",
            operator_id="FLIGHT-SURGEON-1",
            access_token="tok-abc",
            http_status=200,
            payload={
                "event_id": "EVT-101",
                "ack_state": "ACKNOWLEDGED",
                "acknowledged_by": "FLIGHT-SURGEON-1",
                "acknowledged_at": "2026-11-14T11:02:00Z",
            },
            note="Reviewed telemetry",
        )
        self.assertEqual(res.status, "ACKNOWLEDGED")
        self.assertFalse(res.incident_created)
        self.assertEqual(len(res.events), len(initial))
        self.assertEqual(res.events[0].ack_state, "ACKNOWLEDGED")
        self.assertEqual(res.events[1].ack_state, "UNACKNOWLEDGED")

    def test_unknown_event_and_error_do_not_create_incident_or_mutate_state(self):
        m = _load_ack()
        initial = (m.IncidentAckState("EVT-101"),)

        not_found = m.apply_incident_ack(
            initial, "EVT-999", "OP-1", "tok", 200,
            {"event_id": "EVT-999", "ack_state": "ACKNOWLEDGED", "acknowledged_by": "OP-1", "acknowledged_at": "2026-11-14T11:02:00Z"},
        )
        self.assertEqual(not_found.status, "NOT_FOUND")
        self.assertFalse(not_found.incident_created)
        self.assertEqual(len(not_found.events), 1)

        denied = m.apply_incident_ack(initial, "EVT-101", "OP-1", "", 200, {})
        self.assertEqual(denied.status, "DENIED")

        err = m.apply_incident_ack(initial, "EVT-101", "OP-1", "tok", 500, {"detail": "fail"})
        self.assertEqual(err.status, "ERROR")
        self.assertEqual(err.events[0].ack_state, "UNACKNOWLEDGED")


if __name__ == "__main__":
    unittest.main()
