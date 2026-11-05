"""Capture and validate real Citi Bike GBFS data.

Only stdlib; no API keys. Output is a single latest snapshot for controlled
ingestion into Databricks. The operator must explicitly sync/upload new versions.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.request import Request, urlopen

STATUS_URL = "https://gbfs.citibikenyc.com/gbfs/en/station_status.json"
INFO_URL = "https://gbfs.citibikenyc.com/gbfs/en/station_information.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "data" / "latest_snapshot.json"


def fetch_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "cdc-lakehouse-portfolio/1.0"})
    with urlopen(request, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status} from Citi Bike GBFS")
        return json.load(response)


def extract_stations(feed: dict, label: str) -> list[dict]:
    stations = feed.get("data", {}).get("stations")
    if not isinstance(stations, list) or not stations:
        raise ValueError(f"{label}: missing or empty data.stations")
    result = {}
    for station in stations:
        if not isinstance(station, dict) or not str(station.get("station_id", "")).strip():
            raise ValueError(f"{label}: station missing station_id")
        station_id = str(station["station_id"])
        if station_id in result:
            raise ValueError(f"{label}: duplicate station_id {station_id}")
        result[station_id] = station
    return list(result.values())


def _int_nonnegative(value, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value or value < 0:
        raise ValueError(f"Invalid {field}: {value!r}")
    return int(value)


def _name(value) -> str | None:
    # Older GBFS uses a string; newer GBFS can use localized objects.
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value:
        first = next((x for x in value if isinstance(x, dict) and x.get("text")), None)
        return str(first["text"]) if first else None
    return None


def normalize(status_feed: dict, info_feed: dict, captured_at: str) -> dict:
    status = extract_stations(status_feed, "station_status")
    info = {str(s["station_id"]): s for s in extract_stations(info_feed, "station_information")}
    try:
        datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("captured_at must be an ISO 8601 timestamp") from exc
    records = []
    for s in status:
        sid = str(s["station_id"])
        meta = info.get(sid, {})
        bikes_raw = s.get("num_bikes_available", s.get("num_vehicles_available"))
        docks_raw = s.get("num_docks_available")
        if bikes_raw is None or docks_raw is None:
            raise ValueError(f"Station {sid}: missing bikes/docks availability")
        bikes = _int_nonnegative(bikes_raw, "bikes_available")
        docks = _int_nonnegative(docks_raw, "docks_available")
        capacity = meta.get("capacity")
        records.append({
            "station_id": sid,
            "station_name": _name(meta.get("name")),
            "latitude": float(meta["lat"]) if meta.get("lat") is not None else None,
            "longitude": float(meta["lon"]) if meta.get("lon") is not None else None,
            "capacity": _int_nonnegative(capacity, "capacity") if capacity is not None else None,
            "bikes_available": bikes,
            "docks_available": docks,
            "is_renting": bool(s.get("is_renting", False)),
            "is_returning": bool(s.get("is_returning", False)),
        })
    return {
        "source": "Citi Bike GBFS public station snapshots",
        "captured_at": captured_at,
        "station_status_last_updated": status_feed.get("last_updated"),
        "station_information_last_updated": info_feed.get("last_updated"),
        "station_count": len(records),
        "stations": sorted(records, key=lambda x: x["station_id"]),
    }


def run(output: Path = DEFAULT_OUTPUT) -> dict:
    status = fetch_json(STATUS_URL)
    info = fetch_json(INFO_URL)
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    normalized = normalize(status, info, captured_at)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(normalized, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    return normalized


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    data = run(args.output)
    print(f"Captured {data['station_count']} station records at {data['captured_at']} -> {args.output}")
