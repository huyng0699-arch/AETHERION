"""Contract tests for Q-0028 mobile/watch event contract."""

from datetime import datetime
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "packages" / "contracts" / "mobile_watch_event.schema.json"


def validate_mobile_watch_event(event: dict, schema: dict) -> None:
    required = set(schema["required"])
    missing = required - set(event.keys())
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    extra = set(event.keys()) - set(schema["properties"].keys())
    if extra:
        raise ValueError(f"unexpected fields: {sorted(extra)}")

    if not str(event["device_id"]).strip():
        raise ValueError("device_id must be non-empty")
    if event["device_type"] not in schema["properties"]["device_type"]["enum"]:
        raise ValueError(f"invalid device_type: {event['device_type']}")
    if event["ack_status"] not in schema["properties"]["ack_status"]["enum"]:
        raise ValueError(f"invalid ack_status: {event['ack_status']}")
    if event["authoritative_source"] != "server" or event["client_is_authoritative"] is not False:
        raise ValueError("server must remain the sole authority")
    if event["ack_status"] == "ACCEPTED" and event.get("server_observation_id") is None:
        raise ValueError("ACCEPTED events must carry server_observation_id")

    dt = datetime.fromisoformat(event["captured_at"])
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("captured_at must include timezone offset")


class MobileWatchEventContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_valid_watch_event_with_server_ack_passes(self) -> None:
        event = {
            "event_id": "mw-evt-001",
            "device_id": "watch-crew1-a1",
            "device_type": "WATCH",
            "subject_id": "CREW-1",
            "scope": "CREW",
            "event_kind": "CREW_CHECKIN",
            "idempotency_key": "watch-crew1-a1:001",
            "ack_status": "ACCEPTED",
            "ack_at": "2026-11-14T05:10:01+00:00",
            "server_observation_id": 42,
            "authoritative_source": "server",
            "client_is_authoritative": False,
            "captured_at": "2026-11-14T05:10:00+00:00",
        }
        validate_mobile_watch_event(event, self.schema)

    def test_client_authority_claim_or_missing_server_id_rejected(self) -> None:
        bad_authority = {
            "event_id": "mw-evt-002",
            "device_id": "mobile-crew1-01",
            "device_type": "MOBILE",
            "subject_id": "CREW-1",
            "scope": "CREW",
            "event_kind": "ALERT_ACK",
            "idempotency_key": "mobile-crew1-01:002",
            "ack_status": "ACCEPTED",
            "ack_at": "2026-11-14T05:10:01+00:00",
            "server_observation_id": 43,
            "authoritative_source": "client",
            "client_is_authoritative": True,
            "captured_at": "2026-11-14T05:10:00+00:00",
        }
        with self.assertRaises(ValueError):
            validate_mobile_watch_event(bad_authority, self.schema)

        missing_ack_id = dict(bad_authority)
        missing_ack_id["authoritative_source"] = "server"
        missing_ack_id["client_is_authoritative"] = False
        missing_ack_id["server_observation_id"] = None
        with self.assertRaises(ValueError):
            validate_mobile_watch_event(missing_ack_id, self.schema)


if __name__ == "__main__":
    unittest.main()
