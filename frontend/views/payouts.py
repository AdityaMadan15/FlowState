"""Payout ledger: every settlement record the backend returns."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

import components as ui
import state
from format import inr, payout_mode, short_address, short_hash


def _row(payout: dict[str, Any]) -> None:
    label, tone = payout_mode(payout.get("mock"))
    ui.render(
        '<div class="fs-card" style="margin-bottom:8px">'
        '<div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start">'
        f'<div><div style="font-size:14px;font-weight:650;color:#0C2430">'
        f'{escape(str(payout.get("name") or "Worker"))}</div>'
        f'<div class="fs-mono" style="color:#63798A">Worker '
        f'{escape(str(payout.get("worker_id", "—")))} · '
        f"{escape(short_address(payout.get('address')))}</div>"
        f'<div class="fs-mono" style="color:#3C5563;margin-top:8px">'
        f"{escape(short_hash(payout.get('tx_hash')))}</div></div>"
        f'<div style="text-align:right;flex:none"><div style="font-size:17px;font-weight:650;'
        f'color:#0C2430;font-variant-numeric:tabular-nums">{escape(inr(payout.get("amount")))}</div>'
        f'<div style="margin-top:6px">{ui.badge(label, tone)}</div></div></div></div>'
    )
    with st.expander(f"Transaction hashes · {payout.get('name', 'Worker')}"):
        st.code(str(payout.get("tx_hash") or "Not reported"), language=None)
        st.code(str(payout.get("address") or "Not reported"), language=None)


def render() -> None:
    payouts = st.session_state.payouts
    on_chain = sum(1 for record in payouts if record.get("mock") is False)
    mock = sum(1 for record in payouts if record.get("mock") is True)

    ui.page_header(
        "Payout ledger",
        "Every settlement, in order.",
        "The ledger is read straight from GET /api/payouts, newest first. Each record states "
        "whether the transfer settled on the local chain or fell back to a mock hash, so the "
        "demo never overclaims.",
        [
            ui.badge(f"{len(payouts)} records", "idle"),
            ui.badge(f"{on_chain} on-chain", "ok" if on_chain else "idle"),
            ui.badge(f"{mock} mock", "warn" if mock else "idle"),
        ],
    )

    for level, message in state.drain_flash():
        getattr(st, level)(message)

    if st.session_state.payouts_error:
        st.error(st.session_state.payouts_error)
        if st.button("Retry payout history"):
            state.refresh_all()
            st.rerun()
        return

    ui.stat_row(
        [
            {"label": "Records", "value": str(len(payouts)), "meta": "Payout log entries"},
            {
                "label": "On-chain",
                "value": str(on_chain),
                "meta": "Confirmed by the local Hardhat node",
            },
            {
                "label": "Mock",
                "value": str(mock),
                "meta": "Fallback hash when the chain is unavailable",
            },
        ]
    )

    ui.section("Records", "Newest first, as returned by the API")
    if not payouts:
        ui.empty_state(
            "No payout records yet.",
            "Run the storm console to create settlements, then return here.",
        )
        return

    for payout in payouts:
        _row(payout)

    st.caption(
        "The backend does not return timestamps for payout records, so ordering is the only "
        "time signal available and no dates are invented here."
    )
