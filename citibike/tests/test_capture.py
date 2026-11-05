"""Offline tests: small fake GBFS data only. No API requests."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from citibike.capture import normalize, run


class CitiBikeCaptureTests(unittest.TestCase):
    def setUp(self):
        self.status = {
            "last_updated": 1750000000,
            "data": {"stations": [
                {"station_id": "A", "num_bikes_available": 4, "num_docks_available": 6,
                 "is_renting": True, "is_returning": True},
                {"station_id": "B", "num_bikes_available": 0, "num_docks_available": 8,
                 "is_renting": False, "is_returning": True},
            ]}
        }
        self.info = {"data": {"stations": [
            {"station_id": "A", "name": "Station A", "lat": 40.1, "lon": -73.9, "capacity": 10},
            {"station_id": "B", "name": [{"language": "en", "text": "Station B"}],
             "lat": 40.2, "lon": -73.8, "capacity": 8},
        ]}}

    def test_normalizes_station_records(self):
        result = normalize(self.status, self.info, "2026-11-05T00:00:00Z")
        self.assertEqual(result["station_count"], 2)
        self.assertEqual(result["stations"][0]["bikes_available"], 4)
        self.assertEqual(result["stations"][1]["station_name"], "Station B")
        self.assertFalse(result["stations"][1]["is_renting"])

    def test_rejects_duplicate_stations(self):
        self.status["data"]["stations"].append(dict(self.status["data"]["stations"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            normalize(self.status, self.info, "2026-11-05T00:00:00Z")

    def test_rejects_negative_counts(self):
        self.status["data"]["stations"][0]["num_bikes_available"] = -3
        with self.assertRaisesRegex(ValueError, "Invalid"):
            normalize(self.status, self.info, "2026-11-05T00:00:00Z")

    def test_accepts_vehicles_available_alias(self):
        s = self.status["data"]["stations"][0]
        s["num_vehicles_available"] = s.pop("num_bikes_available")
        result = normalize(self.status, self.info, "2026-11-05T00:00:00Z")
        self.assertEqual(result["stations"][0]["bikes_available"], 4)

    def test_run_writes_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("citibike.capture.fetch_json", side_effect=[self.status, self.info]):
                result = run(Path(tmp) / "latest_snapshot.json")
            self.assertEqual(result["station_count"], 2)
            self.assertTrue((Path(tmp) / "latest_snapshot.json").exists())


if __name__ == "__main__":
    unittest.main()
