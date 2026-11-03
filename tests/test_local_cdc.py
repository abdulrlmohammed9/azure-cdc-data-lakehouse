from pathlib import Path

import pytest

from src.local_cdc import aggregate_orders, apply_cdc, run

ROOT = Path(__file__).resolve().parents[1]


def test_insert_update_delete_and_latest_wins():
    events = [
        {"event_id": "1", "sequence": "1", "order_id": "A", "customer_id": "C1", "order_date": "2026-01-01", "amount": "10", "operation": "I"},
        {"event_id": "2", "sequence": "2", "order_id": "A", "customer_id": "C1", "order_date": "2026-01-01", "amount": "15", "operation": "U"},
        {"event_id": "3", "sequence": "3", "order_id": "B", "customer_id": "C1", "order_date": "2026-01-01", "amount": "20", "operation": "I"},
        {"event_id": "4", "sequence": "4", "order_id": "B", "customer_id": "C1", "order_date": "2026-01-01", "amount": "20", "operation": "D"},
    ]
    assert apply_cdc(events) == {"A": {"order_id": "A", "customer_id": "C1", "order_date": "2026-01-01", "amount": "15"}}


def test_unknown_cdc_operation():
    with pytest.raises(ValueError, match="Unsupported"):
        apply_cdc([{"event_id": "1", "sequence": "1", "order_id": "A", "operation": "X"}])


def test_synthetic_example(tmp_path):
    result = run(ROOT / "sample-data", tmp_path)
    assert result == [
        {"customer_id": "C001", "customer_name": "Acme Retail", "region": "West", "order_count": 1, "revenue": 125.0},
        {"customer_id": "C003", "customer_name": "Cedar Markets", "region": "East", "order_count": 1, "revenue": 40.0},
    ]
    assert (tmp_path / "silver_orders.json").exists()
    assert (tmp_path / "gold_customer_revenue.json").exists()
