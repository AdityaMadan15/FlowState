"""How it works: the pipeline, the decision rules, the demo script and honest limits."""

from __future__ import annotations

import streamlit as st

import components as ui


def _pipeline() -> None:
    ui.render(
        ui.flow_steps(
            [
                ("01", "Weather input", "Scenario values from the backend demo state"),
                ("02", "Trained model", "LightGBM forecasts tomorrow's earnings"),
                ("03", "Explanation", "SHAP ranks the factors behind the drop"),
                ("04", "Decision rules", "Payout, loan, or nothing"),
                ("05", "Settlement", "Solidity contract releases the payout"),
                ("06", "Ledger", "INR ledger and payout log updated"),
            ]
        )
    )


def _rules() -> None:
    ui.render(
        '<div class="fs-card" style="padding:0;overflow:hidden">'
        '<div style="display:grid;grid-template-columns:56px 1fr 150px 120px;gap:12px;'
        'padding:12px 18px;border-bottom:1px solid #E2E7E3;font-size:11px;font-weight:600;'
        'letter-spacing:.1em;text-transform:uppercase;color:#63798A">'
        "<div>Order</div><div>Condition</div><div>Action</div><div>Money</div></div>"
        '<div style="display:grid;grid-template-columns:56px 1fr 150px 120px;gap:12px;'
        'padding:14px 18px;border-bottom:1px solid #E2E7E3;font-size:13px;align-items:center">'
        '<div class="fs-mono" style="color:#0B6E66">01</div>'
        "<div>Rainfall above 50 mm <em>or</em> AQI above 400</div>"
        f'<div>{ui.badge("Instant payout", "ok")}</div><div>Free, from the pool</div></div>'
        '<div style="display:grid;grid-template-columns:56px 1fr 150px 120px;gap:12px;'
        'padding:14px 18px;border-bottom:1px solid #E2E7E3;font-size:13px;align-items:center">'
        '<div class="fs-mono" style="color:#0B6E66">02</div>'
        "<div>Predicted income below the survival threshold</div>"
        f'<div>{ui.badge("Loan offered", "warn")}</div><div>Repaid from earnings</div></div>'
        '<div style="display:grid;grid-template-columns:56px 1fr 150px 120px;gap:12px;'
        'padding:14px 18px;font-size:13px;align-items:center">'
        '<div class="fs-mono" style="color:#0B6E66">03</div>'
        "<div>Predicted income at or above the threshold</div>"
        f'<div>{ui.badge("No action", "idle")}</div><div>Nothing moves</div></div>'
        "</div>"
    )
    st.caption(
        "Rules are evaluated in this order by the backend decision engine. A payout is a fact — "
        "the weather crossed a line. A loan is a prediction — the model expects a shortfall."
    )


def _demo_script() -> None:
    steps = [
        ("Understand the forecast", "See how weather conditions can affect expected delivery earnings."),
        ("Review support options", "Workers can review forecasts and any support options available to them."),
        ("Automatic protection", "When weather rules qualify a worker, the system records the resulting payout."),
        ("Follow activity", "Review recorded payouts and their transaction status in the activity ledger."),
    ]
    rows = "".join(
        f'<div class="fs-kv"><dt><span class="fs-mono" style="color:#0B6E66">'
        f"{index:02d}</span> <strong style=\"color:#0C2430\">{title}</strong></dt>"
        f'<dd style="font-weight:400;color:#63798A;text-align:right;max-width:58%">{detail}</dd></div>'
        for index, (title, detail) in enumerate(steps, start=1)
    )
    ui.render(f'<div class="fs-card">{rows}</div>')


def render() -> None:
    ui.page_header(
        "How it works",
        "From rainfall to rupees.",
        "FlowState combines weather inputs, income forecasts and clear support rules to help "
        "delivery workers understand what protection may be available.",
    )

    ui.section("Pipeline")
    _pipeline()

    ui.section("Decision rules", "Evaluated in order, per worker")
    _rules()

    ui.section("How a worker uses FlowState")
    _demo_script()

    ui.section("What is real and what is simulated")
    real_col, sim_col = st.columns(2, gap="large")
    with real_col:
        ui.render(
            '<div class="fs-card">'
            '<div class="fs-card-title">Designed to support workers</div>'
            '<ul class="fs-list">'
            "<li>Weather-aware income forecasts</li>"
            "<li>Clear eligibility decisions for support</li>"
            "<li>Recorded payout activity and transaction status</li>"
            "<li>Worker-level forecast and ledger details</li>"
            "</ul></div>"
        )
    with sim_col:
        ui.render(
            '<div class="fs-card">'
            '<div class="fs-card-title">Prototype scope</div>'
            '<ul class="fs-list">'
            "<li>Worker earnings and weather inputs</li>"
            "<li>Weather and earnings inputs used in this demo</li>"
            "<li>Real bank or UPI transfers</li>"
            "<li>KYC, UPI and bank settlement</li>"
            "<li>Loan repayment</li>"
            "</ul></div>"
        )

