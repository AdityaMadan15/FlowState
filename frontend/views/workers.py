"""Workers: the risk board, one worker's detail and the loan acceptance flow."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from api_client import ApiError, get_prediction, get_worker
import components as ui
import state
from format import (
    action_label,
    action_tone,
    inr,
    paid_label,
    paid_tone,
    payout_mode,
    short_address,
    short_hash,
    source_label,
    status_text,
)

FILTERS = {
    "all": "All workers",
    "TRIGGER_PAYOUT": "Payout",
    "OFFER_LOAN": "Loan offered",
    "NONE": "No action",
    "error": "Prediction error",
}


def _worker_card(row: dict[str, Any]) -> None:
    worker = row["worker"]
    prediction = row["prediction"]
    error = row["prediction_error"]
    worker_id = row["worker_id"]
    name = str(worker.get("name") or "Worker")

    header = (
        '<div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">'
        f'<div><div style="font-size:15px;font-weight:650;color:#0C2430">{escape(name)}</div>'
        f'<div class="fs-mono" style="color:#63798A">Worker {worker_id} · '
        f"{escape(short_address(worker.get('address')))}</div></div>"
        f'<div style="display:flex;flex-direction:column;gap:5px;align-items:flex-end">'
        f'{ui.badge(paid_label(worker.get("paid")), paid_tone(worker.get("paid")))}'
        f"</div></div>"
    )
    ui.render(header)

    if error and not prediction:
        st.warning(error)
        if st.button("Retry prediction", key=f"retry_{worker_id}", disabled=st.session_state.busy):
            state.retry_prediction(worker_id)
            st.rerun()
        return

    if not prediction:
        st.info("Prediction unavailable.")
        return

    action = prediction.get("action")
    metrics = st.columns(3)
    metrics[0].metric("Predicted income", inr(prediction.get("predicted_income")))
    metrics[1].metric("Shortfall", inr(prediction.get("shortfall")))
    metrics[2].metric(
        "Loan offered" if action == "OFFER_LOAN" else "Sweep",
        inr(prediction.get("loan_amount"))
        if action == "OFFER_LOAN"
        else inr(prediction.get("sweep_amount")),
    )

    ui.render(
        f'<div style="display:flex;gap:8px;align-items:center;margin:2px 0 0">'
        f"{ui.badge(action_label(action), action_tone(action))}"
        f'<span class="fs-section-meta">Source: {escape(source_label(prediction.get("source")))}</span>'
        f"</div>"
    )

    reasons = prediction.get("reasons")
    if isinstance(reasons, list) and reasons:
        ui.render(ui.reasons_chips(reasons))

    if st.button(
        "Open worker",
        key=f"open_{worker_id}",
        use_container_width=True,
        disabled=st.session_state.busy,
    ):
        state.select_worker(worker_id)
        st.rerun()
def _filtered_rows(rows: list[dict[str, Any]], query: str, action_filter: str) -> list[dict[str, Any]]:
    needle = query.strip().lower()
    selected: list[dict[str, Any]] = []
    for row in rows:
        worker = row["worker"]
        if needle:
            haystack = f"{worker.get('name', '')} {row['worker_id']} {worker.get('address', '')}".lower()
            if needle not in haystack:
                continue
        if action_filter == "error":
            if not row["prediction_error"]:
                continue
        elif action_filter != "all":
            prediction = row["prediction"]
            if not prediction or prediction.get("action") != action_filter:
                continue
        selected.append(row)
    return selected


def _detail_panel() -> None:
    worker = state.selected_worker()
    if worker is None:
        ui.section("Worker detail")
        ui.empty_state(
            "No worker selected.",
            "Choose any worker on the board to see their ledger, forecast and loan options.",
        )
        return

    worker_id = int(worker["worker_id"])
    name = str(worker.get("name") or "Worker")
    ui.section("Worker detail", f"Worker {worker_id}")

    try:
        ledger = get_worker(worker_id)
    except ApiError as exc:
        st.error(str(exc))
        if st.button("Retry ledger", key=f"retry_ledger_{worker_id}"):
            st.rerun()
        return

    top = st.columns(3)
    top[0].metric("Balance", inr(ledger.get("balance_inr")))
    top[1].metric("Savings vault", inr(ledger.get("vault_inr")))
    top[2].metric("Loan outstanding", inr(ledger.get("loan_outstanding_inr")))

    prediction = state.prediction_for(worker_id)
    if prediction is None:
        try:
            prediction = get_prediction(worker_id)
        except ApiError as exc:
            st.warning(f"Prediction unavailable: {exc}")

    left, right = st.columns(2, gap="large")
    with left:
        pairs = [
            ("Worker", name),
            ("Worker ID", str(worker_id)),
            ("Payout status", paid_label(worker.get("paid"))),
            ("Address", short_address(worker.get("address"))),
        ]
        ui.render(f'<div class="fs-card">{ui.kv_table(pairs)}</div>')
        with st.expander("Full worker address"):
            st.code(str(worker.get("address") or "Not reported"), language=None)

    with right:
        tx_hash = ledger.get("last_payout_tx")
        if tx_hash:
            mode = state.payout_mode_for(tx_hash)
            label, tone = payout_mode(mode)
            ui.render(
                '<div class="fs-card">'
                '<div class="fs-card-title">Last payout transaction</div>'
                f'<div style="margin:10px 0">{ui.badge(label, tone)}</div>'
                f'<div class="fs-mono" style="color:#3C5563">{escape(short_hash(tx_hash))}</div>'
                "</div>"
            )
            with st.expander("Full transaction hash"):
                st.code(str(tx_hash), language=None)
        else:
            ui.render(
                '<div class="fs-card">'
                '<div class="fs-card-title">Last payout transaction</div>'
                '<p class="fs-card-note" style="margin-top:8px">'
                "No payout has been recorded for this worker yet."
                "</p></div>"
            )

    if prediction:
        ui.section("Forecast", source_label(prediction.get("source")))
        weather = prediction.get("weather") or {}
        stripes = st.columns(4)
        stripes[0].metric("Scenario", str(weather.get("scenario", "Not reported")).capitalize())
        stripes[1].metric("Rain", f"{weather.get('rain_mm')} mm" if weather.get("rain_mm") is not None else "—")
        stripes[2].metric("AQI", str(weather.get("aqi", "—")))
        stripes[3].metric("Predicted income", inr(prediction.get("predicted_income")))

        ui.render(
            f'<div style="display:flex;gap:8px;align-items:center;margin:12px 0 0">'
            f"{ui.badge(action_label(prediction.get('action')), action_tone(prediction.get('action')))}"
            f'<span class="fs-section-meta">Shortfall {escape(inr(prediction.get("shortfall")))}</span>'
            f"</div>"
        )
        reasons = prediction.get("reasons")
        if isinstance(reasons, list) and reasons:
            ui.render(ui.reasons_chips(reasons))

        if prediction.get("action") == "OFFER_LOAN":
            outstanding = ledger.get("loan_outstanding_inr")
            blocked = outstanding not in (None, 0)
            st.markdown(
                f"**Loan on offer: {inr(prediction.get('loan_amount'))}** · repaid from future earnings"
            )
            if blocked:
                st.info("This worker already has an outstanding loan, so a new one cannot be accepted.")
            if st.button(
                "Review and accept loan",
                type="primary",
                use_container_width=True,
                disabled=blocked or st.session_state.busy,
                key=f"loan_{worker_id}",
            ):
                st.session_state.pending_loan = {
                    "worker_id": worker_id,
                    "name": name,
                    "amount": prediction.get("loan_amount"),
                }
                st.session_state.dialog = "loan"
                st.rerun()

    result = st.session_state.loan_result
    if isinstance(result, dict) and int(result.get("worker_id", -1)) == worker_id:
        st.success(
            f"Backend returned the updated ledger after acceptance — balance "
            f"{inr(result.get('balance_inr'))}, outstanding {inr(result.get('loan_outstanding_inr'))}."
        )


def render() -> None:
    rows = state.worker_rows()
    counts = state.action_counts()
    chips = [
        ui.badge(f"{counts['TRIGGER_PAYOUT']} payout eligible", "ok" if counts["TRIGGER_PAYOUT"] else "idle"),
        ui.badge(f"{counts['OFFER_LOAN']} loan offers", "warn" if counts["OFFER_LOAN"] else "idle"),
        ui.badge(f"{counts['NONE']} stable", "idle"),
    ]
    ui.page_header(
        "Workers",
        "Ten riders, one forecast each.",
        "Every row is produced by the backend for the current scenario. Predicted income is "
        "compared with the survival threshold to decide between a parametric payout, a small "
        "loan, or no action.",
        chips,
    )

    for level, message in state.drain_flash():
        getattr(st, level)(message)

    if st.session_state.workers_error:
        st.error(st.session_state.workers_error)
        if st.button("Retry worker list"):
            state.refresh_all()
            st.rerun()
        return

    if not rows:
        ui.empty_state("The backend returned no workers.")
        return

    board_tab, phone_tab = st.tabs(["Risk board", "Worker view"])
    with board_tab:
        with st.container(border=True):
            search_col, filter_col = st.columns([2, 1], vertical_alignment="bottom")
            query = search_col.text_input(
                "Search", placeholder="Name, worker ID or address", key="worker_search"
            )
            action_filter = filter_col.selectbox(
                "Action",
                list(FILTERS.keys()),
                format_func=lambda key: FILTERS[key],
                key="worker_filter",
            )

        filtered = _filtered_rows(rows, query, action_filter)
        if not filtered:
            ui.empty_state("No workers match this filter.", "Clear the search or pick All workers.")
        else:
            st.caption(f"{len(filtered)} of {len(rows)} workers shown")
            columns = st.columns(2, gap="medium")
            for index, row in enumerate(filtered):
                with columns[index % 2]:
                    with st.container(border=True):
                        _worker_card(row)

    with phone_tab:
        if not st.session_state.workers:
            ui.empty_state("No worker data is available.")
        else:
            worker_ids = [int(worker["worker_id"]) for worker in st.session_state.workers]
            current = st.session_state.selected_worker_id
            selected_index = worker_ids.index(current) if current in worker_ids else 0
            chosen_id = st.selectbox(
                "Choose a worker", worker_ids, index=selected_index,
                format_func=lambda wid: next(
                    f"{worker.get('name') or 'Worker'} · #{wid}"
                    for worker in st.session_state.workers
                    if int(worker["worker_id"]) == wid
                ),
                key="worker_phone_select",
            )
            state.select_worker(int(chosen_id))
            chosen = next(w for w in st.session_state.workers if int(w["worker_id"]) == int(chosen_id))
            pred = state.prediction_for(int(chosen_id))
            with st.container(border=True):
                st.markdown(f"### {escape(str(chosen.get('name') or 'Worker'))}")
                st.caption(f"Worker #{chosen_id} · {escape(short_address(chosen.get('address')))}")
                st.metric("Forecasted income", inr(pred.get("predicted_income")) if pred else "Unavailable")
                if pred:
                    st.markdown(f"**{action_label(pred.get('action'))}** · {source_label(pred.get('source'))}")
                    if pred.get("action") == "OFFER_LOAN":
                        st.info(f"Loan offer: {inr(pred.get('loan_amount'))}")
                    tx = next(
                        (p for p in st.session_state.payouts if p.get("worker_id") == int(chosen_id)),
                        None,
                    )
                    if tx:
                        label, _tone = payout_mode(tx.get("mock"))
                        st.success(f"Safety payout received · {label} · {short_hash(tx.get('tx_hash'))}")
                    elif chosen.get("paid") is True:
                        st.info("Payout received. Transaction mode is not available in the current payout response.")
                    elif chosen.get("paid") is False:
                        st.caption("No safety payout is reported for this worker yet.")
                else:
                    error = state.prediction_error_for(int(chosen_id))
                    st.warning(error or "Prediction unavailable.")

    _detail_panel()
