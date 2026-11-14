from __future__ import annotations

import socket
import unittest
from unittest.mock import patch

from knowledge.nasa.offline_literature import load_offline_nasa_library


class TestNasaOfflineLiterature(unittest.TestCase):
    def test_loads_all_packaged_references_and_five_hazards_with_network_disconnected(self) -> None:
        with patch.object(socket, "create_connection", side_effect=OSError("Internet disconnected")):
            lib = load_offline_nasa_library()

        self.assertTrue(lib["offline_mode"])
        self.assertFalse(lib["is_live_telemetry"])
        self.assertEqual(
            set(lib["hazards"].keys()),
            {
                "space_radiation",
                "isolation_and_confinement",
                "distance_from_earth",
                "gravity_fields",
                "hostile_closed_environments",
            },
        )
        self.assertEqual(lib["cliff_119_status"]["verification_status"], "NOT_IMPORTED")
        self.assertEqual(len(lib["osdr_datasets"]["datasets"]), 5)


if __name__ == "__main__":
    unittest.main()
