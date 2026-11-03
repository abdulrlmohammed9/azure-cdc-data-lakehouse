"""Reproducible, standard-library-only CDC demo using synthetic e-commerce events.

Bronze = raw CSV events; Silver = latest non-deleted order per key;
Gold = aggregate revenue/order counts by customer and region.
This is a LOCAL educational implementation, not Azure Data Factory or Delta Lake.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def apply_cdc(events: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    """Apply insert/update/delete events in sequence order; latest event wins."""
    state: dict[str, dict[str, str]] = {}
    last_sequence: dict[str, int] = {}
    for event in sorted(events, key=lambda e: (int(e["sequence"]), int(e["event_id"]))):
        key = event["order_id"]
        seq = int(event["sequence"])
        if seq <= last_sequence.get(key, -1):
            continue
        operation = event["operation"].upper()
        if operation == "D":
            state.pop(key, None)
        elif operation in {"I", "U"}:
            state[key] = {k: event[k] for k in ("order_id", "customer_id", "order_date", "amount")}
        else:
            raise ValueError(f"Unsupported CDC operation: {operation}")
        last_sequence[key] = seq
    return state


def aggregate_orders(orders: dict[str, dict[str, str]], customers: list[dict[str, str]]) -> list[dict]:
    customer_index = {r["customer_id"]: r for r in customers}
    totals: dict[str, dict] = defaultdict(lambda: {"order_count": 0, "revenue": 0.0})
    for order in orders.values():
        cid = order["customer_id"]
        if cid not in customer_index:
            raise ValueError(f"Missing customer dimension for {cid}")
        totals[cid]["order_count"] += 1
        totals[cid]["revenue"] += float(order["amount"])
    return [
        {"customer_id": cid, "customer_name": customer_index[cid]["customer_name"],
         "region": customer_index[cid]["region"], "order_count": stats["order_count"],
         "revenue": round(stats["revenue"], 2)}
        for cid, stats in sorted(totals.items())
    ]


def run(input_dir: Path, output_dir: Path) -> list[dict]:
    events = read_csv(input_dir / "ecommerce_orders_cdc.csv")
    customers = read_csv(input_dir / "erp_customers.csv")
    orders = apply_cdc(events)
    gold = aggregate_orders(orders, customers)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "silver_orders.json").write_text(
        json.dumps([orders[k] for k in sorted(orders)], indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "gold_customer_revenue.json").write_text(
        json.dumps(gold, indent=2) + "\n", encoding="utf-8"
    )
    return gold


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run synthetic CDC local demo")
    parser.add_argument("--input", type=Path, default=ROOT / "sample-data")
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output), indent=2))
