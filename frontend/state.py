"""Session state and backend orchestration for the FlowState dashboard.

All API traffic for the dashboard snapshot funnels through here so views stay
presentational. Streamlit is never called from a worker thread: predictions are
fetched concurrently, then rendered on the main thread.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Callable

import streamlit as st

from api_client import (
    ApiError,
    accept_loan as api_accept_loan,
    get_health,
    get_payouts,
    get_prediction,
    get_weather,
    get_workers,
    reset_demo as api_reset_demo,
    set_scenario as api_set_scenario,
    simulate_storm as api_simulate_storm,
)

MAX_PREDICTION_THREADS = 8

DEFAULTS: dict[str, Any] = {
    "view": "overview",
    "health": None,
    "health_error": None,
    "weather": None,
    "weather_error": None,
    "workers": [],
    "workers_error": None,
    "predictions": {},
    "payouts": [],
    "payouts_error": None,
    "last_updated": None,
    "flash": [],
    "busy": False,
    "storm_result": None,
    "loan_result": None,
    "selected_worker_id": None,
    "dialog": None,
    "pending_loan": None,
    "request_id": 0,
    "auto_refresh": False,
    "booted": False,
    "auth_token": None,
    "auth_user": None,
}


def now_label() -> str:
    return datetime.now().astimezone().strftime("%d %b %Y · %I:%M:%S %p")


def init() -> None:
    """Create every session key once, with explicit defaults."""
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _next_request_id() -> int:
    st.session_state.request_id += 1
    return st.session_state.request_id


def flash(level: str, message: str) -> None:
    """Queue a message shown once on the next render."""
    st.session_state.flash.append((level, message))


def drain_flash() -> list[tuple[str, str]]:
    pending = list(st.session_state.flash)
    st.session_state.flash = []
    return pending


# --- reads ------------------------------------------------------------------


def _load_health_and_weather() -> None:
    try:
        health = get_health()
        st.session_state.health = health
        st.session_state.health_error = None
    except ApiError as exc:
        st.session_state.health = None
        st.session_state.health_error = str(exc)
        return

    try:
        st.session_state.weather = get_weather()
        st.session_state.weather_error = None
    except ApiError as exc:
        st.session_state.weather = None
        st.session_state.weather_error = str(exc)


def _fetch_predictions(workers: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Fetch every worker prediction concurrently; failures stay per-worker."""
    results: dict[int, dict[str, Any]] = {}
    if not workers:
        return results

    worker_ids = [int(worker["worker_id"]) for worker in workers]
    with ThreadPoolExecutor(max_workers=min(MAX_PREDICTION_THREADS, len(worker_ids))) as pool:
        futures = {pool.submit(get_prediction, wid): wid for wid in worker_ids}
        for future in as_completed(futures):
            worker_id = futures[future]
            try:
                results[worker_id] = {"data": future.result(), "error": None}
            except ApiError as exc:
                results[worker_id] = {"data": None, "error": str(exc)}
            except (KeyError, TypeError, ValueError) as exc:
                results[worker_id] = {
                    "data": None,
                    "error": f"Prediction payload could not be read: {exc}",
                }
    return results


def _load_workers() -> bool:
    try:
        workers = get_workers()
    except ApiError as exc:
        st.session_state.workers_error = str(exc)
        return False

    st.session_state.workers = workers
    st.session_state.workers_error = None
    st.session_state.predictions.update(_fetch_predictions(workers))
    return True


def _load_payouts() -> bool:
    try:
        payouts = get_payouts()
    except ApiError as exc:
        st.session_state.payouts_error = str(exc)
        return False
    st.session_state.payouts = payouts
    st.session_state.payouts_error = None
    return True


def refresh_all() -> None:
    """Reload the full dashboard snapshot from the backend."""
    if st.session_state.busy:
        return
    st.session_state.busy = True
    request_id = _next_request_id()
    try:
        _load_health_and_weather()
        if st.session_state.health is None:
            return
        if st.session_state.request_id != request_id:
            return
        _load_workers()
        _load_payouts()
        st.session_state.last_updated = now_label()
        st.session_state.booted = True
    finally:
        st.session_state.busy = False


