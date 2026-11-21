"""Exercise the FlowState API end to end using HTTP requests."""

from __future__ import annotations

import argparse

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--expect-mock", action="store_true")
    parser.add_argument("--expect-fallback", action="store_true")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/") + "/api"

    def get(path: str):
        response = requests.get(f"{base_url}{path}", timeout=10)
        response.raise_for_status()
        return response.json()

    def post(path: str):
        response = requests.post(f"{base_url}{path}", timeout=180)
        response.raise_for_status()
        return response.json()

    post("/reset")
    try:
        clear_predictions = [get(f"/predict/{worker_id}") for worker_id in range(1, 11)]
        assert all(item["weather"]["scenario"] == "clear" for item in clear_predictions)
        assert all(item["action"] == "NONE" for item in clear_predictions)
        expected_source = "fallback" if args.expect_fallback else "model"
        assert all(item["source"] == expected_source for item in clear_predictions), [
            item["source"] for item in clear_predictions
        ]

        first = post("/simulate-storm")
        assert first["payouts_triggered"] == 10, first
        assert first["total_amount"] == 5000, first
        assert len(first["payouts"]) == 10
        expected_mock = args.expect_mock
        assert all(item["mock"] is expected_mock for item in first["payouts"]), [
            item["mock"] for item in first["payouts"]
        ]

        second = post("/simulate-storm")
        assert second["payouts_triggered"] == 0 and second["payouts"] == [], second
        payout_log = get("/payouts")
        assert len(payout_log) == 10
        assert [item["worker_id"] for item in payout_log] == list(range(10, 0, -1))
        storm_predictions = [get(f"/predict/{worker_id}") for worker_id in range(1, 11)]
        assert all(item["weather"]["scenario"] == "storm" for item in storm_predictions)
        assert all(item["action"] == "TRIGGER_PAYOUT" for item in storm_predictions)
        assert all(item["source"] == expected_source for item in storm_predictions)

        post("/reset")
        post("/scenario/rainy")
        rainy_predictions = [get(f"/predict/{worker_id}") for worker_id in range(1, 11)]
        eligible = [item for item in rainy_predictions if item["action"] == "OFFER_LOAN"]
        print("Rainy scenario loan offers:", ", ".join(item["name"] for item in eligible))
        assert eligible, "Rainy scenario did not offer a loan to any worker"
        worker_id = eligible[0]["worker_id"]
        accepted = post(f"/loan/accept/{worker_id}")
        assert accepted["loan_outstanding_inr"] == eligible[0]["loan_amount"]
        rejected = requests.post(f"{base_url}/loan/accept/{worker_id}", timeout=10)
        assert rejected.status_code == 400, rejected.text
        print(f"Accepted loan for worker {worker_id}; duplicate acceptance returned HTTP 400.")
        print(
            f"PASS: source={expected_source}, mock={expected_mock}; "
            "10 storm payouts (INR 5000), repeat skipped, payout log newest-first."
        )
    finally:
        post("/reset")


if __name__ == "__main__":
    main()
