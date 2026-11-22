"""Storm console: the parametric payout demo."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

import components as ui
import state
from format import inr, payout_mode, short_address, short_hash


def _rules_card() -> None:
    ui.render(
        ui.flow_steps(
            [
                ("01", "Weather", "Storm scenario: 80mm rain, AQI 450"),
                ("02", "Predict", "Model forecasts tomorrow's income"),
                ("03", "Decide", "Rain > 50mm or AQI > 400 → payout"),
                ("04", "Settle", "Contract releases funds, ledger updates"),
            ]
        )
    )
    st.caption(
        "The backend owns every rule. The console only asks it to run, then displays the exact "
        "records it returns — including whether each transfer was on-chain or mock."
    )


def _payout_feed(payouts: list[dict[str, Any]]) -> None:
    for payout in payouts:
        label, tone = payout_mode(payout.get("mock"))
        ui.render(
            '<div class="fs-card" style="margin-bottom:8px">'
            '<div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start">'
            f'<div><div style="font-size:14px;font-weight:650;color:#0C2430">'
            f'{escape(str(payout.get("name") or "Worker"))}</div>'
            f'<div class="fs-mono" style="color:#63798A">'
            f'Worker {escape(str(payout.get("worker_id", "—")))} · '
            f"{escape(short_address(payout.get('address')))}</div></div>"
            f'<div style="text-align:right"><div style="font-size:16px;font-weight:650;'
            f'color:#0C2430">{escape(inr(payout.get("amount")))}</div>'
            f'<div style="margin-top:5px">{ui.badge(label, tone)}</div></div></div>'
            f'<div class="fs-mono" style="color:#3C5563;margin-top:10px">'
            f"{escape(short_hash(payout.get('tx_hash')))}</div></div>"
        )
        with st.expander(f"Transaction detail · {payout.get('name', 'Worker')}"):
            st.code(str(payout.get("tx_hash") or "Not reported"), language=None)
            st.code(str(payout.get("address") or "Not reported"), language=None)


def render() -> None:
    health = st.session_state.health or {}
    scenario = health.get("scenario")
    chips = [ui.badge(f"Scenario: {scenario or 'unavailable'}", "warn" if scenario == "storm" else "idle")]
    chain_ok = health.get("chain_connected")
    chips.append(
        ui.badge(
            "Chain connected" if chain_ok is True else "Chain unavailable"
            if chain_ok is False
            else "Chain not reported",
            "ok" if chain_ok is True else "bad" if chain_ok is False else "idle",
        )
    )

    ui.page_header(
        "Storm console",
        "Nobody files a claim.",
        "A storm is a fact, not a prediction. When rainfall or air quality crosses the "
        "threshold, the backend pays every eligible worker through the payout contract without "
        "a form, a claim or a phone call.",
        chips,
    )

    for level, message in state.drain_flash():
        getattr(st, level)(message)

    with st.container(border=True):
        action_col, copy_col = st.columns([1.05, 2.95], vertical_alignment="center")
        with action_col:
            if st.button(
                "Run storm simulation",
                key="storm_run",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.busy,
            ):
                st.session_state.dialog = "storm"
                st.rerun()
        with copy_col:
            st.caption(
                "Preview the severe-weather protection flow. Eligible payouts and settlement "
                "records are returned by the backend."
            )

    info_col, rules_col = st.columns([1, 2], gap="large")
    with info_col:
        with st.container(border=True):
            st.markdown("### Protection when weather turns severe")
            st.write(
                "FlowState monitors weather conditions and uses the protection rules to "
                "identify workers who may need support. Eligible assistance is handled "
                "automatically, without requiring a claim."
            )
            st.caption("Payout amounts and weather values shown here are part of the demo.")

    with rules_col:
        ui.section("How protection works")
        _rules_card()

    result = st.session_state.storm_result
    if isinstance(result, dict):
        ui.section("Latest simulation", "Response from POST /api/simulate-storm")
        ui.stat_row(
            [
                {
                    "label": "Payouts triggered",
                    "value": str(result.get("payouts_triggered", "—")),
                    "meta": "Workers paid in this run",
                },
                {
                    "label": "Total disbursed",
                    "value": inr(result.get("total_amount")),
                    "meta": "Amount reported by the backend",
                },
                {
                    "label": "Records returned",
                    "value": str(len(result.get("payouts") or [])),
                    "meta": "Individual payout records",
                },
            ]
        )

        payouts = result.get("payouts")
        if isinstance(payouts, list) and payouts:
            ui.section("Payout feed", "Newest run, in backend order")
            _payout_feed(payouts)
        elif result.get("payouts_triggered") == 0:
            st.info(
                "The backend returned zero new payouts. Every eligible worker in this demo "
                "ledger has probably been paid already — reset the demo to replay the run."
            )
    else:
        ui.section("Latest simulation")
        ui.empty_state(
            "No storm run in this session yet.",
            "The result panel fills with the backend's real response after you run the console.",
        )

    if st.session_state.payouts:
        ui.section("Full payout ledger", f"{len(st.session_state.payouts)} records")
        st.caption("Newest first, exactly as /api/payouts returns them. Open Payouts for detail.")
