"""Overview: system state, scenario control, risk snapshot and coverage."""

from __future__ import annotations

from typing import Any

import streamlit as st

import components as ui
import coverage
import state
from format import (
    inr,
    number,
    paid_label,
    paid_tone,
    scenario_label,
    status_text,
    status_tone,
    payout_mode,
    short_hash,
)

# The backend decision engine compares predicted income against this value.
SURVIVAL_THRESHOLD_INR = 500.0


def _status_card(label: str, value_label: str, tone: str, note: str) -> str:
    return (
        f'<div class="fs-stat">'
        f'<div class="fs-stat-label">{label}</div>'
        f'<div style="margin:9px 0 7px">{ui.badge(value_label, tone)}</div>'
        f'<div class="fs-stat-meta">{note}</div>'
        f"</div>"
    )


def _health_strip(health: dict[str, Any]) -> None:
    status = str(health.get("status") or "unknown")
    if status == "ok":
        backend_tone, backend_text = "ok", "Healthy"
    elif status == "degraded":
        backend_tone, backend_text = "warn", "Degraded"
    else:
        backend_tone, backend_text = "idle", "Status not reported"

    cards = [
        ("Backend API", backend_text, backend_tone, "GET /api/health"),
        (
            "PostgreSQL",
            status_text(health.get("database_connected")),
            status_tone(health.get("database_connected")),
            "Demo ledger and payout log",
        ),
        (
            "Prediction model",
            status_text(health.get("model_loaded"), yes="Loaded", no="Not loaded"),
            status_tone(health.get("model_loaded")),
            "LightGBM + SHAP assets",
        ),
        (
            "Local blockchain",
            status_text(health.get("chain_connected")),
            status_tone(health.get("chain_connected")),
            "Hardhat contract on :8545",
        ),
    ]

    columns = st.columns(len(cards), gap="small")
    for column, (label, value_label, tone, note) in zip(columns, cards):
        with column:
            ui.render(_status_card(label, value_label, tone, note))


def _impact_tiles() -> None:
    workers = st.session_state.workers
    paid_count = sum(1 for worker in workers if worker.get("paid") is True)
    weather = st.session_state.weather or {}
    health = st.session_state.health or {}
    payouts = st.session_state.payouts

    tiles = [
        {
            "label": "Workers covered",
            "value": str(len(workers)) if workers else "—",
            "meta": "Delivery workers protected by FlowState",
            "badge": "Active" if workers else "Unavailable",
            "tone": "ok" if workers else "idle",
        },
        {
            "label": "Payouts received",
            "value": f"{paid_count} / {len(workers)}" if workers else "—",
            "meta": "Workers paid in this demo run",
            "badge": "Live",
            "tone": "idle",
        },
        {
            "label": "Current scenario",
            "value": scenario_label(health.get("scenario")),
            "meta": "Set by the backend demo state",
            "small": True,
            "badge": "Current",
            "tone": "warn" if health.get("scenario") == "storm" else "ok",
        },
        {
            "label": "Rainfall",
            "value": f"{number(weather.get('rain_mm'))} mm",
            "meta": f"AQI {number(weather.get('aqi'))} · source {weather.get('source', 'not reported')}",
            "badge": "Weather",
            "tone": "warn" if (weather.get("rain_mm") or 0) > 50 else "ok",
        },
    ]

    tiles.append(
        {
            "label": "Payout activity",
            "value": str(len(payouts)),
            "meta": "Recorded worker settlements",
            "badge": "Ledger",
            "tone": "ok" if payouts else "idle",
        }
    )

    ui.stat_row(tiles)


def _risk_snapshot() -> None:
    rows = state.worker_rows()
    chart_rows: list[tuple[str, float, bool]] = []
    highest = SURVIVAL_THRESHOLD_INR
    for row in rows:
        prediction = row["prediction"]
        if not prediction:
            continue
        try:
            value = float(prediction.get("predicted_income") or 0.0)
        except (TypeError, ValueError):
            continue
        highest = max(highest, value)
        chart_rows.append((str(row["worker"].get("name") or "Worker"), value, value < SURVIVAL_THRESHOLD_INR))

    chart_rows.sort(key=lambda item: item[1])
    if not chart_rows:
        ui.empty_state(
            "No predictions available yet.",
            "Predictions load from /api/predict/{worker_id}.",
        )
        return

    ceiling = highest * 1.12
    ui.render(ui.bar_chart(chart_rows, ceiling=ceiling, marker=SURVIVAL_THRESHOLD_INR))
    st.caption(
        f"Bars show each worker's predicted income for tomorrow from the backend model. "
        f"The vertical marker is the {inr(SURVIVAL_THRESHOLD_INR)} decision threshold used by "
        f"the payout and loan rules."
    )