def refresh_after_mutation() -> None:
    """Reload everything after a mutation changed backend state."""
    _load_health_and_weather()
    if st.session_state.health is not None:
        _load_workers()
    _load_payouts()
    st.session_state.last_updated = now_label()


def retry_prediction(worker_id: int) -> None:
    """Re-fetch one worker's prediction without touching the rest of the table."""
    try:
        data = get_prediction(worker_id)
    except ApiError as exc:
        st.session_state.predictions[worker_id] = {"data": None, "error": str(exc)}
        return
    st.session_state.predictions[worker_id] = {"data": data, "error": None}
# --- mutations --------------------------------------------------------------


def _run(action: Callable[[], Any], success_message: str) -> Any | None:
    """Execute a mutating call behind a busy guard and refresh state after it."""
    if st.session_state.busy:
        return None
    st.session_state.busy = True
    try:
        result = action()
        refresh_after_mutation()
        flash("success", success_message)
        return result
    except ApiError as exc:
        flash("error", str(exc))
        return None
    finally:
        st.session_state.busy = False


def change_scenario(name: str) -> None:
    """Switch the backend demo scenario; predictions are re-fetched afterwards."""
    _run(
        lambda: api_set_scenario(name),
        f"Backend scenario switched to {name}. Predictions reloaded.",
    )


def run_storm() -> None:
    """Trigger the parametric payout simulation."""
    result = _run(
        api_simulate_storm,
        "Storm simulation finished. Ledger and payout records reloaded.",
    )
    if result is not None:
        st.session_state.storm_result = result
        st.session_state.loan_result = None


def reset_demo() -> None:
    """Clear the demo ledger, payout log and scenario."""
    result = _run(api_reset_demo, "Demo reset. Ledger, payouts and scenario restored.")
    if result is not None:
        st.session_state.storm_result = None
        st.session_state.loan_result = None


def accept_loan(worker_id: int) -> dict[str, Any] | None:
    """Accept the backend's current loan offer for one worker."""
    result = _run(
        lambda: api_accept_loan(worker_id),
        "Loan accepted. The worker ledger was reloaded from the backend.",
    )
    if result is not None:
        st.session_state.loan_result = result
        st.session_state.selected_worker_id = worker_id
    return result


# --- derived helpers --------------------------------------------------------


def prediction_for(worker_id: int) -> dict[str, Any] | None:
    entry = st.session_state.predictions.get(worker_id)
    return entry.get("data") if entry else None


def prediction_error_for(worker_id: int) -> str | None:
    entry = st.session_state.predictions.get(worker_id)
    if not entry:
        return "Prediction has not been loaded yet."
    return entry.get("error")


def worker_rows() -> list[dict[str, Any]]:
    """Join worker identity with its prediction for table rendering."""
    rows: list[dict[str, Any]] = []
    for worker in st.session_state.workers:
        worker_id = int(worker["worker_id"])
        rows.append(
            {
                "worker": worker,
                "worker_id": worker_id,
                "prediction": prediction_for(worker_id),
                "prediction_error": prediction_error_for(worker_id),
            }
        )
    return rows


def selected_worker() -> dict[str, Any] | None:
    target = st.session_state.selected_worker_id
    if target is None:
        return None
    for worker in st.session_state.workers:
        if int(worker["worker_id"]) == target:
            return worker
    return None


def select_worker(worker_id: int) -> None:
    st.session_state.selected_worker_id = worker_id


def payout_mode_for(tx_hash: object) -> bool | None:
    """Look up whether a transaction hash came from the chain or a mock path."""
    if not tx_hash:
        return None
    for record in st.session_state.payouts:
        if record.get("tx_hash") == tx_hash:
            return record.get("mock")
    return None


def action_counts() -> dict[str, int]:
    """Count workers per backend action, from already-loaded predictions."""
    counts = {"TRIGGER_PAYOUT": 0, "OFFER_LOAN": 0, "NONE": 0, "unknown": 0}
    for worker in st.session_state.workers:
        entry = st.session_state.predictions.get(int(worker["worker_id"]))
        action = (entry or {}).get("data", {}).get("action") if entry else None
        if action in counts:
            counts[action] += 1
        else:
            counts["unknown"] += 1
    return counts