def _coverage_section() -> None:
    map_col, list_col = st.columns([1, 1], gap="large")
    with map_col:
        coverage.render(st.session_state.workers, st.session_state.selected_worker_id)
    with list_col:
        workers = st.session_state.workers
        if not workers:
            ui.empty_state("No workers returned by the backend.")
            return
        for worker in workers[-5:]:
            worker_id = int(worker["worker_id"])
            prediction = state.prediction_for(worker_id)
            action = prediction.get("action") if prediction else None
            ui.render(
                '<div class="fs-kv" style="align-items:center">'
                f'<dt style="display:flex;gap:8px;align-items:center">'
                f'<span style="font-weight:600;color:#0C2430">{ui_badge_text(worker.get("name"))}</span>'
                f'{ui.badge(paid_label(worker.get("paid")), paid_tone(worker.get("paid")))}</dt>'
                f"<dd>{inr(prediction.get('predicted_income')) if prediction else '—'}</dd>"
                "</div>"
            )
        st.caption("Showing the five lowest-ID workers. Open Workers for the full board.")


def _hero() -> None:
    left, right = st.columns([1.15, 0.85], gap="large", vertical_alignment="center")
    with left:
        ui.render(
            '<div class="fs-hero-copy">'
            '<div class="fs-eyebrow">Weather-aware income protection</div>'
            '<h1 class="fs-hero-title">Predict, then protect.</h1>'
            '<p class="fs-hero-sub">When severe weather threatens a delivery worker’s earnings, '
            'FlowState helps identify who may need support and makes protection easier to reach.</p>'
            '<div class="fs-hero-trust"><span>Weather-aware</span><i></i><span>Income forecasts</span>'
            '<i></i><span>Automatic eligibility</span></div></div>'
        )
        cta1, cta2 = st.columns([1, 1], gap="small")
        with cta1:
            if st.button("Explore worker forecasts", type="primary", use_container_width=True,
                         key="hero_workers"):
                st.session_state.view = "workers"
                st.rerun()
        with cta2:
            if st.button("How protection works", use_container_width=True, key="hero_guide"):
                st.session_state.view = "guide"
                st.rerun()
    with right:
        weather = st.session_state.weather or {}
        health = st.session_state.health or {}
        rain = number(weather.get("rain_mm"))
        aqi = number(weather.get("aqi"))
        scenario = scenario_label(health.get("scenario"))
        rows = []
        for row in state.worker_rows():
            pred = row.get("prediction")
            if not pred:
                continue
            try:
                val = float(pred.get("predicted_income"))
            except (TypeError, ValueError):
                continue
            rows.append((str(row["worker"].get("name") or "Worker"), val,
                         val < SURVIVAL_THRESHOLD_INR))
        rows.sort(key=lambda item: item[1])
        ui.render(
            '<div class="fs-hero-card"><div class="fs-hero-card-top">'
            '<div><div class="fs-card-kicker">Local conditions</div>'
            f'<div class="fs-hero-card-title">{scenario}</div></div>'
            f'{ui.badge("Protection active", "ok")}</div>'
            '<div class="fs-hero-weather">'
            f'<div><span>Rainfall</span><strong>{rain} mm</strong></div>'
            f'<div><span>Air quality</span><strong>{aqi} AQI</strong></div>'
            '</div><div class="fs-hero-chart-label">Forecasted income · lowest 3</div>'
        )
        if rows:
            ui.render(ui.bar_chart(rows[:3], ceiling=max(max(x[1] for x in rows[:3]) * 1.15, 1),
                                   marker=SURVIVAL_THRESHOLD_INR))
        else:
            ui.empty_state("Forecasts are loading", "Worker predictions will appear here when available.")
        ui.render('</div>')


def _recent_activity() -> None:
    payouts = st.session_state.payouts or []
    ui.section("Recent protection activity", "Latest recorded payouts")
    if st.session_state.payouts_error:
        st.warning(st.session_state.payouts_error)
        return
    if not payouts:
        ui.empty_state("No payouts recorded yet", "When a payout is recorded, its details will appear here.")
        return
    for payout in payouts[:3]:
        label, tone = payout_mode(payout.get("mock"))
        ui.render(
            '<div class="fs-activity-row"><div><strong>'
            f'{ui_badge_text(payout.get("name") or "Worker")}</strong>'
            f'<span>Worker {ui_badge_text(payout.get("worker_id", "—"))} · '
            f'{ui_badge_text(short_hash(payout.get("tx_hash")))}</span></div>'
            f'<div class="fs-activity-right"><strong>{ui_badge_text(inr(payout.get("amount")))}</strong>'
            f'{ui.badge(label, tone)}</div></div>'
        )


def ui_badge_text(value: object) -> str:
    """Small escape helper for inline name text."""
    from html import escape

    return escape(str(value or "Worker"))


def render() -> None:
    health = st.session_state.health
    if health is None:
        st.error(st.session_state.health_error or "The backend health endpoint did not respond.")
        return

    for level, message in state.drain_flash():
        getattr(st, level)(message)

    _hero()
    ui.section("Your protection at a glance")
    _impact_tiles()

    ui.section("Risk snapshot", "Predicted income vs the decision threshold")
    _risk_snapshot()

    ui.section("Coverage", "Simulated Mumbai coordinates")
    _coverage_section()
    _recent_activity()
